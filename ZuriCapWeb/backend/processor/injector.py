# By: Riasat Ullah

from ZuriCapWeb.backend.database import info_queries, inject_queries
from ZuriCapWeb.backend.processor import grabber
from ZuriCapWeb.backend.processor.limits import ClientLimits, RelationLimits
from ZuriCapWeb.backend.processor.logger import Logger
from ZuriCapWeb.backend.processor.invoice import Invoice
from ZuriCapWeb.backend.processor.portfolio import Portfolio
from ZuriCapWeb.utils import handyman, times
from ZuriCapWeb.variables import params, messages


def upload_invoice(date, username, buyer_id, supplier_id,
                   invoice_date, financing_product_id,
                   description, invoice_value,
                   currency='KES', timestamp=None):
    new_invoice_value = float(invoice_value)
    buyer_id = int(buyer_id)
    supplier_id = int(supplier_id)
    errors = []

    # check buyer limits first
    buyer_open_invoices = grabber.retrieve_invoices(buyer_id=buyer_id, status=params.open_status)
    buyer_portfolio = Portfolio(buyer_open_invoices)
    buyer_limits = ClientLimits(buyer_id, date)
    if not buyer_limits.within_discounting_giv(currency, buyer_portfolio.current_giv() + new_invoice_value):
        errors.append(messages.limit_breach(params.discounting_max_giv,
                                            buyer_limits.get_discounting_giv(currency),
                                            buyer_portfolio.current_giv() + new_invoice_value))
        return errors

    if not buyer_limits.within_discounting_single_iv(currency, new_invoice_value):
        errors.append(messages.limit_breach(params.discounting_max_single_iv,
                                            buyer_limits.get_discounting_single_iv(currency),
                                            new_invoice_value))
        return errors

    if not buyer_limits.within_discounting_invoice_count(currency, buyer_portfolio.invoice_count() + 1):
        errors.append(messages.limit_breach(params.discounting_max_invoice_count,
                                            buyer_limits.get_discounting_invoice_count(currency),
                                            buyer_limits.get_discounting_invoice_count(currency) + 1))
        return errors

    # check supplier limits second
    supplier_open_invoices = grabber.retrieve_invoices(supplier_id=supplier_id, status=params.open_status)
    supplier_portfolio = Portfolio(supplier_open_invoices)
    supplier_limits = ClientLimits(supplier_id, date)
    if not supplier_limits.within_invoicing_giv(currency, supplier_portfolio.current_giv() + new_invoice_value):
        errors.append(messages.limit_breach(params.invoicing_max_giv,
                                            supplier_limits.get_invoicing_giv(currency),
                                            supplier_portfolio.current_giv() + new_invoice_value))
        return errors

    if not supplier_limits.within_invoicing_single_iv(currency, new_invoice_value):
        errors.append(messages.limit_breach(params.invoicing_max_giv,
                                            supplier_limits.get_invoicing_single_iv(currency),
                                            new_invoice_value))
        return errors

    if not supplier_limits.within_invoicing_invoice_count(currency, supplier_portfolio.invoice_count() + 1):
        errors.append(messages.limit_breach(params.invoicing_max_invoice_count,
                                            supplier_limits.get_invoicing_invoice_count(currency),
                                            supplier_limits.get_invoicing_invoice_count(currency) + 1))
        return errors

    # check relation limits last
    relation_open_invoices = grabber.retrieve_invoices(buyer_id=buyer_id,
                                                       supplier_id=supplier_id,
                                                       status=params.open_status)
    relation_portfolio = Portfolio(relation_open_invoices)
    relation_limits = RelationLimits(buyer_id, supplier_id, date)
    if not relation_limits.within_relation_giv(currency, relation_portfolio.current_giv() + new_invoice_value):
        errors.append(messages.limit_breach(params.relation_max_giv,
                                            relation_limits.get_relation_giv(currency),
                                            relation_portfolio.current_giv() + new_invoice_value))
        return errors

    if not relation_limits.within_relation_single_iv(currency, new_invoice_value):
        errors.append(messages.limit_breach(params.relation_max_single_iv,
                                            relation_limits.get_relation_single_iv(currency),
                                            new_invoice_value))
        return errors

    if not relation_limits.within_relation_invoice_count(currency, relation_portfolio.invoice_count() + 1):
        errors.append(messages.limit_breach(params.relation_max_invoice_count,
                                            relation_limits.get_relation_invoice_count(currency),
                                            relation_limits.get_relation_invoice_count(currency) + 1))
        return errors

    client_names = info_queries.name_from_clientid([buyer_id, supplier_id])
    financing_products = info_queries.financing_product_from_id(financing_product_id)
    data = dict()
    data[params.invoice_ref_id] = handyman.mint_reference_id(date, 1, buyer_id, supplier_id)
    data[params.buyer_id] = buyer_id
    data[params.buyer_name] = client_names[buyer_id]
    data[params.supplier_id] = supplier_id
    data[params.supplier_name] = client_names[supplier_id]
    data[params.financing_product_id] = financing_product_id
    data[params.financing_product] = financing_products[financing_product_id]
    data[params.submission_timestamp] = times.current_timestamp() if timestamp is None else timestamp
    data[params.submitted_on] = date
    data[params.invoice_date] = invoice_date
    data[params.description] = description
    data[params.currency] = currency
    data[params.invoice_total] = new_invoice_value
    data[params.submitted_by] = username
    data[params.submission_overridden] = 'f'
    data[params.approved_on] = date
    data[params.approved_by] = username
    data[params.invoice_status] = params.open_status

    output = inject_queries.add_new_invoice(data)
    return output


def add_user(client_id, first_name, last_name, birth_date,
             id_type, id_no, title, email, office_phone,
             cell_phone=None, question_1=None, answer_1=None,
             question_2=None, answer_2=None, notes=''):
    try:
        data = dict()
        data[params.username] = handyman.mint_username(first_name, last_name)
        pwd = Logger.generate_password()
        pwd_hash = Logger.get_hash(pwd)
        data[params.salt] = pwd_hash[0]
        data[params.hash_password] = pwd_hash[1]
        data[params.id_type] = id_type
        data[params.id] = id_no
        data[params.start_date] = times.current_date()
        data[params.end_date] = '99990101'
        data[params.client_id] = client_id
        data[params.first_name] = first_name
        data[params.last_name] = last_name
        data[params.birth_date] = birth_date
        data[params.title] = title
        data[params.email] = email
        data[params.office_phone] = office_phone
        data[params.cell_phone] = 'null' if cell_phone is None else cell_phone
        data[params.question_1] = 'null' if question_1 is None else question_1
        data[params.answer_1] = 'null' if question_1 is None else answer_1
        data[params.question_2] = 'null' if question_2 is None else question_2
        data[params.answer_2] = 'null' if question_2 is None else answer_2
        data[params.notes] = notes
        inject_queries.add_user(data)
    except Exception as e:
        raise Exception(e)


def update_password(username, new_password):
    try:
        hash_pwd = Logger.get_hash(new_password)
        inject_queries.update_password(username, hash_pwd[0], hash_pwd[1])
    except Exception as e:
        raise Exception(e)
