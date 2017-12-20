# By: Riasat Ullah

from ZuriCapWeb.backend.database.connector import DBConn
from ZuriCapWeb.utils import times, handyman
from ZuriCapWeb.variables import messages, params
import psycopg2

conn = DBConn()


def add_new_invoice(data):
    try:
        query = '''
                insert into invoices
                (reference_id, buyer_id, buyer_name, supplier_id, supplier_name,
                financing_product_id, financing_product, submission_timestamp,
                submission_date, invoice_date, item_description,
                currency, invoice_total, submittedby, submission_overridden,
                approval_date, approved_by, status)
                values
                ('{0}', {1}, '{2}', {3}, '{4}',
                {5}, '{6}', '{7}',
                '{8}', '{9}', '{10}',
                '{11}', {12}, '{13}', '{14}',
                '{15}', '{16}', '{17}')
                '''.format(data[params.invoice_ref_id],
                           data[params.buyer_id],
                           data[params.buyer_name],
                           data[params.supplier_id],
                           data[params.supplier_name],
                           data[params.financing_product_id],
                           data[params.financing_product],
                           data[params.submission_timestamp],
                           data[params.submitted_on],
                           data[params.invoice_date],
                           data[params.description],
                           data[params.currency],
                           data[params.invoice_total],
                           data[params.submitted_by],
                           data[params.submission_overridden],
                           data[params.approved_on],
                           data[params.approved_by],
                           data[params.invoice_status])
        conn.execute(query)
        return 0
    except Exception as e:
        raise Exception(e)


def close_invoice(data, cancelled=False):
    cancel_query = '''
                    update invoices set cancelled = 't',
                        cancelled_timestamp = '{0}', cancelled_by = '{1}'
                        where invoice_id = {2};
                   '''.format(data[params.updated_timestamp],
                              data[params.updated_by],
                              data[params.invoice_id])
    query = '''
            begin;

            insert into closed_invoices
            (invoice_id, closing_date, status, currency,
            financed, transaction_costs, principal_repaid, total_repayments,
            discount_fees, unrealized_pnl, updated_by, updated_timestamp, notes)
            values
            ({0), '{1}', '{2}', '{3}', {4}, {5}, {6},
            {7}, {8}, {9}, '{10}', '{11}', '{12}');

            update invoices set status = '{2}' where invoice_id = {0};

            {13}

            end;
            '''.format(data[params.invoice_id],
                       data[params.completion_date],
                       data[params.invoice_status],
                       data[params.currency],
                       data[params.total_financed],
                       data[params.transaction_cost],
                       data[params.principal_repaid],
                       data[params.total_repayments],
                       data[params.discount_fees],
                       data[params.unrealized_pnl],
                       data[params.updated_by],
                       data[params.updated_timestamp],
                       data[params.notes],
                       cancel_query if cancelled else '')
    try:
        print(query)
    except Exception as e:
        raise Exception(e)


def add_client(data):
    query = '''
            insert into clients
            (startdate, enddate, buyer, supplier, client_name,
            address, city, zip, country, phone,
            registration_no, tax_pin, description, industry, size)
            '''.format(data[params.start_date],
                       data[params.end_date],
                       data[params.buyer],
                       data[params.supplier],
                       data[params.client_name],
                       data[params.address],
                       data[params.city],
                       data[params.client_zip],
                       data[params.country],
                       data[params.phone],
                       data[params.registration],
                       data[params.tax_pin],
                       data[params.description],
                       data[params.industry],
                       data[params.client_size])
    try:
        conn.execute(query)
    except Exception as e:
        raise Exception(e)


def add_user(data):
    query = '''
            insert into authorized_signatories
            (username, pwd_salt, pwd_hash, id_type, id_no,
            access_start, access_end, clientid, first_name, last_name,
            birth_date, title, email, office_phone, cell_phone,
            question_1, answer_1, question_2, answer_2, notes)
            values
            ('{0}', '{1}', '{2}', '{3}', '{4}',
            '{5}', '{6}', {7}, '{8}', '{9}',
            '{10}', '{11}', '{12}', '{13}', '{14}',
            '{15}', '{16}', '{17}', '{18}', '{19}')
            '''.format(data[params.username],
                       data[params.salt],
                       data[params.hash_password],
                       data[params.id_type],
                       data[params.id],
                       data[params.start_date],
                       data[params.end_date],
                       data[params.client_id],
                       data[params.first_name],
                       data[params.last_name],
                       data[params.birth_date],
                       data[params.title],
                       data[params.email],
                       data[params.office_phone],
                       data[params.cell_phone],
                       data[params.question_1],
                       data[params.answer_1],
                       data[params.question_2],
                       data[params.answer_2],
                       data[params.notes])
    try:
        conn.execute(query)
    except Exception as e:
        raise Exception(e)


def update_password(username, salt, new_hash_pwd):
    query = '''
            update authorized_signatories
            set pwd_salt = '{0}', pwd_hash = '{1}'
            where username = '{2}'
            '''.format(salt,
                       new_hash_pwd,
                       username)
    try:
        print(query)
    except Exception as e:
        raise Exception(e)


def add_forwarded_payment(payment_date, currency, amount, fees, payment_type, paid_to,
                          updated_by, notes, invoice_id, invoice_percentage):
    query = '''
            select make_payment('{0}', '{1}', {2}, {3},
                                '{4}', 0, {5}, '{6}',
                                '{7}', '{8}', {9}, {10})
            '''.format(payment_date, currency, str(amount), str(fees),
                       payment_type, str(paid_to), updated_by,
                       times.current_timestamp(), notes,
                       str(invoice_id), str(invoice_percentage))
    try:
        conn.execute(query)
    except Exception as e:
        raise Exception(e)


def add_received_payment(payment_date, currency, amount, fees, payment_type,
                         paid_by, updated_by, notes, invoices, closures):
    details_str = ''
    details = []
    for item in invoices:
        details.append('{' + ','.join(str(element) for element in item) + '}')
    if len(details) > 0:
        details_str += '{' + ','.join(details) + '}'

    query = '''
            begin;

            select accept_payment('{0}', '{1}', {2}, {3},
                                  '{4}', {5}, 0, '{6}',
                                  '{7}', '{8}', {9});

            update invoices set status = 'CLOSED' where invoice_id in ({10});

            end;
            '''.format(payment_date, currency, str(amount), str(fees),
                       payment_type, str(paid_by), updated_by,
                       times.current_timestamp(), notes, details_str,
                       handyman.convert_int_to_string(closures))
    try:
        conn.execute(query)
    except Exception as e:
        raise Exception(e)


def add_new_client(data):
    '''
    Inserts a new client
    :param data: a dictionary of data to add
    '''
    query = '''
            begin;

            with t1 as(
            select max(clientid) + 1 as id from clients
            )
            , t2 as(
            insert into clients
            (select id, '{0}', '99990101', {1}, {2},
            '{3}', '{4}', '{5}', '{6}', '{7}',
            '{8}', '{9}', '{10}', '{11}', '{12}', '{13}' from t1)
            )
            , t3 as(
            insert into client_limits
            (select '{0}', '99990101', id, 1, 'discounting_max_giv', 'KES', 0 from t1)
            ), t4 as(
            insert into client_limits
            (select '{0}', '99990101', id, 2, 'discounting_max_single_iv', 'KES', 0 from t1)
            ), t5 as(
            insert into client_limits
            (select '{0}', '99990101', id, 3, 'discounting_max_invoice_count', 'KES', 0 from t1)
            ), t6 as(
            insert into client_limits
            (select '{0}', '99990101', id, 4, 'invoicing_max_giv', 'KES', 0 from t1)
            ), t7 as(
            insert into client_limits
            (select '{0}', '99990101', id, 5, 'invoicing_max_single_iv', 'KES', 0 from t1)
            )
            insert into client_limits
            (select '{0}', '99990101', id, 6, 'invoicing_max_invoice_count', 'KES', 0 from t1);

            end;
            '''.format(data[params.start_date],
                       True if data[params.client_type] in ['BUYER', 'BOTH'] else False,
                       True if data[params.client_type] in ['SUPPLIER', 'BOTH'] else False,
                       data[params.client_name],
                       data[params.address],
                       data[params.city],
                       data[params.client_zip],
                       data[params.country],
                       data[params.office_phone],
                       data[params.registration],
                       data[params.tax_pin],
                       data[params.description],
                       data[params.industry],
                       data[params.client_size])
    try:
        conn.execute(query)
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e
    except Exception as e:
        raise Exception(e)


def update_client_profile(data):
    '''
    Update's a client's details
    :param data: dictionary of data to update with
    '''
    query = '''
            update clients
            set buyer = {0},
                supplier = {1},
                address = '{2}',
                city = '{3}',
                zip = '{4}',
                country = '{5}'
                phone = '{6}',
                registration_no = '{7}',
                tax_pin = '{8}',
                description = '{9}',
                industry = '{10}',
                size = '{11}'
            where clientid = {12}
            '''.format(True if data[params.client_type] in ['BUYER', 'BOTH'] else False,
                       True if data[params.client_type] in ['SUPPLIER', 'BOTH'] else False,
                       data[params.address],
                       data[params.city],
                       data[params.client_zip],
                       data[params.country],
                       data[params.phone],
                       data[params.registration],
                       data[params.tax_pin],
                       data[params.description],
                       data[params.industry],
                       data[params.client_size],
                       data[params.client_id])
    try:
        print(query)
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def add_relation(data):
    '''
    Adds a new relation
    :param data: data for the relation
    '''
    query = '''
            begin;

            insert into relations values
            ('{0}', '99990101', {1}, '{2}',
            {3}, '{4}', {5}, {6},
            {7}, {8}, '{9}');

            insert into relation_limits values
            ('{0}', '99990101', {1}, {3}, 7, 'relation_max_giv', 'KES', 0),
            ('{0}', '99990101', {1}, {3}, 8, 'relation_max_single_iv', 'KES', 0),
            ('{0}', '99990101', {1}, {3}, 9, 'relation_max_invoice_count', 'KES', 0);

            end;
            '''.format(data[params.start_date],
                       str(data[params.buyer_id]),
                       data[params.buyer_name],
                       str(data[params.supplier_id]),
                       data[params.supplier_name],
                       data[params.buyer_fraction],
                       data[params.supplier_fraction],
                       True if data[params.buyer_approval] == 0 else False,
                       True if data[params.supplier_approval] == 0 else False,
                       data[params.rm_name])
    try:
        print(query)
        conn.execute(query)
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def edit_relation(buyer_id, supplier_id, data, date=None):
    '''
    Updates a relation
    :param buyer_id: buyer's client id
    :param supplier_id: supplier's client id
    :param data: data to update
    '''
    today = times.current_date()
    if date is not None:
        today = date
    query = '''
            begin;

            update relations set enddate = '{0}'
            where buyer_clientid = {1} and
                supplier_clientid = {2} and
                startdate <= '{0}' and
                enddate > '{0}';

            with t1 as(
            select client_name as buyer_name from clients where clientid = {1}
            )
            , t2 as(
            select client_name as supplier_name from clients where clientid = {2}
            )
            , t3 as(
            select t1.buyer_name, t2.supplier_name from t1, t2
            )
            insert into relations
            (select '{0}', '99990101', {1}, buyer_name, {2}, supplier_name,
            {3}, {4}, {5}, {6}, '{7}' from t3);

            end;
            '''.format(today,
                       str(buyer_id),
                       str(supplier_id),
                       str(data[params.buyer_fraction]),
                       str(data[params.supplier_fraction]),
                       True if int(data[params.buyer_approval]) == 0 else False,
                       True if int(data[params.supplier_approval]) == 0 else False,
                       data[params.rm_name])
    try:
        conn.execute(query)
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def save_client_limits(client_id, data, date=None, currency='KES'):
    '''
    Saves a client's limits
    :param client_id: client id
    :param data: data to update with
    :param date: date to set the changes for
    :param currency: currency of the limits
    '''
    today = times.current_date()
    if date is not None:
        today = date
    query = '''
            begin;

            update client_limits set enddate = '{0}'
            where startdate <= '{0}' and
                enddate > '{0}' and
                clientid = {1};

            insert into client_limits values
            ('{0}', '99990101', {1}, 1, 'discounting_max_giv', '{2}', {3}),
            ('{0}', '99990101', {1}, 2, 'discounting_max_single_iv', '{2}', {4}),
            ('{0}', '99990101', {1}, 3, 'discounting_max_invoice_count', '{2}', {5}),
            ('{0}', '99990101', {1}, 4, 'invoicing_max_giv', '{2}', {6}),
            ('{0}', '99990101', {1}, 5, 'invoicing_max_single_iv', '{2}', {7}),
            ('{0}', '99990101', {1}, 6, 'invoicing_max_invoice_count', '{2}', {8});

            end;
            '''.format(today,
                       str(client_id),
                       currency,
                       data[params.discounting_max_giv],
                       data[params.discounting_max_single_iv],
                       data[params.discounting_max_invoice_count],
                       data[params.invoicing_max_giv],
                       data[params.invoicing_max_single_iv],
                       data[params.invoicing_max_invoice_count])
    try:
        conn.execute(query)
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError(messages.error_db_query) from e


def save_relation_limits(buyer_id, supplier_id, data, date=None, currency='KES'):
    '''
    Saves relation limits in the database
    :param buyer_id: buyer's client id
    :param supplier_id: supplier's client id
    :param data: data to update with
    :param date: date to set the changes for
    :param currency: currency of the limits
    '''
    today = times.current_date()
    if date is not None:
        today = date
    query = '''
            begin;

            update relation_limits set enddate = '{0}'
            where startdate <= '{0}' and
                enddate > '{0}' and
                buyer_clientid = {1} and
                supplier_clientid = {2};

            insert into relation_limits values
            ('{0}', '99990101', {1}, {2}, 7, 'relation_max_giv', '{3}', {4}),
            ('{0}', '99990101', {1}, {2}, 8, 'relation_max_single_iv', '{3}', {5}),
            ('{0}', '99990101', {1}, {2}, 9, 'relation_max_invoice_count', '{3}', {6});

            end;
            '''.format(today,
                       str(buyer_id),
                       str(supplier_id),
                       currency,
                       data[params.relation_max_giv],
                       data[params.relation_max_single_iv],
                       data[params.relation_max_invoice_count])
    try:
        conn.execute(query)
    except psycopg2.DatabaseError as e:
        raise psycopg2.DatabaseError from e


def close_connection():
    conn.disconnect()
