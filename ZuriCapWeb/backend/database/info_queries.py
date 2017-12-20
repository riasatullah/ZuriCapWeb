# By: Riasat Ullah

from ZuriCapWeb.backend.database.connector import DBConn
from ZuriCapWeb.utils import handyman, times
from ZuriCapWeb.variables import messages, params
import psycopg2
import traceback

conn = DBConn()

#####################
#   Login queries
#####################


def get_login_details(username, date=times.current_date()):
    '''
    Gets login details for users given a username
    :param username: user's username
    :param date: date to filter by
    :return: dictionary with pwd hash, pwd and id
    '''
    assert isinstance(username, str)
    query = '''
            select pwd_salt, pwd_hash, id_no
            from authorized_signatories
            where username = '{0}' and
                access_start <= '{1}' and
                access_end > '{1}'
            '''.format(username, date)
    try:
        result = conn.fetch(query)
        data = dict()
        for pwd_salt, pwd_hash, id_no in result:
            data = {params.salt: pwd_salt,
                    params.hash_password: pwd_hash,
                    params.id: id_no}
        return data
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_loging_failed) from e
    except TypeError as e:
        err = 'Username: expected string; received ' + type(username)
        raise TypeError(err) from e


def get_admin_login(username, date=times.current_date()):
    '''
    Gets login details for admins given a username
    :param username: user's username
    :return: dictionary with pwd hash, pwd and id
    '''
    assert isinstance(username, str)
    query = '''
            select rm_pwd_salt, rm_pwd_hash, employee_id
            from rms
            where rm_username = '{0}' and
                startdate <= '{1}' and
                enddate > '{1}'
            '''.format(username, date)
    try:
        result = conn.fetch(query)
        data = dict()
        for pwd_salt, pwd_hash, id_no in result:
            data = {params.salt: pwd_salt,
                    params.hash_password: pwd_hash,
                    params.id: id_no}
        return data
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_loging_failed) from e
    except TypeError as e:
        err = 'Username: expected string; received ' + type(username)
        raise TypeError(err) from e


#########################
# Relation queries
#########################
def get_relations(buyer_id=None, buyer_user=None, supplier_id=None, supplier_user=None, on_date=None):
    '''
    Gets relations between clients
    :param buyer_id: clientid of the buyer
    :param buyer_user: username of an authorized signatory of the buyer
    :param supplier_id: clientid of the supplier
    :param supplier_user: username of an authorized signatory of the supplier
    :param on_date: date to check for relations
    :return: list --> dictionaries with relation details
    '''
    conditions = []
    if buyer_id is not None:
        conditions.append('buyer_clientid in ({0})'.format(handyman.convert_int_to_string(buyer_id)))
    if buyer_user is not None:
        conditions.append('buyer_clientid in ({0})'.format(with_clientid_from_username_query(buyer_user)))
    if supplier_id is not None:
        conditions.append('supplier_clientid in ({0})'.format(handyman.convert_int_to_string(supplier_id)))
    if supplier_user is not None:
        conditions.append('supplier_clientid in ({0})'.format(with_clientid_from_username_query(supplier_user)))
    if on_date is not None:
        conditions.append('''
                            rel.startdate <= '{0}' and
                            rel.enddate > '{0}' and
                            cl.startdate <= '{0}' and
                            cl.enddate > '{0}' and
                            cl2.startdate <= '{0}' and
                            cl2.enddate > '{0}'
                          '''.format(on_date))
    query = '''
            select rel.buyer_clientid, cl.client_name as buyer,
                rel.supplier_clientid, cl2.client_name as supplier,
                buyer_fraction, supplier_fraction,
                buyer_approval_allowed, supplier_approval_allowed, rm_name,
                rel.startdate, rel.enddate
            from relations as rel
            join clients as cl
            on cl.clientid = buyer_clientid
            join clients as cl2
            on cl2.clientid = supplier_clientid
            {0}
            order by enddate desc, buyer_name, supplier_name
            '''.format(handyman.aggregate_conditions(conditions))
    try:
        result = conn.fetch(query)
        data = []
        for buyer_id, buyer_name, supplier_id, supplier_name, buyer_fraction, supplier_fraction, \
            buyer_approval, supplier_approval, rm_name, start_, end_ in result:
            data.append({params.buyer_id: buyer_id,
                         params.buyer_name: buyer_name,
                         params.supplier_id: supplier_id,
                         params.supplier_name: supplier_name,
                         params.buyer_fraction: buyer_fraction,
                         params.supplier_fraction: supplier_fraction,
                         params.buyer_approval: buyer_approval,
                         params.supplier_approval: supplier_approval,
                         params.rm_name: rm_name,
                         params.start_date: start_,
                         params.end_date: end_})
        return data
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e
    except Exception as e:
        raise Exception(e)


def get_client_type(clientid=None, username=None, date=None):
    '''
    Gets the type of the client
    :param clientid: client's id
    :param username: username
    :param date: the date to look for
    :return: list --> dictionary containing details
    '''
    conditions = []
    if date is None:
        date = times.current_date()
    conditions.append("startdate <= '{0}' and enddate > '{0}'".format(date))
    if clientid is not None:
        conditions.append('clientid in ({0})'.format(handyman.convert_int_to_string(clientid)))
    if username is not None:
        conditions.append('clientid in ({0})'.format(with_clientid_from_username_query(username)))
    query = '''
            select clientid, buyer, supplier
            from clients
            {0}
            '''.format(handyman.aggregate_conditions(conditions))
    try:
        results = conn.fetch(query)
        data = []
        for item in results:
            data.append({params.client_id: item[0],
                         params.buyer: item[1],
                         params.supplier: item[2]})
        return data
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_payments(username, client_type, offset=0, limit=50):
    assert isinstance(username, str)
    assert isinstance(client_type, str)

    client_col_to_get = 'buyer_id'
    if client_type == 'supplier':
        client_col_to_get = 'supplier_id'

    query = '''
            (select iv.invoice_id, payment_date,
                'Financing - Invoice ' || reference_id || ' - ' || supplier_name as description,
                fp.currency, -paid_amount as amount
            from forwarded_payments as fp join invoices as iv
            using (invoice_id)
            where {0} = (select clientid from authorized_signatories where username = '{1}')
            union
            select iv.invoice_id, payment_date,
                'Transaction cost - Invoice ' || reference_id || ' - ' || supplier_name as description,
                fp.currency, -additional_fees as amount
            from forwarded_payments as fp join invoices as iv
            using (invoice_id)
            where {0} = (select clientid from authorized_signatories where username = '{1}')
            union
            select iv.invoice_id, payment_date,
                'Repayments for Invoice ' || reference_id || ' - ' || supplier_name as description,
                rp.currency, received_amount as amount
            from received_payments as rp join invoices as iv
            using (invoice_id)
            where {0} = (select clientid from authorized_signatories where username = '{1}')
            )
            order by payment_date desc
            {3} offset {2}
            '''.format(client_col_to_get,
                       username,
                       str(offset),
                       '' if limit <= 0 else ' limit ' + str(limit))
    try:
        result = conn.fetch(query)
        return result
    except Exception as e:
        raise Exception(e)


def fetch_payments(invoice_id=None, buyer_id=None, supplier_id=None,
                   payment_type=None, cancelled=None, side=None,
                   limit=None, offset=None):
    '''
    Gets details about payments.
    :param invoice_id: invoice id(s) to filter with
    :param buyer_id: buyer id(s) to filter with
    :param supplier_id: supplier id(s) to filter with
    :param payment_type: payment type to filter with
    :param cancelled: True or False; filter by whether a payment is cancelled or not
    :param side: 1 or 2; 1 if the payment is coming in to ZuriCap; 2 if it is going out
    :param limit: the number of rows to limit by
    :param offset: the number of rows to skip
    :return: list of dictionaries with payment details
    '''
    invoice_conditions = []
    if invoice_id is not None:
        invoice_conditions.append('invoice_id in ({0})'.format(handyman.convert_int_to_string(invoice_id)))
    if buyer_id is not None:
        invoice_conditions.append('buyer_id in ({0})'.format(handyman.convert_int_to_string(buyer_id)))
    if supplier_id is not None:
        invoice_conditions.append('supplier_id in ({0})'.format(handyman.convert_int_to_string(supplier_id)))

    payment_conditions = []
    if payment_type is not None:
        payment_conditions.append("payment_type = '{0}'".format(payment_type))
    if cancelled is not None:
        if type(cancelled) is bool:
            payment_conditions.append('cancelled = {0}'.format(cancelled))
    if side is not None:
        if side in [1, 2]:
            payment_conditions.append('side = {0}'.format(side))

    query = '''
            with t1 as(
            select invoice_id from invoices {0}
            )
            ,t2 as(
            select payment_id from forwarded_payments where invoice_id in (select invoice_id from t1)
            union
            select payment_id from received_payments where invoice_id in (select invoice_id from t1)
            )
            , t3 as(
            select * from payments where payment_id in (select payment_id from t2)
            order by payment_date desc
            {1} {2}
            )
            , t4 as(
            select payment_id, payment_date, side, currency, amount, transaction_cost,
                cancelled, paid_by, paid_to, client_name as paid_by_name
            from t3 left join clients on paid_by = clientid
            )
            select t4.*, client_name as paid_to_name
            from t4 left join clients on paid_to = clientid
            order by payment_date desc, payment_id desc
            '''.format(handyman.aggregate_conditions(invoice_conditions),
                       ' limit {0} '.format(limit) if limit is not None and type(limit) is int else '',
                       ' offset {0} '.format(offset) if offset is not None and type(offset) is int else '')
    try:
        results = conn.fetch(query)
        data = []
        for id_, date_, side_, currency_, amount_, cost_, cancelled_status,\
            paid_by, paid_to, paid_by_name, paid_to_name in results:
            data.append({params.payment_id: id_,
                         params.payment_date: date_,
                         params.side: side_,
                         params.currency: currency_,
                         params.amount: amount_,
                         params.transaction_cost: cost_,
                         params.cancelled_status: cancelled_status,
                         params.paid_by: paid_by,
                         params.paid_to: paid_to,
                         params.buyer_name: paid_by_name,
                         params.supplier_name: paid_to_name}
                        )
        return data
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


########################
# Invoices
########################
def get_invoice(invoice_id=None, buyer_id=None, supplier_id=None, status=None, limit_rows=0, offset=None):
    '''
    Gets the details of invoice(s)
    :param invoice_id: the invoice id; default=None
    :param buyer_id: client id of the buyer; default=None
    :param supplier_id: supplier id of the supplier; default=None
    :param status: status of the invoice (OPEN, CLOSED, etc); default None
    :param limit_rows: number of rows to return
    :param offset: number of rows of offsets to apply
    :return: dictionary --> dictionaries; [invoide id] --> details
    '''
    conditions = []
    if invoice_id is not None:
        conditions.append('invoice_id in ({0})'.format(handyman.convert_int_to_string(invoice_id)))
    if buyer_id is not None:
        conditions.append('buyer_id in ({0})'.format(handyman.convert_int_to_string(buyer_id)))
    if supplier_id is not None:
        conditions.append('supplier_id in ({0})'.format(handyman.convert_int_to_string(supplier_id)))
    if status is not None:
        conditions.append("status = '{0}'".format(status))
    query = '''
            select invoice_id, reference_id,
                buyer_id, buyer_name,
                supplier_id, supplier_name,
                financing_product_id, financing_product,
                submission_date, invoice_date, approval_date,
                item_description, currency, invoice_total, status
            from invoices
            {0}
            order by submission_date desc
            {1} {2}
            '''.format(handyman.aggregate_conditions(conditions),
                       ' limit {0} '.format(str(limit_rows)) if limit_rows != 0 else '',
                       '' if offset is None else ' offset {0} '.format(offset))
    try:
        result = conn.fetch(query)
        cols = [params.invoice_id, params.invoice_ref_id,
                params.buyer_id, params.buyer_name,
                params.supplier_id, params.supplier_name,
                params.financing_product_id, params.financing_product,
                params.submitted_on, params.invoice_date,
                params.approved_on, params.description,
                params.currency, params.invoice_total,
                params.invoice_status]
        all_invoices = dict()
        if len(result) > 0:
            for item in result:
                invoice = dict()
                if len(item) == len(cols):
                    for i in range(0, len(cols)):
                        invoice[cols[i]] = item[i]
                    all_invoices[invoice[params.invoice_id]] = invoice
                else:
                    raise Exception('Incorrect number of columns passed')
        return all_invoices
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_forwarded_payments(invoice_id=None, buyer_id=None, supplier_id=None,
                           first_date=None, last_date=None):
    '''
    Gets financing details of invoices
    :param invoice_id: invoice id (list or int); default=None
    :param buyer_id: buyer's client id; default=None
    :param supplier_id: supplier's client id; default=None
    :param first_date: first date to fetch; default=None
    :param last_date: last date to fetch; default=None
    :return: dictionary -> list[dictionaries]; keyed on invoice id
    '''
    conditions = []
    if invoice_id is not None:
        conditions.append('invoice_id in ({0})'.format(handyman.convert_int_to_string(invoice_id)))
    if buyer_id is not None:
        conditions.append('invoice_id in ({0})'.format(with_invoiceid_from_clientid(params.buyer,
                                                                                    buyer_id)))
    if supplier_id is not None:
        conditions.append('invoice_id in ({0})'.format(with_invoiceid_from_clientid(params.supplier,
                                                                                    supplier_id)))
    if first_date is not None:
        conditions.append("payment_date >= '{0}'".format(first_date))
    if last_date is not None:
        conditions.append("payment_date <= '{0}'".format(last_date))
    try:
        query = '''
                select invoice_id, payment_date, paid_amount, additional_fees
                from forwarded_payments
                {0}
                order by payment_date
                '''.format(handyman.aggregate_conditions(conditions))
        financing = dict()
        result = conn.fetch(query)
        if len(result) > 0:
            for invoice_id, payment_date, financed_amount, transaction_cost in result:
                if invoice_id not in financing:
                    financing[invoice_id] = []
                financing[invoice_id].append({params.financing_date: payment_date,
                                              params.financed_amount: financed_amount,
                                              params.transaction_cost: transaction_cost})
        return financing
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_received_payments(invoice_id=None, buyer_id=None, supplier_id=None,
                          first_date=None, last_date=None):
    '''
    Gets repayment details of invoices
    :param invoice_id: invoice id (list or int); default=None
    :param buyer_id: buyer's client id; default=None
    :param supplier_id: supplier's client id; default=None
    :param first_date: first date to fetch; default=None
    :param last_date: last date to fetch; default=None
    :return: dictionary -> list[dictionaries]; keyed on invoice id
    '''
    conditions = []
    if invoice_id is not None:
        conditions.append('invoice_id in ({0})'.format(handyman.convert_int_to_string(invoice_id)))
    if buyer_id is not None:
        conditions.append('invoice_id in ({0})'.format(with_invoiceid_from_clientid(params.buyer,
                                                                                    buyer_id)))
    if supplier_id is not None:
        conditions.append('invoice_id in ({0})'.format(with_invoiceid_from_clientid(params.supplier,
                                                                                    supplier_id)))
    if first_date is not None:
        conditions.append("payment_date >= '{0}'".format(first_date))
    if last_date is not None:
        conditions.append("payment_date <= '{0}'".format(last_date))
    try:
        query = '''
                select invoice_id, payment_date, received_amount, principal_repaid, discount_fees
                from received_payments
                {0}
                order by payment_date
                '''.format(handyman.aggregate_conditions(conditions))
        repayments = dict()
        result = conn.fetch(query)
        if len(result) > 0:
            for invoice_id, payment_date, repaid_amount, principal_repaid, discount_fees in result:
                if invoice_id not in repayments:
                    repayments[invoice_id] = []
                repayments[invoice_id].append({params.repayment_date: payment_date,
                                               params.principal_repaid: principal_repaid,
                                               params.repaid_amount: repaid_amount,
                                               params.discount_fees: discount_fees})
        return repayments
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_rates(date):
    '''
    Gets the rates for all products that
    are/were valid on a given date
    :param date: date for which the rates should be fetched
    :return: dictionary -> lists of rates; keyed on product id
    '''
    query = '''
            select product_id, startperiod, endperiod, base_rate
            from product_rates
            where rate_startdate <= '{0}' and
                rate_enddate > '{0}'
            '''.format(date)
    try:
        results = conn.fetch(query)
        rates_map = dict()
        if len(results) > 0:
            for productid, startperiod, endperiod, base_rate in results:
                if productid not in rates_map:
                    rates_map[productid] = []
                rates_map[productid].append([startperiod,
                                             endperiod,
                                             base_rate])
            return rates_map
        else:
            raise LookupError('Financing product rates are not available')
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_overridden_rates(client_id=None, date=None):
    '''
    Gets overriden rates
    :param date: the date for which the rates should be retrieved for
    :param client_id: the clientid(s) the rates should be retrieved for
    :return: dictionary -> lists of dictionaries | keyed on clientid
    '''
    conditions = []
    if client_id is not None:
        conditions.append(" clientid in ({0}) ".format(handyman.convert_int_to_string(client_id)))
    if date is not None:
        conditions.append(" startdate <= '{0}' and enddate > '{0}' ".format(date))
    query = '''
            select clientid, product_id, startdate, enddate, buyer_rate, supplier_rate
            from rate_overrides
            {0}
            '''.format(handyman.aggregate_conditions(conditions))
    try:
        results = conn.fetch(query)
        data = dict()
        for clientid, productid, startdate, enddate, buyer_rate, supplier_rate in results:
            if clientid not in data.keys():
                data[clientid] = []
            data[clientid].append({params.financing_product_id: productid,
                                   params.start_date: startdate,
                                   params.end_date: enddate,
                                   params.buyer_rate: buyer_rate,
                                   params.supplier_rate: supplier_rate})
        return data
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_client_limits(clientid=None, date=None):
    conditions = []
    if clientid is not None:
        conditions.append('clientid in ({0})'.format(handyman.convert_int_to_string(clientid)))
    if date is not None:
        conditions.append('''client_limits.startdate <= '{0}' and
                             client_limits.enddate > '{0}' and
                             clients.startdate <= '{0}' and
                             clients.enddate > '{0}'
                          '''.format(date))
    query = '''
            select client_limits.startdate, client_limits.enddate,
                client_limits.clientid, clients.client_name,
                client_limits.limit_id, client_limits.limit_type,
                client_limits.currency, client_limits.amount
            from client_limits
            join clients using(clientid)
            {0}
            '''.format(handyman.aggregate_conditions(conditions))
    try:
        results = conn.fetch(query)
        holder = []
        for start_, end_, client_id, name_, limit_id, limit_type, currency, amount in results:
            holder.append({params.start_date: start_,
                           params.end_date: end_,
                           params.client_id: client_id,
                           params.client_name: name_,
                           params.limit_id: limit_id,
                           params.limit_type: limit_type,
                           params.currency: currency,
                           params.amount: amount})
        return holder
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_relation_limits(buyer_id=None, supplier_id=None, date=None):
    conditions = []
    if buyer_id is not None:
        conditions.append('rl.buyer_clientid in ({0})'.format(handyman.convert_int_to_string(buyer_id)))
    if supplier_id is not None:
        conditions.append('rl.supplier_clientid in ({0})'.format(handyman.convert_int_to_string(supplier_id)))
    if date is not None:
        conditions.append('''
                            rl.startdate <= '{0}' and
                            rl.enddate > '{0}' and
                            cl1.startdate <= '{0}' and
                            cl1.enddate > '{0}' and
                            cl2.startdate <= '{0}' and
                            cl2.enddate > '{0}'
                          '''.format(date))
    query = '''
            select rl.startdate, rl.enddate,
                    rl.buyer_clientid, cl1.client_name as buyer_name,
                    rl.supplier_clientid, cl2.client_name as supplier_name,
                    rl.limit_id, rl.limit_type,
                    rl.currency, rl.amount
            from relation_limits as rl
            join clients as cl1 on rl.buyer_clientid = cl1.clientid
            join clients as cl2 on rl.supplier_clientid = cl2.clientid
            {0}
            '''.format(handyman.aggregate_conditions(conditions))
    try:
        results = conn.fetch(query)
        holder = []
        for start_, end_, buyer_clientid, buyer_name, supplier_clientid, supplier_name,\
            limit_id, limit_type, currency, amount in results:
            holder.append({params.start_date: start_,
                           params.end_date: end_,
                           params.buyer_id: buyer_clientid,
                           params.buyer_name: buyer_name,
                           params.supplier_id: supplier_clientid,
                           params.supplier_name: supplier_name,
                           params.limit_id: limit_id,
                           params.limit_type: limit_type,
                           params.currency: currency,
                           params.amount: amount})
        return holder
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def clientid_from_username(username):
    '''
    Returns the client id of an associated username
    :param username: username of the user
    :return: client id
    '''
    assert isinstance(username, str)
    query = '''
            select clientid from authorized_signatories where username = '{0}'
            '''.format(username)
    try:
        results = conn.fetch(query)
        return results[0][0]
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def clientid_from_name(name):
    assert isinstance(name, str)
    query = '''
            select clientid from clients where client_name = '{0}'
            '''.format(name)
    try:
        results = conn.fetch(query)
        return results[0][0]
    except Exception as e:
        raise Exception(e)


def name_from_clientid(clientid=None, date=None):
    '''
    Query to get a client's id and name
    :param clientid: client id to filter by
    :param date: date to filter by
    :return: dictionary [client id] --> client name
    '''
    conditions = []
    if clientid is not None:
        conditions.append('clientid in ({0})'.format(handyman.convert_int_to_string(clientid)))
    if date is not None:
        conditions.append("startdate <= '{0}' and enddate > '{0}'".format(date))
    query = '''
            select clientid, client_name from clients {0}
            '''.format(handyman.aggregate_conditions(conditions))
    try:
        print(query)
        result = conn.fetch(query)
        info = dict()
        if len(result) > 0:
            for clientid, name in result:
                info[clientid] = name
        print(info)
        return info
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def financing_product_from_id(financing_product_id):
    str_product_ids = handyman.convert_int_to_string(financing_product_id)
    query = '''
            select product_id, product_name from products where product_id in ({0})
            '''.format(str_product_ids)
    try:
        result = conn.fetch(query)
        info = dict()
        if len(result) > 0:
            for product_id, product_name in result:
                info[product_id] = product_name
        return info
    except Exception as e:
        raise Exception(e)


def get_user_info(username):
    query = '''
            select client_name, first_name, last_name, title, email, office_phone, cell_phone
            from authorized_signatories as auth
            join clients using(clientid)
            where username = '{0}'
            '''.format(username)
    try:
        result = conn.fetch(query)
        if len(result) > 1:
            raise Exception('Expected 1 row; ' + str(len(result)) + ' returned')
        data = {}
        for client_name, first_name, last_name, title, email, office_phone, cell_phone in result:
            data[params.client_name] = client_name
            data[params.first_name] = first_name
            data[params.last_name] = last_name
            data[params.title] = title
            data[params.email] = email
            data[params.office_phone] = office_phone
            data[params.cell_phone] = cell_phone
        return data
    except Exception as e:
        raise Exception(e)


def giv_data(buyer_id=None, supplier_id=None, first_date=None, last_date=None, invoice_id=None, breakdown=True):
    '''
    Gets the GIV value or the breakdown of the GIV value
    :param buyer_id: client id of the buyer
    :param supplier_id: client id of the supplier
    :param first_date: the minimum date to fetch for (inclusive)
    :param last_date: the maximum date to fetch for (incusive)
    :param invoice_id: invoice id(s)
    :param breakdown: True if breakdown of day to day GIV is required; False if the sum is required
    :return:
    '''
    invoice_conditions = ['cancelled=False']
    if invoice_id is not None:
        invoice_conditions.append('invoice_id in ({0})'.format(handyman.convert_int_to_string(invoice_id)))
    if buyer_id is not None:
        invoice_conditions.append('invoice_id in ({0})'.format(with_invoiceid_from_clientid(params.buyer, buyer_id)))
    if supplier_id is not None:
        invoice_conditions.append('invoice_id in ({0})'.format(with_invoiceid_from_clientid(params.supplier,
                                                                                            supplier_id)))
    str_payment_conditions = ''
    if first_date is not None:
        str_payment_conditions += " and " + "payment_date >= '{0}'".format(first_date)
    if last_date is not None:
        str_payment_conditions += " and " + "payment_date <= '{0}'".format(last_date)

    main_query = 'select payment_date, sum(amount) from t2 group by payment_date order by payment_date'
    if not breakdown:
        main_query = 'select sum(amount) from t2'
    try:
        query = '''
                with t1 as(
                select invoice_id from invoices {0}
                ),
                t2 as(
                select payment_date, sum(paid_amount) as amount from forwarded_payments
                    where invoice_id in (select invoice_id from t1) {1}
                    group by payment_date
                union
                select payment_date, -sum(principal_repaid) as amount from received_payments
                    where invoice_id in (select invoice_id from t1) {1}
                    group by payment_date
                )
                {2}
                '''.format(handyman.aggregate_conditions(invoice_conditions),
                           str_payment_conditions,
                           main_query)
        result = conn.fetch(query)
        if breakdown:
            holder = []
            for payment_date, amount in result:
                holder.append([payment_date, amount])
            return holder
        else:
            if len(result) > 0:
                return result[0][0]
            return 0
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def invoice_submissions(first_date, last_date, client_type=None, client_id=None, with_username=None):
    query = '''
            select submission_date, invoice_total from invoices
            where cancelled='f' and
                submission_date >= '{0}' and
                submission_date <= '{1}'
                {2}
                order by submission_date
            '''.format(first_date,
                       last_date,
                       with_clientid_condition(client_type, client_id, with_username))
    try:
        results = conn.fetch(query)
        data = dict()
        for date, amount in results:
            date = str(date).replace('-', '')
            data[date] = float(amount)
        return data
    except Exception as e:
        raise Exception(e)


def invoice_count_per_month(first_date, last_date, client_type=None, client_id=None, with_username=None):
    query = '''
            select to_char(submission_date, 'YYYY') || '-' || to_char(submission_date, 'Mon') as month, count(*)
            from invoices
            where cancelled='f' and
                submission_date >= '{0}' and
                submission_date <= '{1}'
                {2}
            group by month
            order by month
            '''.format(first_date,
                       last_date,
                       with_clientid_condition(client_type, client_id, with_username))
    try:
        results = conn.fetch(query)
        return results
    except Exception as e:
        raise Exception(e)


def client_name_search(date, name=None, ids=None):
    conditions = []
    if name is not None:
        conditions.append("lower(client_name) like '%{0}%'".format(str(name).lower()))
    if ids is not None:
        conditions.append('clientid in ({0})'.format(handyman.convert_int_to_string(ids)))
    query = '''
            select clientid, client_name, case
                when buyer = true and supplier = false then 'Buyer'
                when buyer = false and supplier = true then 'Supplier'
                when buyer = true and supplier = true then 'Both'
            end as client_type, industry, case
                when startdate <= '{0}' and enddate > '{0}' then 'Active'
                else 'Dead'
            end as status
            from clients
            {1}
            order by client_name
            '''.format(date, handyman.aggregate_conditions(conditions))
    try:
        result = conn.fetch(query)
        data = []
        if len(result) > 0:
            for client_id, name, client_type, industry, status in result:
                data.append({params.client_id: client_id,
                             params.client_name: name,
                             params.client_type: client_type,
                             params.industry: industry,
                             params.client_status: status})
        return data
    except Exception as e:
        raise Exception(e)


def client_details(clientid, date):
    '''
    Query that retrieves a particular client's information.
    Can only get 1 client's information at a time.
    :param clientid: client's id
    :param date: the date to look for
    :return: dictionary with client details
    '''
    query = '''
            select client_name, address, city, zip, country, phone,
            registration_no, tax_pin, description, industry, size,
            case when buyer = true and supplier = false then 'BUYER'
                when buyer = false and supplier = true then 'SUPPLIER'
                when buyer = true and supplier = true then 'BOTH'
            end as client_type
            from clients
            where clientid = {0} and
                startdate <= '{1}' and
                enddate > '{1}'
            '''.format(clientid, date)
    try:
        result = conn.fetch(query)
        data = dict()
        for item in result:
            data[params.client_name] = item[0]
            data[params.address] = item[1]
            data[params.city] = item[2]
            data[params.client_zip] = item[3]
            data[params.country] = item[4]
            data[params.phone] = item[5]
            data[params.registration] = item[6]
            data[params.tax_pin] = item[7]
            data[params.description] = item[8]
            data[params.industry] = item[9]
            data[params.client_size] = item[10]
            data[params.client_type] = item[11]
        return data
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def get_performance_fee(date=times.current_date()):
    '''
    Gets the applicable performance fee on a given date
    :param date: date to fetch the rate for
    :return: performance fee rate
    '''
    query = '''
            select fee_percentage from performance_fee
            where startdate <= '{0}' and
                enddate > '{0}'
            '''.format(date)
    try:
        result = conn.fetch(query)
        return float(result[0][0])
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def rm_details(rm_name=None, date=None):
    '''
    Query to get rms' details
    :param rm_id: rms to filter by
    :param date: date to filter by
    :return: list of dictionaries
    '''
    conditions = []
    if rm_name is not None:
        conditions.append("rm_name = '{0}')".format(rm_name))
    if date is not None:
        conditions.append("startdate <= '{0}' and enddate > '{0}'".format(date))
    query = '''
            select rm_username, rm_name, employee_id from rms {0}
            '''.format(handyman.aggregate_conditions(conditions))
    try:
        result = conn.fetch(query)
        info = dict()
        if len(result) > 0:
            for rm_username, rm_name, employee_id in result:
                info[rm_username] = {params.rm_name: rm_name,
                                     params.id: employee_id}
        return info
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def with_clientid_from_username_query(username):
    date = times.current_date()
    return '''select clientid from authorized_signatories
                where access_start <= '{1}' and
                access_end > '{1}' and
                username = '{0}'
            '''.format(username, date)


def with_clientid_condition(client_type, client_id, with_username):
    add_condition = ''
    client_cond = ''
    if with_username is not None:
        client_cond = with_clientid_from_username_query(with_username)
    if client_id is not None:
        client_cond = handyman.convert_int_to_string(client_id)
    if client_cond != '':
        if client_type == params.buyer:
            add_condition = ' and buyer_id in ({0})'.format(client_cond)
        elif client_type == params.supplier:
            add_condition = ' and supplier_id in ({0})'.format(client_cond)
    return add_condition


def with_invoiceid_from_clientid(client_type, clientid):
    client_column = 'buyer_id'
    if client_type == 'supplier':
        client_column = 'supplier_id'
    return "select invoice_id from invoices where {0} in ({1})".format(client_column, clientid)


def with_invoiceid_from_username(client_type, username):
    client_column = 'buyer_id'
    if client_type == 'supplier':
        client_column = 'supplier_id'
    return '''select invoice_id from invoices where {0} in
            (select clientid from authorized_signatories where username = '{1}')
            '''.format(client_column, username)


def close_connection():
    conn.disconnect()
