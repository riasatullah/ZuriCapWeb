# By: Riasat Ullah

from ZuriCapWeb.backend.processor.invoice import Invoice
from ZuriCapWeb.backend.database import info_queries, inject_queries
from ZuriCapWeb.backend.processor.portfolio import Portfolio
from ZuriCapWeb.variables import messages, params
import psycopg2


class InvoicePayment(object):

    def __init__(self, portfolio: Portfolio, amount, fees, payment_date,
                 payment_method, updated_by, paid_by=None, paid_to=None,
                 currency='KES', notes=''):
        self.portfolio = portfolio
        try:
            self.portfolio.assert_portfolio_of_invoices()
        except TypeError as e:
            raise TypeError('Portfolio assertion failed') from e
        self.amount = amount
        self.fees = fees
        self.payment_date = payment_date
        self.payment_method = payment_method
        self.updated_by = updated_by
        self.paid_by = paid_by
        self.paid_to = paid_to
        self.currency = currency
        self.notes = notes

    def make(self):
        '''
        Log a financing payment in the database.
        Financed amounts are booked as a -ve number.
        '''
        if self.portfolio.invoice_count() != 1:
            err = 'Financing payments can only be made per invoice. ' +\
                  'Expected 1 invoice; received ' + str(self.portfolio.invoice_count())
            raise TypeError(err)
        else:
            invoice = self.portfolio.get_invoices()[0]
            assert isinstance(invoice, Invoice)
            payment_to = self.paid_to
            if payment_to is None:
                payment_to = invoice.supplier_id()
            invoice_percentage = round(self.amount/invoice.invoice_total()*100, 2)
            if 0 < self.amount <= invoice.financing_due():
                try:
                    inject_queries.add_forwarded_payment(self.payment_date, self.currency,
                                                         -self.amount, self.fees, self.payment_method,
                                                         payment_to, self.updated_by, self.notes,
                                                         invoice.invoice_id(), invoice_percentage)
                except psycopg2.DatabaseError as e:
                    raise psycopg2.DatabaseError(messages.error_db_query) from e
            elif self.amount == 0:
                raise ValueError(messages.error_financing_zero)
            else:
                raise ValueError(messages.error_financing_amount)

    def receive(self):
        '''
        Log a repayment of an invoice in the database.
        '''
        self.portfolio.sort(params.submitted_on)
        if self.paid_by is None or type(self.paid_by) is not int:
            raise TypeError(messages.error_invalid_payee)
        if self.amount == 0:
            raise ValueError(messages.error_repayment_zero)
        elif self.amount > self.portfolio.total_repayment_due():
            raise ValueError(messages.error_repayment_amount)
        else:
            allocations = []
            closures = []
            remaining = self.amount
            performance_fee = info_queries.get_performance_fee()/100
            invoice_list = self.portfolio.get_invoices()
            i = 0
            while i < len(invoice_list) and remaining > 0:
                invoice = invoice_list[i]
                assert isinstance(invoice, Invoice)
                if self.amount < invoice.repayment_due():
                    remaining = 0
                    principal_to_pay = (self.amount - invoice.transaction_cost_due())/(1 + (invoice.applied_rate()/100))
                    discount_fees = round(self.amount - principal_to_pay, 2)
                    numbers = [invoice.invoice_id,
                               self.amount,
                               round(principal_to_pay/invoice.total_financed() * 100, 2),
                               invoice.accrual_period(),
                               invoice.applied_rate(),
                               discount_fees,
                               discount_fees * performance_fee,
                               principal_to_pay]
                else:
                    remaining -= invoice.repayment_due()
                    numbers = [invoice.invoice_id,
                               invoice.principal_due(),
                               round(invoice.principal_due() / invoice.total_financed() * 100, 2),
                               invoice.accrual_period(),
                               invoice.applied_rate(),
                               invoice.total_discount_fees(),
                               invoice.total_discount_fees() * performance_fee,
                               invoice.principal_due()]
                    closures.append(invoice.invoice_id)
                i += 1
                allocations.append(numbers)
            try:
                inject_queries.add_received_payment(self.payment_date,
                                                    self.currency,
                                                    self.amount,
                                                    self.fees,
                                                    self.payment_method,
                                                    self.paid_by,
                                                    self.updated_by,
                                                    self.notes,
                                                    allocations,
                                                    closures)
            except psycopg2.DatabaseError as e:
                raise psycopg2.DatabaseError(e)
