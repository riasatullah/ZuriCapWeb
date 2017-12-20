# By: Riasat Ullah

from ZuriCapWeb.backend.database import info_queries, inject_queries
from ZuriCapWeb.utils import calculator, handyman, times
from ZuriCapWeb.variables import params
import pandas


class Invoice(object):

    financing = None
    repayments = None
    rates = None
    buyer_rate_override = 0
    supplier_rate_override = 0
    buyer_fraction = 100
    supplier_fraction = 0

    def __init__(self, details, financing=None, repayments=None, rates=None,
                 buyer_rate_override=0, supplier_rate_override=0,
                 buyer_fraction=100, supplier_fraction=0):
        self.invoice_id = details[params.invoice_id]
        self.details = details
        if financing is not None:
            self.with_financing(financing)
        if repayments is not None:
            self.with_repayments(repayments)
        if rates is not None:
            self.with_rates(rates)

        self.buyer_rate_override = buyer_rate_override
        self.supplier_rate_override = supplier_rate_override
        self.buyer_fraction = buyer_fraction
        self.supplier_fraction = supplier_fraction

    @staticmethod
    def from_invoice_id(invoice_id):
        '''
        Allows you to create an invoice object with its invoice id.
        There is no need to provide any other information. It will
        automatically try to retrieve information from the database.
        This should only be used if an invoice already exists.
        :param invoice_id: the invoice id
        :return: an invoice object
        '''
        details = info_queries.get_invoice(invoice_id)
        if len(details) > 0:
            details = details[invoice_id]
            invoice = Invoice(details)
            invoice.with_financing()
            invoice.with_repayments()
            invoice.with_rates()
            invoice.with_overridden_rates()
            invoice.with_fee_split()
            invoice.add_dues(times.current_date())
            return invoice
        else:
            raise KeyError('Invalid invoice id')

    def with_financing(self, info=None):
        '''
        Incorporates all financing details of the invoice. It can process
        financing information provided to it. If no such information is
        provided, it will retrieve the information from the database.
        :param info: financing details; default None
        '''
        if info is None:
            info = info_queries.get_forwarded_payments(self.invoice_id)[self.invoice_id]
        if len(info) > 0:
            self.financing = info
            self.details[params.financing_details] = self.financing
            self.details[params.total_financed] = self.total_financed()
            self.details[params.total_transaction_cost] = self.total_transaction_cost()

    def with_repayments(self, info=None):
        '''
        Incorporates all repayment details of the invoice. It can process
        repayment information provided to it. If no such information is
        provided, it will retrieve the information from the database.
        :param info: repayment details; default None
        '''
        if info is None:
            info = info_queries.get_received_payments(self.invoice_id)[self.invoice_id]
        if len(info) > 0:
            self.repayments = info
            self.details[params.repayment_details] = self.repayments
            self.details[params.total_repayments] = self.total_repayments()
            self.details[params.total_discount_fees] = self.total_discount_fees()

    def with_rates(self, info=None):
        '''
        Incorporates all product rates. It can process rate information
        provided to it. If no such information is provided, it will
        retrieve the information from the database.
        :param info: product rates; default None
        '''
        if info is None:
            info = info_queries.get_rates(times.current_date())
        if len(info) > 0:
            self.rates = info

    def with_overridden_rates(self, info=None):
        '''
        Incorporates overridden rates that may apply to the
        buyer and/or the supplier
        :param info: overridden rates details; default None
        '''
        if info is None:
            client_ids = handyman.combine_items([self.buyer_id(), self.supplier_id()])
            info = info_queries.get_overridden_rates(client_ids, self.submitted_on())
        if len(info) > 0:
            if self.buyer_id() in info.keys():
                overrides = info[self.buyer_id()]
                for item in overrides:
                    if item[params.financing_product_id] == self.financing_product_id():
                        if item[params.buyer_rate] != 0:
                            self.buyer_fraction = item[params.buyer_rate]
            if self.supplier_id() in info.keys():
                overrides = info[self.buyer_id()]
                for item in overrides:
                    if item[params.financing_product_id] == self.financing_product_id():
                        if item[params.supplier_rate] != 0:
                            self.supplier_fraction = item[params.supplier_rate]

    def with_fee_split(self, info=None):
        '''
        Sets the share of the fee borne by the buyer and the supplier
        :param info: fee split details; default None
        '''
        if info is None:
            info = info_queries.get_relations(buyer_id=self.buyer_id(),
                                              supplier_id=self.supplier_id(),
                                              on_date=self.submitted_on())
        found = False
        if len(info) > 0:
            for relation in info:
                if relation[params.buyer_id] == self.buyer_id():
                    if relation[params.supplier_id] == self.supplier_id():
                        self.buyer_fraction = relation[params.buyer_fraction]
                        self.supplier_fraction = relation[params.supplier_fraction]
                        found = True
        if not found:
            err = 'No relation found on {0} between buyer (id: {1}) and supplier (id: {2})'\
                .format(str(self.submitted_on()),
                        str(self.buyer_id()),
                        str(self.supplier_id()))
            raise LookupError(err)

    def add_dues(self, date):
        '''
        Calculates and incorporates details of the total repayable
        along with details about accrual period, average applied rate,
        total discount fees and total financing remaining
        :param date: date to check dues on
        '''
        if self.details[params.invoice_status] != params.closed_status:
            principal_repaid = self.total_principal_repaid()
            principal_dues = self.get_principal_dues(principal_repaid)

            total_due = self.calc_total_dues(date, principal_dues)
            self.details[params.principal_due] = total_due[0]
            self.details[params.accrual_period] = total_due[1]
            self.details[params.applied_rate] = total_due[2] * 100
            self.details[params.discount_fees] = total_due[3]
            self.details[params.repayment_due] = total_due[4]
            self.details[params.remaining_financing] = total_due[5]

    def get_principal_dues(self, principal_repaid):
        '''
        Gets the breakdown of due payments with respect
        to the list of financed amounts
        :param principal_repaid: the principal value of
                                financing that was repaid
        :return: list --> tuples (financing_date, due)
        '''
        dues = []
        principal_due = self.total_financed()
        transaction_cost_due = self.total_transaction_cost()
        principal_due += transaction_cost_due
        repayment_on_hand = principal_repaid
        if principal_due > 0:
            for payment in self.financing:
                financed = float(payment[params.financed_amount])
                if repayment_on_hand <= financed:
                    principal_due -= repayment_on_hand
                    dues.append((payment[params.financing_date],
                                 financed - repayment_on_hand))
                    repayment_on_hand -= repayment_on_hand
                else:
                    repayment_on_hand -= financed
                    principal_due -= financed
                    dues.append((payment[params.financing_date], 0))
        return dues

    def calc_total_dues(self, date, dues):
        '''
        Calculates the total dues along with the accrual period,
        average applied rate, total discount fees and remaining financing
        :param date: date to check dues on
        :param dues: breakdown of dues
        :return: tuple --> (average accrual, average applied rate,
                            total discount fees, total repayable,
                            total financing remaining)
        '''
        dues = pandas.DataFrame(dues, columns=[params.payment_date, params.amount])
        dues[params.amount] = dues[params.amount].astype(float)
        principal_due = dues[params.amount].sum()
        dues[params.accrual_period] = dues[params.payment_date].map(lambda x: times.accrual_period(str(x), date))
        dues[params.applied_rate] = dues[params.accrual_period].map(lambda x: self.get_rate(x))
        dues[params.discount_fees] = dues[params.amount] * dues[params.applied_rate]
        discount_fees = round(dues[params.discount_fees].sum(), 0)
        repayment_due = self.repayable(principal_due, discount_fees)
        remaining_financing = self.remaining_financing(discount_fees)

        weight = 'weight'
        weighted_accrual = 'weighted_accrual'
        weighted_rate = 'weighted_rate'
        dues[weight] = dues[params.amount]/principal_due
        dues[weighted_accrual] = dues[params.accrual_period] * dues[weight]
        avg_accrual = round(dues[weighted_accrual].sum(), 2)
        dues[weighted_rate] = dues[params.applied_rate] * dues[weight]
        avg_rate = round(dues[weighted_rate].sum(), 4)
        return (principal_due, avg_accrual, avg_rate, discount_fees, repayment_due, remaining_financing)

    def repayable(self, principal_due, discount_fees):
        '''
        Calculates the repayable for an invoice taking into account how
        the cost of the discount fee shall be borne by the buyer and the supplier
        :param discount_fees: discount fees
        :return: total amount that should be repaid by the buyer
        '''
        bf = self.buyer_fraction/100
        fees_due = self.transaction_cost_due()
        if principal_due == 0:
            return 0
        if bf == 1:
            return principal_due + discount_fees + fees_due
        else:
            return (bf * discount_fees) + principal_due + fees_due

    def remaining_financing(self, discount_fees):
        '''
        Calculates the amount that still needs to paid to the supplier.
        This is important in cases where a supplied led program is run
        because in a supplier led program only a partial amount of the
        invoice is financed initially and the remaining is paid to the
        supplier after the buyer pays the full amount.
        :param discount_fees: discount fees
        :return: total remaining to be paid to the supplier
        '''
        discount_fees = float(discount_fees)
        bf = self.buyer_fraction/100
        sf = self.supplier_fraction/100
        if bf == 1:
            return 0
        else:
            return self.invoice_total() - self.total_financed() - (sf * discount_fees)

    def get_rate(self, day):
        '''
        Gets the rate, adjusted for overridden rates,
        for the financing product for this invoice for a particular day
        :param day: the day to get the rate for
        :return: rate
        '''
        rate_chart = pandas.DataFrame(
            self.rates[self.details[params.financing_product_id]])
        max_day = rate_chart[0].max()
        if 0 <= day <= max_day:
            rate = rate_chart[(rate_chart[0] <= day) & (rate_chart[1] > day)][2]
        else:
            rate = rate_chart[rate_chart[0] == max_day][2]
        try:
            rate = round((float(rate)/100), 4)
            rate += self.buyer_rate_override + self.supplier_rate_override
            return rate
        except ValueError as e:
            raise ValueError('Rate is not valid - ' + str(day)) from e

    def get_details(self):
        return self.details

    def get_financing(self):
        return self.financing

    def get_repayments(self):
        return self.repayments

    def validate(self):
        pass

    def invoice_total(self):
        return float(self.details[params.invoice_total])

    def buyer_id(self):
        return self.details[params.buyer_id]

    def buyer_name(self):
        return self.details[params.buyer_name]

    def supplier_id(self):
        return self.details[params.supplier_id]

    def supplier_name(self):
        return self.details[params.supplier_name]

    def financing_product_id(self):
        return self.details[params.financing_product_id]

    def accrual_period(self):
        return self.details[params.accrual_period]

    def applied_rate(self):
        return self.details[params.applied_rate]

    def submitted_on(self):
        return self.details[params.submitted_on]

    def total_principal_repaid(self):
        if self.repayments is None or len(self.repayments) == 0:
            return 0
        else:
            return calculator.total_from_dict(self.repayments,
                                              params.principal_repaid)

    def total_financed(self):
        if self.financing is None or len(self.financing) == 0:
            return 0
        else:
            return calculator.total_from_dict(self.financing, params.financed_amount)

    def total_transaction_cost(self):
        if self.financing is None or len(self.financing) == 0:
            return 0
        else:
            return calculator.total_from_dict(self.financing, params.transaction_cost)

    def transaction_cost_due(self):
        cost = self.total_transaction_cost()
        repaid = self.total_repayments()
        if repaid < cost:
            return cost - repaid
        else:
            return 0

    def total_discount_fees(self):
        if self.repayments is None or len(self.repayments) == 0:
            return 0
        else:
            return calculator.total_from_dict(self.repayments, params.discount_fees)

    def total_repayments(self):
        if self.repayments is None or len(self.repayments) == 0:
            return 0
        else:
            return calculator.total_from_dict(self.repayments, params.repaid_amount)

    def principal_due(self):
        return float(self.details[params.principal_due])

    def repayment_due(self):
        return self.details[params.repayment_due]

    def financing_due(self):
        return self.details[params.remaining_financing]

    def invoice_date(self):
        return self.details[params.invoice_date]

    def last_repayment_date(self):
        if self.repayments is None or len(self.repayments) == 0:
            return None
        else:
            return calculator.min_from_dict(self.repayments, params.repayment_date)

    def currency(self):
        return self.details[params.currency]

    def log_financing(self, username, payment_date, amount, fees, payment_method, notes, currency='KES'):
        pass

    def log_repayment(self, username, payment_date, amount, payment_method, notes, currency='KES'):
        pass

    def close_invoice(self, username, notes='', completion_date=None, cancelled=False):
        try:
            if completion_date is None:
                completion_date = times.current_date()
            data = dict()
            data[params.invoice_id] = self.invoice_id
            data[params.completion_date] = completion_date
            data[params.invoice_status] = params.closed_status if not cancelled else params.cancelled_status
            data[params.currency] = self.currency()
            data[params.total_financed] = self.total_financed()
            data[params.transaction_cost] = self.total_transaction_cost()
            data[params.principal_repaid] = self.total_principal_repaid()
            data[params.total_repayments] = self.total_repayments()
            data[params.discount_fees] = self.total_discount_fees()
            data[params.unrealized_pnl] = self.pnl()
            data[params.updated_by] = username
            data[params.updated_timestamp] = times.current_timestamp()
            data[params.notes] = notes
            inject_queries.close_invoice(data, cancelled)
        except Exception as e:
            raise Exception(e)
