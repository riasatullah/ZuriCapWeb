from django.shortcuts import render, redirect
from ZuriCapWeb.backend.processor import grabber, injector
from ZuriCapWeb.backend.database import info_queries
from ZuriCapWeb.backend.processor.logger import Logger
from ZuriCapWeb.utils.string_verifier import StringVerifier
from ZuriCapWeb.utils import times
from ZuriCapWeb.variables import messages, pages, params
import traceback


def login(request):
    '''
    This page allows the user to login to ZuriCap Access
    :param request: HTTP request
    :return: HTTP response with the login page if successful;
            else let's the user retry
    '''
    if request.method == 'GET':
        context = dict()
        if params.username in request.session and request.session[params.user_type] == params.client:
            context[params.title] = pages.title_upload_invoice
            return render(request, pages.upload_invoice, context)

        context[params.title] = pages.title_login
        return render(request, pages.login, context)
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

                passport = Logger(username, password, id)
                if passport.is_correct():
                    request.session[params.username] = username
                    request.session[params.user_type] = params.client

                    # set the client type for this client if not defined already
                    if params.client_type not in request.session:
                        request.session[params.client_type] = grabber.get_client_type(username=username)

                    # set the page type if it is not already defined
                    if params.page_type not in request.session:
                        if params.buyer not in request.session[params.client_type]:
                            request.session[params.page_type] = params.supplier
                        else:
                            request.session[params.page_type] = params.buyer

                    context[params.title] = pages.title_upload_invoice
                    context[params.username] = username
                    context[params.page_type] = request.session[params.page_type]

                    if request.session[params.page_type] in request.session[params.client_type]:
                        context[params.client_relations] = grabber.client_relations(request.session[params.username],
                                                                                    request.session[params.page_type])
                        request.method = 'GET'
                        return redirect(upload_invoice)
                    else:
                        return render(request, pages.invalid_client_type, context)
                else:
                    context[params.title] = pages.title_login
                    context[params.login_failed] = True
                    context[params.login_error] = messages.error_login_incorrect
                    return render(request, pages.login, context)
            else:
                context[params.login_failed] = True
                context[params.login_error] = messages.error_login_missing
                return render(request, pages.login, context)
        except Exception as e:
            raise Exception(e)
            #return error(request)


def forgot_username(request):
    context = dict()
    context[params.title] = pages.title_forgot_credentials
    context[params.credential_type] = 'username'
    if request.method == 'GET':
        info = request.POST
        return render(request, pages.forgot_credentials, context)
    elif request.method == 'POST':
        context[params.request_submitted] = True
        return render(request, pages.forgot_credentials, context)


def forgot_password(request):
    context = dict()
    context[params.title] = pages.title_forgot_credentials
    context[params.credential_type] = 'password'
    if request.method == 'GET':
        info = request.POST
        return render(request, pages.forgot_credentials, context)
    elif request.method == 'POST':
        context[params.request_submitted] = True
        return render(request, pages.forgot_credentials, context)


def set_buyer(request):
    '''
    Allows an user to switch the client type to buyer
    :param request: Http request
    :return: sets client type to buyer and redirects
            to the upload invoice page
    '''
    if params.username in request.session and request.session[params.user_type] == params.client:
        if request.method == 'GET':
            request.session[params.page_type] = params.buyer
            return redirect(upload_invoice)
    else:
        return redirect(login)


def set_supplier(request):
    '''
    Allows an user to switch the client type to supplier
    :param request: Http request
    :return: sets client type to supplier and redirects
            to the upload invoice page
    '''
    if params.username in request.session and request.session[params.user_type] == params.client:
        if request.method == 'GET':
            request.session[params.page_type] = params.supplier
            return redirect(upload_invoice)
    else:
        return redirect(login)


def upload_invoice(request):
    '''
    This page allows users to upload invoices
    :param request: Http request
    :return: GET --> retrieves page to upload invoice
             POST --> uploads the invoice to the database
    '''
    if params.username in request.session and request.session[params.user_type] == params.client:
        context = dict()
        context[params.username] = request.session[params.username]
        context[params.title] = pages.title_upload_invoice

        if params.page_type in request.session:
            context[params.page_type] = request.session[params.page_type]
        else:
            return redirect(login)

        if request.method == 'GET':
            if request.session[params.page_type] in request.session[params.client_type]:
                context[params.client_relations] = grabber.client_relations(request.session[params.username],
                                                                            request.session[params.page_type])
                request.method = 'GET'
                return render(request, pages.upload_invoice, context)
            else:
                return render(request, pages.invalid_client_type, context)
        elif request.method == 'POST':
            context[params.client_relations] = grabber.client_relations(request.session[params.username],
                                                                        request.session[params.page_type])
            info = request.POST
            buyer_id = info_queries.clientid_from_username(request.session[params.username])
            supplier_id = info[params.client]
            if request.session[params.page_type] == params.supplier:
                temp_id = buyer_id
                buyer_id = supplier_id
                supplier_id = temp_id

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
                                                 request.session[params.username],
                                                 buyer_id, supplier_id,
                                                 invoice_date, int(financing_product_id),
                                                 description, amount)
                if output == 0:
                    context[params.messages] = [messages.msg_invoice_success]
                else:
                    context[params.has_errors] = output
            return render(request, pages.upload_invoice, context)
    else:
        return redirect(login)


def open_invoices(request):
    '''
    Renders a web page containing details of all open invoices
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.client:
        if request.method == 'GET':
            context = dict()
            context[params.username] = request.session[params.username]
            context[params.title] = pages.title_open_invoices
            context[params.page_type] = request.session[params.page_type]
            client_id = grabber.clientid_from_username(request.session[params.username])
            if request.session[params.page_type] in request.session[params.client_type]:
                if request.session[params.page_type] == params.buyer:
                    data = grabber.retrieve_invoices(buyer_id=client_id,
                                                     status=params.open_status,
                                                     as_dict=True)
                else:
                    data = grabber.retrieve_invoices(supplier_id=client_id,
                                                     status=params.open_status,
                                                     as_dict=True)
                data = sorted(data, key=lambda k: k[params.submitted_on])
                context[params.data] = data
                return render(request, pages.open_invoices, context)
            else:
                return render(request, pages.invalid_client_type, context)
    else:
        return redirect(login)


def history(request):
    '''
    Renders web page containing deails of all closed invoices
    :param request: Http request
    :return: Http response
    '''
    if params.username in request.session and request.session[params.user_type] == params.client:
        if request.method == 'GET':
            context = dict()
            context[params.username] = request.session[params.username]
            context[params.title] = pages.title_history
            context[params.page_type] = request.session[params.page_type]
            client_id = grabber.clientid_from_username(request.session[params.username])
            if request.session[params.page_type] in request.session[params.client_type]:
                if request.session[params.page_type] == params.buyer:
                    data = grabber.retrieve_invoices(buyer_id=client_id,
                                                     status=params.closed_status,
                                                     as_dict=True)
                else:
                    data = grabber.retrieve_invoices(supplier_id=client_id,
                                                     status=params.closed_status,
                                                     as_dict=True)
                data = sorted(data, key=lambda k: k[params.submitted_on], reverse=True)
                context[params.data] = data
                return render(request, pages.history, context)
            else:
                return render(request, pages.invalid_client_type, context)
    else:
        return redirect(login)


def payments(request):
    if params.username in request.session and request.session[params.user_type] == params.client:
        if request.method == 'GET':
            context = dict()
            context[params.username] = request.session[params.username]
            context[params.title] = pages.title_payments
            context[params.page_type] = request.session[params.page_type]
            if request.session[params.page_type] in request.session[params.client_type]:
                context[params.data] = grabber.payments(request.session[params.username],
                                                        request.session[params.page_type])
                return render(request, pages.payments, context)
            else:
                return render(request, pages.invalid_client_type, context)
    else:
        return redirect(login)


def reports(request):
    if params.username in request.session and request.session[params.user_type] == params.client:
        context = dict()
        context[params.username] = request.session[params.username]
        context[params.title] = pages.title_reports
        context[params.page_type] = request.session[params.page_type]
        if request.method == 'GET' or request.method == 'POST':
            if request.method == 'POST':
                info = request.POST
                report_type = int(info[params.report_type])
                period = int(info[params.timeline])
            else:
                report_type = 1
                period = 60
            if request.session[params.page_type] in request.session[params.client_type]:
                chart_type, labels, values = grabber.get_reports(report_type,
                                                                 client_type=request.session[params.page_type],
                                                                 username=request.session[params.username],
                                                                 timeline=period)
                context[params.chart_type] = chart_type
                context[params.labels] = labels
                context[params.values] = values
                return render(request, pages.reports, context)
            else:
                return render(request, pages.invalid_client_type, context)
    else:
        return redirect(login)


def settings(request):
    if params.username in request.session and request.session[params.user_type] == params.client:
        if request.method == 'GET':
            try:
                context = dict()
                context[params.username] = request.session[params.username]
                context[params.title] = pages.title_settings
                context[params.page_type] = request.session[params.page_type]
                context[params.data] = grabber.user_info(request.session[params.username])
                return render(request, pages.settings, context)
            except Exception as e:
                raise Exception(e)
    else:
        return redirect(login)


def change_password(request):
    if params.username in request.session and request.session[params.user_type] == params.client:
        if request.method == 'GET':
            context = dict()
            context[params.username] = request.session[params.username]
            context[params.title] = pages.title_settings
            return render(request, pages.change_password, context)
        elif request.method == 'POST':
            context = dict()
            info = request.POST
            new_pwd = info[params.new_password]
            confirm_pwd = info[params.confirm_password]
            errors = []
            if len(new_pwd) != len(confirm_pwd) and\
                    not isinstance(confirm_pwd, type(new_pwd)) and new_pwd != confirm_pwd:
                errors.append(messages.error_password_mismatch)
            if not Logger.is_valid(new_pwd):
                errors.append(messages.error_password_invalid)

            if len(errors) > 0:
                context[params.has_errors] = errors
                return render(request, pages.change_password, context)
            else:
                try:
                    injector.update_password(request.session[params.username],
                                             info[params.new_password])
                    context[params.messages] = [messages.msg_password_updated]
                    return render(request, pages.settings, context)
                except Exception as e:
                    raise Exception(e)
    else:
        return redirect(login)


def logout(request):
    '''
    Ends the session and logs out the user
    :param request: HTTP request
    :return: directs the user to the login page
    '''
    if params.username in request.session and request.session[params.user_type] == params.client:
        del request.session[params.username]
        del request.session[params.user_type]
    return redirect(login)


def error(request):
    if params.username in request.session and request.session[params.user_type] == params.client:
        del request.session[params.username]
        del request.session[params.user_type]
        if params.page_type in request.session:
            del request.session[params.page_type]
    return render(request, pages.error_404)
