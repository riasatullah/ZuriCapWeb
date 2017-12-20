# By: Riasat Ullah

from ZuriCapWeb.backend.database import info_queries
from ZuriCapWeb.backend.processor.invoice import Invoice
from ZuriCapWeb.utils import handyman, times
from ZuriCapWeb.variables import messages, params
import datetime
import psycopg2
import traceback

def clientid_from_username(username):
    return info_queries.clientid_from_username(username)


def client_relations(username, client_type, date=None):
    '''
    Gets the relations that a client has with counterparts
    :param username: username of the user
    :param client_type: the type of the client (buyer or supplier)
    :param date: date to check for
    :return: list --> list[id, client_name]
    '''
    if date is None:
        date = datetime.datetime.now().date()
        date = date.strftime('%Y%m%d')
    try:
        if client_type == params.buyer:
            attributes = [params.supplier_id, params.supplier_name]
            results = info_queries.get_relations(buyer_user=username, on_date=date)
        else:
            attributes = [params.buyer_id, params.buyer_name]
            results = info_queries.get_relations(supplier_user=username, on_date=date)
        relations = []
        for item in results:
            relations.append([item[attributes[0]], item[attributes[1]]])
        return relations
    except psycopg2.DatabaseError as e:
        err = 'Could not retrieve relations from database'
        raise psycopg2.DatabaseError(err)


def get_client_type(clientid=None, username=None):
    '''
    Gets the type of client given a clientid or username
    :param clientid: client's id
    :param username: username of the user
    :return: list --> buyer and/or supplier
    '''
    try:
        details = info_queries.get_client_type(clientid=clientid, username=username)
        if len(details) > 0:
            client_type = details[0]
            if client_type[params.buyer] and not client_type[params.supplier]:
                return [params.buyer]
            elif not client_type[params.buyer] and client_type[params.supplier]:
                return [params.supplier]
            elif client_type[params.buyer] and client_type[params.supplier]:
                return [params.buyer, params.supplier]
            else:
                raise LookupError(messages.error_client_type_invalid)
        else:
            raise LookupError(messages.error_client_type_invalid)
    except psycopg2.DatabaseError as e:
        err = 'Failed to query client type from database'
        raise psycopg2.DatabaseError(err) from e
    except Exception as e:
        raise Exception(e)


def payments(username, client_type, offset=0):
    transactions = info_queries.get_payments(username, client_type, offset)
    if len(transactions) == 0:
        return []
    else:
        holder = []
        for invoice_id, payment_date, description, currency, amount in transactions:
            holder.append({params.invoice_id: invoice_id,
                           params.payment_date: payment_date,
                           params.description: description,
                           params.currency: currency,
                           params.debit: 0 if int(amount) < 0 else amount,
                           params.credit: 0 if int(amount) > 0 else abs(amount)
                           })
        return holder


def present_payments(invoice_id=None, buyer_id=None, supplier_id=None,
                     limit=None, offset=None):
    '''
    Gets payment details with descriptions of each payment
    :param invoice_id: invoice id(s) to filter by
    :param buyer_id: buyer id(s) to filter by
    :param supplier_id: supplier id(s) to filter by
    :param limit: number of rows to limit by
    :param offset: number of rows to skip in query output
    :return: list of dictionaries with payment details
    '''
    details = info_queries.fetch_payments(invoice_id=invoice_id,
                                          buyer_id=buyer_id,
                                          supplier_id=supplier_id,
                                          limit=limit,
                                          offset=offset)
    for item in details:
        if item[params.side] == 1:
            item[params.description] = 'Repayment by ' + item[params.buyer_name]
            item[params.debit] = abs(item[params.amount])
        elif item[params.side] == 2:
            item[params.description] = 'Financed - ' + item[params.supplier_name]
            item[params.credit] = abs(item[params.amount])

        if item[params.cancelled_status]:
            desc = item[params.description]
            item[params.description] = 'CANCELLED - ' + desc
    return details


def retrieve_invoices(buyer_id=None, supplier_id=None, status=None,
                      limit_rows=0, offset=0, as_dict=False):
    '''
    Gets details of invoices from the database
    :param buyer_id: buyer's client id
    :param supplier_id: supplier's client id
    :param status: status of the invoices
    :param limit_rows: the number of invoices that should be retrieved
    :param offset: the number of invoices that should be skipped
    :param as_dict: specifies if invoice details are wanted in dictionary format
    :return: list of Invoice objects if as_dict=False;
            else list of dictionaries with details of each invoice
    '''
    invoices = info_queries.get_invoice(buyer_id=buyer_id, supplier_id=supplier_id,
                                        status=status, limit_rows=limit_rows, offset=offset)
    if len(list(invoices.keys())) > 0:
        financing = info_queries.get_forwarded_payments(list(invoices.keys()))
        repayments = info_queries.get_received_payments(list(invoices.keys()))
    else:
        financing = []
        repayments = []
    current_date = times.current_date()
    rates = info_queries.get_rates(current_date)
    client_ids = handyman.combine_items([buyer_id, supplier_id])
    overrides = info_queries.get_overridden_rates(None if len(client_ids) == 0 else client_ids)
    fee_fractions = info_queries.get_relations(buyer_id=buyer_id, supplier_id=supplier_id)

    holder = []
    for id_ in invoices:
        fin_info = None
        rep_info = None
        if id_ in financing.keys():
            fin_info = financing[id_]
        if id_ in repayments.keys():
            rep_info = repayments[id_]
        invoice = Invoice(invoices[id_], fin_info, rep_info, rates)
        invoice.with_overridden_rates(overrides)
        invoice.with_fee_split(fee_fractions)
        invoice.add_dues(current_date)
        holder.append(invoice)
    if as_dict:
        store = []
        for invoice in holder:
            store.append(invoice.get_details())
        return store
    return holder


def present_client_profile(clientid, date):
    '''
    Gets the client details and processes them to make them more displayable
    :param clientid: client's id
    :param date: date to look for
    :return: dictionary with client details
    '''
    try:
        details = info_queries.client_details(clientid=clientid, date=date)
        for item in details.keys():
            val = details[item]
            if val is None:
                details[item] = ''
        return details
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError('Could not get client details') from e


def present_client_limits(clientid=None, date=None):
    '''
    Gets client limits and arranges them in a displayable manner.
    :param clientid: client id(s) to look for
    :param date: date to check against
    :return: dictionary of limits
    '''
    limits = info_queries.get_client_limits(clientid=clientid, date=date)
    bucket = dict()
    for item in limits:
        bucket[item[params.limit_type]] = item[params.amount]
    return bucket


def present_relation_limits(buyer_id=None, supplier_id=None, date=None):
    '''
    Gets relation limits and arranges them in a displayable manner
    :param buyer_id: buyer id(s) to look for
    :param supplier_id: supplier id(s) to look for
    :param date: date to check against
    :return: list of dictionaries
    '''
    limits = info_queries.get_relation_limits(buyer_id=buyer_id, supplier_id=supplier_id, date=date)
    bucket = dict()
    for item in limits:
        buyer_id = item[params.buyer_id]
        buyer_name = item[params.buyer_name]
        supplier_id = item[params.supplier_id]
        supplier_name = item[params.supplier_name]
        row_key = (buyer_name, supplier_name)
        if row_key not in bucket.keys():
            bucket[row_key] = {params.buyer_id: buyer_id,
                               params.buyer_name: buyer_name,
                               params.supplier_id: supplier_id,
                               params.supplier_name: supplier_name}
        bucket[row_key][item[params.limit_type]] = item[params.amount]
    return list(bucket.values())


def user_info(username):
    return info_queries.get_user_info(username)


def get_reports(report_type, client_type=None, clientid=None, username=None, timeline=None):
    labels = []
    values = []
    clientid = info_queries.clientid_from_username(username)
    try:
        if report_type == 1:
            report = invoice_submissions_report(timeline, client_type, clientid, username)
            chart_type = 'bar'
            for item in report:
                labels.append(item[0])
                values.append(item[1])
            return chart_type, labels, values
        elif report_type == 2:
            report = cumulative_giv_report(client_type=client_type, clientid=clientid, timeline=timeline)
            chart_type = 'line'
            for date, amount in report:
                labels.append(str(date).replace('-', ''))
                values.append(float(amount))
            return chart_type, labels, values
    except Exception as e:
        raise Exception(e)


def invoice_submissions_report(timeline, client_type=None, clientid=None, username=None):
    first_date = times.date_with_delta(timeline)
    last_date = times.current_date()
    date_range = times.date_range(first_date, last_date)
    submissions = info_queries.invoice_submissions(first_date, last_date, client_type,
                                                   client_id=clientid, with_username=username)
    report = []
    for date in date_range:
        date = str(date).replace('-', '')
        if date in submissions:
            report.append([date, submissions[date]])
        else:
            report.append([date, 0])
    return report


def cumulative_giv_report(client_type=None, clientid=None, timeline=None,
                          first_date=None, last_date=None, invoice_id=None):
    try:
        if first_date is not None and last_date is not None:
            first_date = first_date
            last_date = last_date
        elif timeline is not None:
            first_date = times.date_with_delta(timeline)
            last_date = times.current_date()
        else:
            raise ValueError('Timeline is missing, or first date and last date are missing')

        if client_type == params.buyer:
            buyer_id = clientid
            supplier_id = None
        else:
            buyer_id = None
            supplier_id = clientid

        base_giv = info_queries.giv_data(buyer_id=buyer_id, supplier_id=supplier_id,
                                         last_date=first_date, invoice_id=invoice_id,
                                         breakdown=False)
        daily_giv = info_queries.giv_data(buyer_id=buyer_id, supplier_id=supplier_id,
                                          first_date=first_date, last_date=last_date,
                                          invoice_id=invoice_id, breakdown=True)
        for i in range(0, len(daily_giv)):
            if i == 0:
                daily_giv[i][1] += base_giv
            else:
                daily_giv[i][1] += daily_giv[i-1][1]
        return daily_giv
    except Exception as e:
        raise Exception(e)
