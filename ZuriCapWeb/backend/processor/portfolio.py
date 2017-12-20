# By: Riasat Ullah

from ZuriCapWeb.backend.processor.invoice import Invoice
from ZuriCapWeb.variables import params
import pandas


class Portfolio(object):

    def __init__(self, portfolio_of_invoices: list):
        self.portfolio = portfolio_of_invoices
        self.assert_portfolio_of_invoices()

    def assert_portfolio_of_invoices(self):
        assertion = True
        if len(self.portfolio) > 0:
            i = 0
            while i < len(self.portfolio) and assertion is not False:
                item = self.portfolio[i]
                if not isinstance(item, Invoice):
                    err = 'Expected a portfolio of invoices. ' +\
                          'Found ' + str(type(item))
                    raise TypeError(err)
                i += 1

    def add_invoice(self, invoice: Invoice):
        self.portfolio.append(invoice)

    def total_financed(self):
        total = 0
        if len(self.portfolio) > 0:
            for invoice in self.portfolio:
                total += invoice.total_financed()
        return float(total)

    def total_repaid(self):
        total = 0
        if len(self.portfolio) > 0:
            for invoice in self.portfolio:
                total += invoice.total_principal_repaid()
        return float(total)

    def total_repayment_due(self):
        total = 0
        if len(self.portfolio) > 0:
            for invoice in self.portfolio:
                assert isinstance(invoice, Invoice)
                total += invoice.repayment_due()
        return float(total)

    def current_giv(self):
        return float(self.total_financed() - self.total_repaid())

    def invoice_count(self):
        return len(self.portfolio)

    def get_invoices(self):
        return self.portfolio

    def sort(self, attribute):
        '''
        Sorts the portfolio by a given attribute
        :param attribute: the attribute to sort by
        '''
        self.portfolio = sorted(self.portfolio, key=lambda k: k.get_details()[attribute])
