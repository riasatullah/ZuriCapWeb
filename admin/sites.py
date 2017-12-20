from django.shortcuts import render, redirect
from ZuriCapWeb.backend.database import info_queries, inject_queries
from ZuriCapWeb.backend.processor import grabber, injector
from ZuriCapWeb.backend.processor.logger import Logger
from ZuriCapWeb.backend.processor.invoice import Invoice
from ZuriCapWeb.backend.processor.portfolio import Portfolio
from ZuriCapWeb.backend.processor.payment import InvoicePayment
from ZuriCapWeb.utils import times
from ZuriCapWeb.utils.string_verifier import StringVerifier
from ZuriCapWeb.variables import messages, pages, params
import psycopg2


def login(request):
    '''
    Login page for the admin site for ZuriCap Access
    :param request: Http request
    :return: HttpResponse directed to the clients page
            if login is successful; else let's the user retry to login
    '''
    if request.method == 'GET':
        context = dict()
        if params.username in request.session and request.session[params.user_type] == params.admin:
            context[params.title] = pages.title_clients
            return render(request, pages.admin_clients, context)
        else:
            context[params.title] = pages.title_login
            return render(request, pages.admin_login, context)
    elif request.method == 'POST':
        info = request.POST
        context = dict()
        try:
            username = info[params.username]
            password = info[params.password]
            id = info[params.id]

            if StringVerifier(username).is_not_empty() and\
                    StringVerifier(password).is_not_empty() and\
                    StringVerifier(id).is_not_empty():

                passport = Logger(username, password, id, admin=True)

                if passport.is_correct():
                    request.session[params.user_type] = params.admin
                    request.session[params.username] = username
                    request.session[params.user_type] = params.admin
                    return redirect(clients)
                else:
                    context[params.login_failed] = True
                    context[params.login_error] = messages.error_login_incorrect
                    return render(request, pages.admin_login, context)
            else:
                context[params.login_failed] = True
                context[params.login_error] = messages.error_login_missing
                return render(request, pages.admin_login, context)
        except Exception as e:
            raise Exception(e)


def open_invoices(request):
    '''
    Gets a web page with all open invoices
    :param request: Http request
    :return: Http response
    '''
    std_limit = 100
    std_offset = 0
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_open_invoices
        if request.method == 'GET':
            # set the number of rows to fetch
            if params.previous_page in request.session and request.session[params.previous_page] == open_invoices:
                if params.row_multiplier in request.session:
                    current_multiplier = request.session[params.row_multiplier]
            else:
                request.session[params.previous_page] = open_invoices
                current_multiplier = 1
            std_offset = (std_limit * current_multiplier) - std_limit

            data = grabber.retrieve_invoices(status=params.open_status,
                                             limit_rows=std_limit,
                                             offset=std_offset,
                                             as_dict=True)
            data = sorted(data, key=lambda k: k[params.submitted_on], reverse=True)
            context[params.data] = data
            context[params.row_multiplier] = current_multiplier
            context[params.row_count] = len(context[params.data])
            request.session[params.row_multiplier] = current_multiplier
            return render(request, pages.admin_open_invoices, context)
    else:
        return redirect(login)


def history(request):
    '''
    Gets a web page with all closed invoices
    :param request: Http request
    :return: Http response
    '''
    std_limit = 100
    std_offset = 0
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_history
        if request.method == 'GET':
            # set the number of rows to fetch
            if params.previous_page in request.session and request.session[params.previous_page] == history:
                if params.row_multiplier in request.session:
                    current_multiplier = request.session[params.row_multiplier]
            else:
                request.session[params.previous_page] = history
                current_multiplier = 1
            std_offset = (std_limit * current_multiplier) - std_limit

            data = grabber.retrieve_invoices(status=params.closed_status,
                                             limit_rows=std_limit,
                                             offset=std_offset,
                                             as_dict=True)
            data = sorted(data, key=lambda k: k[params.submitted_on], reverse=True)
            context[params.data] = data
            context[params.row_multiplier] = current_multiplier
            context[params.row_count] = len(context[params.data])
            request.session[params.row_multiplier] = current_multiplier
            return render(request, pages.admin_history, context)
    else:
        return redirect(login)


def payments(request):
    '''
    Gets the web page for payment details
    :param request: Http request
    :return: Http response
    '''
    std_limit = 100
    std_offset = 0
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_payments
        if request.method == 'GET':
            if params.previous_page in request.session and request.session[params.previous_page] == payments:
                if params.row_multiplier in request.session:
                    current_multiplier = request.session[params.row_multiplier]
            else:
                request.session[params.previous_page] = payments
                current_multiplier = 1
            std_offset = (std_limit * current_multiplier) - std_limit
            context[params.data] = grabber.present_payments(limit=std_limit,
                                                            offset=std_offset)
            request.session[params.row_multiplier] = current_multiplier
            context[params.row_multiplier] = current_multiplier
            context[params.row_count] = len(context[params.data])
            return render(request, pages.admin_payments, context)
    else:
        return redirect(login)


def clients(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_clients
        if request.method == 'GET':
            names = info_queries.client_name_search(date=times.current_date())
            context[params.data] = names
            return render(request, pages.admin_clients, context)
        elif request.method == 'POST':
            info = request.POST
            search_name = info[params.client_name]
            if search_name == '' or len(search_name) <= 1:
                search_name = None
            names = info_queries.client_name_search(date=times.current_date(),
                                                    name=search_name)
            context[params.data] = names
            table_body = ''
            for name in names:
                table_body += '''
                <form method="post" action="client_profile">
                    <input type="hidden" id="client_name" name="client_name" value ="{0}" >
                    <tr>
                        <td><button type="submit" class="btn btn-link"> {0} </button></td>
                        <td> {1} </td>
                        <td> {2} </td>
                        <td> {3} </td>
                    </tr>
                </form>
                '''.format(name[params.client_name],
                           name[params.client_type],
                           name[params.industry],
                           name[params.client_status])
            return render(request, 'scrap.html', context)
            #return render(request, pages.admin_clients, context)
        else:
            print(request)
    else:
        return login(request)


def add_client(request):
    '''
    Web page to add a new client
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_clients
        if request.method == 'GET':
            context[params.start_date] = times.current_date()
            return render(request, pages.add_client, context)
        elif request.method == 'POST':
            info = request.POST
            data = dict()
            data[params.start_date] = info[params.start_date]
            data[params.client_name] = str(info[params.client_name]).upper()
            data[params.address] = info[params.address]
            data[params.city] = info[params.city]
            data[params.client_zip] = info[params.client_zip]
            data[params.country] = info[params.country]
            data[params.registration] = info[params.registration]
            data[params.tax_pin] = info[params.tax_pin]
            data[params.office_phone] = info[params.office_phone]
            data[params.description] = info[params.description]
            data[params.client_type] = info[params.client_type]
            data[params.industry] = info[params.industry]
            data[params.client_size] = info[params.client_size]
            try:
                inject_queries.add_new_client(data)
                context[params.messages] = ['Successfully added client - ' + info[params.client_name]]
            except psycopg2.DatabaseError as e:
                context[params.has_errors] = [messages.error_client_add]
            finally:
                return render(request, pages.add_client, context)


def client_profile(request):
    '''
    Gets a web page with a client's detail
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_clients
        client_id = None

        if request.method == 'GET':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                client_name = info_queries.name_from_clientid(clientid=client_id)[int(client_id)]
                context[params.client_name] = client_name

        elif request.method == 'POST':
            info = request.POST
            client_id = info[params.client_id]

            # set the client type for this client
            request.session[params.client_type] = grabber.get_client_type(clientid=client_id)
            request.session[params.client_id] = int(client_id)

        data = grabber.present_client_profile(client_id, times.current_date())
        context.update(data)

        # set the page type
        if params.buyer not in request.session[params.client_type]:
            request.session[params.page_type] = params.supplier
        else:
            request.session[params.page_type] = params.buyer

        context[params.page_type] = request.session[params.page_type]
        context[params.edit] = 2
        if params.edit in request.session:
            context[params.edit] = request.session[params.edit]
            del request.session[params.edit]

        if request.session[params.page_type] in request.session[params.client_type]:
            request.method = 'GET'
            return render(request, pages.admin_client_profile, context)
        else:
            return render(request, pages.admin_invalid_client_type, context)
    else:
        return redirect(login)


def edit_profile(request):
    '''
    Turns on the edit mode of the client profile page and redirects to it
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        if request.method == 'GET':
            request.session[params.edit] = 1
            return redirect(client_profile)
        elif request.method == 'POST':
            context = dict()
            context[params.title] = pages.title_clients
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                client_name = info_queries.name_from_clientid(clientid=client_id)[int(client_id)]
                context[params.client_name] = client_name

                info = request.POST
                data = dict()
                data[params.client_id] = client_id
                data[params.address] = info[params.address]
                data[params.city] = info[params.city]
                data[params.client_zip] = info[params.client_zip]
                data[params.country] = info[params.country]
                data[params.registration] = info[params.registration]
                data[params.tax_pin] = info[params.tax_pin]
                data[params.office_phone] = info[params.office_phone]
                data[params.description] = info[params.description]
                data[params.client_type] = info[params.client_type]
                data[params.industry] = info[params.industry]
                data[params.client_size] = info[params.client_size]
                try:
                    inject_queries.update_client_profile(data)
                    context[params.messages] = ['Successfully updated client information']
                except psycopg2.DatabaseError as e:
                    context[params.has_errors] = [messages.error_client_edit]
                finally:
                    return render(request, pages.admin_client_profile, context)
            else:
                return redirect(client_profile)
    else:
        return redirect(login)


def client_relations(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_relations
        if params.page_type in request.session:
            context[params.page_type] = request.session[params.page_type]

        if request.method == 'GET':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                client_name = info_queries.name_from_clientid(clientid=client_id)[int(client_id)]
                context[params.client_name] = client_name

                if params.client_type not in request.session:
                    request.session[params.client_type] = grabber.get_client_type(clientid=client_id)

                if request.session[params.page_type] in request.session[params.client_type]:
                    if request.session[params.page_type] == params.buyer:
                        relations = info_queries.get_relations(buyer_id=client_id)
                    else:
                        relations = info_queries.get_relations(supplier_id=client_id)
                    for rel in relations:
                        rel[params.start_date] = times.date_to_string(rel[params.start_date])
                        rel[params.end_date] = times.date_to_string(rel[params.end_date])
                    context[params.client_relations] = relations
                    return render(request, pages.client_relations, context)
                else:
                    context[params.page_type] = request.session[params.page_type]
                    return render(request, pages.admin_invalid_client_type, context)
        elif request.method == 'POST':
            try:
                info = request.POST
                buyer_id = info[params.buyer_id]
                supplier_id = info[params.supplier_id]
                start_date = info[params.start_date]

                request.session[params.buyer_id] = buyer_id
                request.session[params.supplier_id] = supplier_id
                request.session[params.start_date] = start_date

                request.method = 'GET'
                return redirect(edit_relations)
            except psycopg2.DatabaseError as e:
                pass
    else:
        return redirect(login)


def edit_relations(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_relations
        if params.client_id in request.session:
            client_id = request.session[params.client_id]
            client_name = info_queries.name_from_clientid(clientid=client_id)[int(client_id)]
            context[params.client_name] = client_name
        if request.method == 'GET':
            if params.buyer_id in request.session and\
                            params.supplier_id in request.session and\
                            params.start_date in request.session:

                buyer_id = request.session[params.buyer_id]
                supplier_id = request.session[params.supplier_id]
                start_date = request.session[params.start_date]

                del request.session[params.buyer_id]
                del request.session[params.supplier_id]
                del request.session[params.start_date]

                relations = info_queries.get_relations(buyer_id=buyer_id,
                                                       supplier_id=supplier_id,
                                                       on_date=start_date)
                context.update(relations[0])

                all_rms = info_queries.rm_details(date=times.current_date())
                all_rms = list(all_rms.keys())
                context[params.rm_name] = all_rms

                errors = []
                if len(relations) > 1:
                    errors.append(messages.error_multiple_entries)
                if len(errors) > 0:
                    context[params.has_errors] = errors
                return render(request, pages.client_edit_relations, context)
        elif request.method == 'POST':
            info = request.POST
            buyer_id = info[params.buyer_id]
            supplier_id = info[params.supplier_id]
            buyer_name = info[params.buyer_name]
            supplier_name = info[params.supplier_name]
            buyer_fraction = float(info[params.buyer_fraction])
            supplier_fraction = float(info[params.supplier_fraction])
            buyer_aproval = info[params.buyer_approval]
            supplier_approval = info[params.supplier_approval]
            rm_name = info[params.rm_name]

            errors = []
            if buyer_fraction + supplier_fraction != 100:
                errors.append('Buyer and supplier fractions must sum up to 100')
            if len(errors) > 0:
                context[params.has_errors] = errors
            else:
                data = {params.buyer_fraction: buyer_fraction,
                        params.supplier_fraction: supplier_fraction,
                        params.buyer_approval: buyer_aproval,
                        params.supplier_approval: supplier_approval,
                        params.rm_name: rm_name}
                try:
                    inject_queries.edit_relation(buyer_id, supplier_id, data, date=times.current_date())
                except psycopg2.DatabaseError as e:
                    raise psycopg2.DatabaseError(e)
                context[params.messages] = ['Successfully updated relation details for ' +
                                            buyer_name + ' and ' + supplier_name]
            return render(request, pages.client_edit_relations, context)
    else:
        return redirect(login)


def add_relation(request):
    '''
    Web page to add a new relation
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_relations
        if request.method == 'GET':
            try:
                context[params.start_date] = times.current_date()
                all_clients = info_queries.name_from_clientid(date=times.current_date())
                context[params.client] = all_clients
                all_rms = info_queries.rm_details(date=times.current_date())
                all_rms = list(all_rms.keys())
                context[params.rm_name] = all_rms
                return render(request, pages.add_relation, context)
            except psycopg2.DatabaseError as e:
                raise psycopg2.DatabaseError(e)
            except Exception as e:
                raise Exception(e)
        elif request.method == 'POST':
            try:
                info = request.POST
                start_date = info[params.start_date]
                buyer_id = info[params.buyer]
                buyer_name = info_queries.name_from_clientid(clientid=buyer_id)[int(buyer_id)]
                supplier_id = info[params.supplier]
                supplier_name = info_queries.name_from_clientid(clientid=supplier_id)[int(supplier_id)]
                buyer_fraction = info[params.buyer_fraction]
                supplier_fraction = info[params.supplier_fraction]
                buyer_approval = int(info[params.buyer_approval])
                supplier_approval = int(info[params.supplier_approval])
                rm_name = info[params.rm_name]

                data = dict()
                data[params.start_date] = start_date
                data[params.buyer_id] = buyer_id
                data[params.buyer_name] = buyer_name
                data[params.supplier_id] = supplier_id
                data[params.supplier_name] = supplier_name
                data[params.buyer_fraction] = buyer_fraction
                data[params.supplier_fraction] = supplier_fraction
                data[params.buyer_approval] = buyer_approval
                data[params.supplier_approval] = supplier_approval
                data[params.rm_name] = rm_name

                inject_queries.add_relation(data)
                context[params.messages] = ['Successfully added relation between ' +\
                                           buyer_name + ' and ' + supplier_name]
            except psycopg2.DatabaseError as e:
                context[params.has_errors] = [messages.error_relation_add]
            return render(request, pages.add_relation, context)
    else:
        return redirect(login)


def client_limits(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_limits
        if request.method == 'GET':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                limits_clients = grabber.present_client_limits(client_id, date=times.current_date())
                if params.client_type not in request.session:
                    request.session[params.client_type] = grabber.get_client_type(clientid=client_id)

                if request.session[params.page_type] in request.session[params.client_type]:
                    if request.session[params.page_type] == params.buyer:
                        limits_relations = grabber.present_relation_limits(buyer_id=client_id,
                                                                           date=times.current_date())
                    else:
                        limits_relations = grabber.present_relation_limits(supplier_id=client_id,
                                                                           date=times.current_date())
                    context.update(limits_clients)
                    context[params.relation_limits] = limits_relations
                else:
                    context[params.page_type] = request.session[params.page_type]
                    return render(request, pages.admin_invalid_client_type, context)
            return render(request, pages.client_limits, context)
    else:
        return redirect(login)


def edit_client_limits(request):
    '''
    Sets the edit mode for client limits
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_limits
        if request.method == 'POST':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                limits_clients = grabber.present_client_limits(client_id, date=times.current_date())
                context.update(limits_clients)
                return render(request, pages.edit_client_limits, context)
            else:
                context[params.has_errors] = [messages.error_page_failed]
                return render(request, pages.client_limits, context)
    else:
        return redirect(login)


def save_client_limits(request):
    '''
    Saves a client's new limits and redirects to the client limits page
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_limits
        if request.method == 'POST':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                info = request.POST
                data = dict()
                data[params.discounting_max_giv] = info[params.discounting_max_giv]
                data[params.discounting_max_single_iv] = info[params.discounting_max_single_iv]
                data[params.discounting_max_invoice_count] = info[params.discounting_max_invoice_count]
                data[params.invoicing_max_giv] = info[params.invoicing_max_giv]
                data[params.invoicing_max_single_iv] = info[params.invoicing_max_single_iv]
                data[params.invoicing_max_invoice_count] = info[params.invoicing_max_invoice_count]
                try:
                    inject_queries.save_client_limits(client_id, data)
                except psycopg2.DatabaseError as e:
                    context[params.has_errors] = [messages.error_save_limits]
                    return render(request, pages.client_limits, context)
                except Exception as e:
                    pass
                finally:
                    context[params.messages] = [messages.msg_limits_saved]
                    return render(request, pages.client_limits, context)
    else:
        return redirect(login)


def edit_relation_limits(request):
    '''
    Sets the edit mode for relation limits
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_limits
        if request.method == 'POST':
            info = request.POST
            buyer_id = info[params.buyer_id]
            supplier_id = info[params.supplier_id]
            try:
                limits = grabber.present_relation_limits(buyer_id=buyer_id,
                                                         supplier_id=supplier_id,
                                                         date=times.current_date())
                context.update(limits[0])
            except psycopg2.DatabaseError as e:
                context[params.has_errors] = [messages.error_page_failed]
                return render(request, pages.client_limits, context)
            finally:
                return render(request, pages.edit_relation_limits, context)
    else:
        return redirect(login)


def save_relation_limits(request):
    '''
    Saves a relation's new limits and redirects to the client limits page
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_limits
        if request.method == 'POST':
            info = request.POST
            data = dict()
            buyer_id = info[params.buyer_id]
            supplier_id = info[params.supplier_id]
            data[params.relation_max_giv] = info[params.relation_max_giv]
            data[params.relation_max_single_iv] = info[params.relation_max_single_iv]
            data[params.relation_max_invoice_count] = info[params.relation_max_invoice_count]
            try:
                inject_queries.save_relation_limits(buyer_id=buyer_id,
                                                    supplier_id=supplier_id,
                                                    data=data)
            except psycopg2.DatabaseError as e:
                context[params.has_errors] = [messages.error_save_limits]
                return render(request, pages.client_limits, context)
            finally:
                context[params.messages] = [messages.msg_limits_saved]
                return render(request, pages.client_limits, context)
    else:
        return redirect(login)


def client_users(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        pass
    else:
        return redirect(login)


def client_open_invoices(request):
    std_limit = 100
    std_offset = 0
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_open_invoices
        if params.page_type in request.session:
            context[params.page_type] = request.session[params.page_type]
        if request.method == 'GET':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                client_name = info_queries.name_from_clientid(clientid=client_id)[int(client_id)]
                context[params.client_name] = client_name

                # set the number of rows to fetch
                if params.previous_page in request.session and\
                                request.session[params.previous_page] == client_open_invoices:
                    if params.row_multiplier in request.session:
                        current_multiplier = request.session[params.row_multiplier]
                else:
                    request.session[params.previous_page] = client_open_invoices
                    current_multiplier = 1
                std_offset = (std_limit * current_multiplier) - std_limit

                if request.session[params.page_type] in request.session[params.client_type]:
                    if request.session[params.page_type] == params.buyer:
                        data = grabber.retrieve_invoices(buyer_id=client_id,
                                                         status=params.open_status,
                                                         limit_rows=std_limit,
                                                         offset=std_offset,
                                                         as_dict=True)
                    else:
                        data = grabber.retrieve_invoices(supplier_id=client_id,
                                                         status=params.open_status,
                                                         limit_rows=std_limit,
                                                         offset=std_offset,
                                                         as_dict=True)
                    data = sorted(data, key=lambda k: k[params.submitted_on], reverse=True)
                    context[params.data] = data
                    context[params.row_multiplier] = current_multiplier
                    context[params.row_count] = len(context[params.data])
                    request.session[params.row_multiplier] = current_multiplier
                    return render(request, pages.client_open_invoices, context)
                else:
                    return render(request, pages.admin_invalid_client_type, context)
    else:
        return redirect(login)


def client_history(request):
    std_limit = 100
    std_offset = 0
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_open_invoices
        if params.page_type in request.session:
            context[params.page_type] = request.session[params.page_type]
        if request.method == 'GET':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]

                # set the number of rows to fetch
                if params.previous_page in request.session and request.session[params.previous_page] == client_history:
                    if params.row_multiplier in request.session:
                        current_multiplier = request.session[params.row_multiplier]
                else:
                    request.session[params.previous_page] = client_history
                    current_multiplier = 1
                std_offset = (std_limit * current_multiplier) - std_limit

                if request.session[params.page_type] in request.session[params.client_type]:
                    if request.session[params.page_type] == params.buyer:
                        data = grabber.retrieve_invoices(buyer_id=client_id,
                                                         status=params.closed_status,
                                                         limit_rows=std_limit,
                                                         offset=std_offset,
                                                         as_dict=True)
                    else:
                        data = grabber.retrieve_invoices(supplier_id=client_id,
                                                         status=params.closed_status,
                                                         limit_rows=std_limit,
                                                         offset=std_offset,
                                                         as_dict=True)
                    data = sorted(data, key=lambda k: k[params.submitted_on], reverse=True)
                    context[params.data] = data
                    context[params.row_multiplier] = current_multiplier
                    context[params.row_count] = len(context[params.data])
                    request.session[params.row_multiplier] = current_multiplier
                    return render(request, pages.client_history, context)
                else:
                    return render(request, pages.admin_invalid_client_type, context)
    else:
        return redirect(login)


def upload_invoice(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.username] = request.session[params.username]
        context[params.title] = pages.title_upload_invoice
        if request.method == 'GET':
            context[params.client_relations] =\
                grabber.client_relations(request.session[params.username],
                                         'buyer')
            return render(request, pages.upload_invoice, context)
        elif request.method == 'POST':
            context[params.client_relations] = grabber.client_relations(request.session[params.username], 'buyer')

            info = request.POST
            client_id = info[params.client]
            financing_product_id = info[params.financing_product]
            invoice_date = info[params.invoice_date]
            description = info[params.description]
            amount = info[params.amount]

            errors = []
            if not StringVerifier(invoice_date).valid_date():
                errors.append(messages.error_invalid_date)
            if not StringVerifier(amount).valid_amount():
                errors.append(messages.error_invoice_amount)
            if len(description) > 140:
                errors.append(messages.error_invoice_description)

            if len(errors) > 0:
                context[params.has_errors] = errors
            else:
                output = injector.upload_invoice(times.current_date(),
                                        username, 'buyer',
                                        invoice_date, client_id,
                                        int(financing_product_id),
                                        description, amount)
                if output == 0:
                    context[params.messages] = [messages.msg_invoice_success]
                else:
                    context[params.has_errors] = output
            return render(request, pages.upload_invoice, context)
    else:
        return redirect(login)


def save_financing(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_open_invoices
        if request.method == 'POST':
            info = request.POST
            invoice_id = info[params.financing_invoice_id]
            paid_on = info[params.financing_date]
            amount = info[params.financed_amount]
            fees = info[params.financing_transaction_cost]
            payment_type = info[params.financing_payment_type]
            notes = info[params.financing_notes]

            invoice = Invoice.from_invoice_id(invoice_id)
            portfolio = Portfolio([invoice])
            payment = InvoicePayment(portfolio=portfolio,
                                     amount=amount,
                                     fees=fees,
                                     payment_date=paid_on,
                                     payment_method=payment_type,
                                     updated_by=request.session[params.username],
                                     notes=notes)
            try:
                payment.make()
            except TypeError as e:
                raise TypeError(e) from e
            except ValueError as e:
                context[params.has_errors] = [e]
                return render(request, pages.client_open_invoices, context)
            except psycopg2.DatabaseError as e:
                context[params.has_errors] = [messages.error_book_financing]
            except Exception as e:
                pass
            finally:
                context[params.messages] = [messages.msg_payment_booked]
                return render(request, pages.client_open_invoices, context)
    else:
        return redirect(login)


def save_invoice_repayment(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_open_invoices
        if request.method == 'POST':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]

                info = request.POST
                invoice_id = int(info[params.repayment_invoice_id])
                paid_on = info[params.repayment_date]
                amount = info[params.repaid_amount]
                fees = info[params.repayment_transaction_cost]
                payment_type = info[params.repayment_payment_type]
                notes = info[params.repayment_notes]

                invoice = Invoice.from_invoice_id(invoice_id)
                portfolio = Portfolio([invoice])
                payment = InvoicePayment(portfolio=portfolio,
                                         amount=amount,
                                         fees=fees,
                                         payment_date=paid_on,
                                         payment_method=payment_type,
                                         updated_by=request.session[params.username],
                                         paid_by=client_id,
                                         notes=notes)
                try:
                    payment.receive()
                except TypeError as e:
                    raise TypeError(e) from e
                except ValueError as e:
                    context[params.has_errors] = [e]
                    return render(request, pages.client_open_invoices, context)
                except psycopg2.DatabaseError as e:
                    context[params.has_errors] = [messages.error_book_financing]
                except Exception as e:
                    pass
                finally:
                    context[params.messages] = [messages.msg_payment_booked]
                    return render(request, pages.client_open_invoices, context)
    else:
        return redirect(login)


def client_repayment(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_repayment
        if request.method == 'GET':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]
                client_name = info_queries.name_from_clientid(clientid=client_id)[int(client_id)]
                context[params.client_name] = client_name
                return render(request, pages.client_repayment, context)
    else:
        return redirect(login)


def save_client_repayment(request):
    if params.username in request.session and request.session[params.user_type] == params.admin:
        context = dict()
        context[params.title] = pages.title_repayment
        if request.method == 'POST':
            if params.client_id in request.session:
                client_id = request.session[params.client_id]

                info = request.POST
                paid_on = info[params.repayment_date]
                amount = float(info[params.repaid_amount])
                fees = float(info[params.repayment_transaction_cost])
                payment_type = info[params.repayment_payment_type]
                notes = info[params.repayment_notes]

                if request.session[params.page_type] in request.session[params.client_type]:
                    if request.session[params.page_type] == params.buyer:
                        invoices = grabber.retrieve_invoices(buyer_id=client_id,
                                                             status=params.open_status)
                    else:
                        invoices = grabber.retrieve_invoices(supplier_id=client_id,
                                                             status=params.open_status)
                    portfolio = Portfolio(invoices)
                    payment = InvoicePayment(portfolio=portfolio,
                                             amount=amount,
                                             fees=fees,
                                             payment_date=paid_on,
                                             payment_method=payment_type,
                                             updated_by=request.session[params.username],
                                             paid_by=client_id,
                                             notes=notes)
                    try:
                        payment.receive()
                        context[params.messages] = [messages.msg_payment_booked]
                        return render(request, pages.client_repayment, context)
                    except TypeError as e:
                        raise TypeError(e) from e
                    except ValueError as e:
                        context[params.has_errors] = [e]
                        return render(request, pages.client_open_invoices, context)
                    except psycopg2.DatabaseError as e:
                        raise Exception(e) from e
                        context[params.has_errors] = [messages.error_book_repayment]
                        return render(request, pages.client_open_invoices, context)
                    except Exception as e:
                        raise Exception(e)
    else:
        return redirect(login)


def set_buyer(request):
    '''
    Allows an user to switch the client type to buyer
    :param request: Http request
    :return: sets client type to buyer and redirects
            to the upload invoice page
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        if request.method == 'GET':
            request.session[params.page_type] = params.buyer
            return redirect(client_profile)
    else:
        return redirect(login)


def set_supplier(request):
    '''
    Allows an user to switch the client type to supplier
    :param request: Http request
    :return: sets client type to supplier and redirects
            to the upload invoice page
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        if request.method == 'GET':
            request.session[params.page_type] = params.supplier
            return redirect(client_profile)
    else:
        return redirect(login)


def prev_rows(request):
    '''
    This is an intermediary page that helps to get previous rows.
    This is used in conjunction with pages that display limited rows of data.
    :param request: Http request
    :return: redirects to a the previous page stored in session
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        if request.method == 'GET':
            if params.row_multiplier in request.session:
                current_multiplier = request.session[params.row_multiplier]
                if current_multiplier > 1:
                    request.session[params.row_multiplier] = current_multiplier - 1
            return redirect(request.session[params.previous_page])
    else:
        return redirect(login)


def next_rows(request):
    '''
    This is an intermediary page that helps to get next rows.
    This is used in conjunction with pages that display limited rows of data.
    :param request: Http request
    :return: redirects to a the previous page stored in session
    '''
    if params.username in request.session and request.session[params.user_type] == params.admin:
        if request.method == 'GET':
            if params.row_multiplier in request.session:
                current_multiplier = request.session[params.row_multiplier]
                request.session[params.row_multiplier] = current_multiplier + 1
            return redirect(request.session[params.previous_page])
    else:
        return redirect(login)


def logout(request):
    if params.username in request.session:
        del request.session[params.username]
    if params.user_type in request.session:
        del request.session[params.user_type]
    if params.client_type in request.session:
        del request.session[params.client_type]
    return redirect(login)
