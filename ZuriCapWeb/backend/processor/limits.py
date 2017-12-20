# By: Riasat Ullah

from ZuriCapWeb.backend.database import info_queries
from ZuriCapWeb.variables import params

missing_code = -1
within_code = 0
over_code = 1


class ClientLimits(object):

    def __init__(self, clientid, date):
        self.limits = Limits(self.add_limits(clientid, date))

    def add_limits(self, clientid, date):
        data = info_queries.get_client_limits(clientid, date)
        limits = dict()
        if len(data) > 0:
            for limit_type, currency, amount in data:
                limits[(limit_type, currency)] = amount
        return limits

    def missing_types(self):
        expecting = [params.discounting_max_giv,
                     params.discounting_max_single_iv,
                     params.discounting_max_invoice_count,
                     params.invoicing_max_giv,
                     params.invoicing_max_single_iv,
                     params.invoicing_max_invoice_count]
        limit_types = list(self.limits.keys())
        missing = set(expecting).difference(set(limit_types))
        return missing

    def get_discounting_giv(self, currency):
        return self.limits.get(params.discounting_max_giv, currency)

    def get_discounting_single_iv(self, currency):
        return self.limits.get(params.discounting_max_single_iv, currency)

    def get_discounting_invoice_count(self, currency):
        return self.limits.get(params.discounting_max_invoice_count, currency)

    def get_invoicing_giv(self, currnecy):
        return self.limits.get(params.invoicing_max_giv, currnecy)

    def get_invoicing_single_iv(self, currency):
        return self.limits.get(params.invoicing_max_single_iv, currency)

    def get_invoicing_invoice_count(self, currency):
        return self.limits.get(params.invoicing_max_invoice_count, currency)

    def within_discounting_giv(self, currency, value):
        return self.limits.within_limit(params.discounting_max_giv, currency, value)

    def within_discounting_single_iv(self, currency, value):
        return self.limits.within_limit(params.discounting_max_single_iv, currency, value)

    def within_discounting_invoice_count(self, currency, value):
        return self.limits.within_limit(params.discounting_max_invoice_count, currency, value)

    def within_invoicing_giv(self, currency, value):
        return self.limits.within_limit(params.invoicing_max_giv, currency, value)

    def within_invoicing_single_iv(self, currency, value):
        return self.limits.within_limit(params.invoicing_max_single_iv, currency, value)

    def within_invoicing_invoice_count(self, currency, value):
        return self.limits.within_limit(params.invoicing_max_invoice_count, currency, value)


class RelationLimits(object):

    def __init__(self, buyerid, supplierid, date):
        self.limits = Limits(self.add_limits(buyerid, supplierid, date))

    def add_limits(self, buyerid, supplierid, date):
        data = info_queries.get_relation_limits(buyerid, supplierid, date)
        limits = dict()
        if len(data) > 0:
            for limit_type, currency, amount in data:
                limits[(limit_type, currency)] = amount
        return limits

    def missing_types(self):
        expecting = [params.relation_max_giv,
                     params.relation_max_single_iv,
                     params.relation_max_invoice_count]
        limit_types = list(self.limits.keys())
        missing = set(expecting).difference(set(limit_types))
        return missing

    def get_relation_giv(self, currency):
        return self.limits.get(params.relation_max_giv, currency)

    def get_relation_single_iv(self, currency):
        return self.limits.get(params.relation_max_single_iv, currency)

    def get_relation_invoice_count(self, currency):
        return self.limits.get(params.relation_max_invoice_count, currency)

    def within_relation_giv(self, currency, value):
        return self.limits.within_limit(params.relation_max_giv, currency, value)

    def within_relation_single_iv(self, currency, value):
        return self.limits.within_limit(params.relation_max_single_iv, currency, value)

    def within_relation_invoice_count(self, currency, value):
        return self.limits.within_limit(params.relation_max_invoice_count, currency, value)

class Limits(object):

    def __init__(self, limits):
        self.limits = limits

    def get(self, limit_type, currency):
        if self.has_limits(limit_type, currency):
            return self.limits[(limit_type, currency)]
        else:
            return missing_code

    def has_limits(self, limit_type, currency):
        if (limit_type, currency) in self.limits:
            return True
        else:
            return False

    def within_limit(self, limit_type, currency, value):
        if not self.has_limits(limit_type, currency):
            return missing_code
        else:
            limit_value = self.limits[(limit_type, currency)]
            if value <= limit_value:
                return True
            else:
                return False
