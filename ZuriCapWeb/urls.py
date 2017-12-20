"""ZuriCapWeb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
#from django.contrib import admin
from access import views
from admin import sites

access_urls = [
    url(r'^access/login$', views.login),
    url(r'^access/forgot_username$', views.forgot_username),
    url(r'^access/forgot_password$', views.forgot_password),
    url(r'^access/$', views.upload_invoice),
    url(r'^$', views.upload_invoice),
    url(r'^access/upload_invoice$', views.upload_invoice),
    url(r'^access/open_invoices$', views.open_invoices),
    url(r'^access/history$', views.history),
    url(r'^access/payments$', views.payments),
    url(r'^access/reports$', views.reports),
    url(r'^access/settings$', views.settings),
    url(r'^access/change_password$', views.change_password),
    url(r'^access/buyer$', views.set_buyer),
    url(r'^access/supplier$', views.set_supplier),
    url(r'^access/logout$', views.logout)
]

admin_urls = [
    url(r'^admin/$', sites.login),
    url(r'^admin/login$', sites.login),
    url(r'^admin/clients$', sites.clients),
    url(r'^admin/open_invoices', sites.open_invoices),
    url(r'^admin/history', sites.history),
    url(r'^admin/payments', sites.payments),
    url(r'^admin/prev_rows$', sites.prev_rows),
    url(r'^admin/next_rows$', sites.next_rows),
    url(r'^admin/buyer$', sites.set_buyer),
    url(r'^admin/supplier$', sites.set_supplier),
    url(r'^admin/add_client$', sites.add_client),
    url(r'^admin/client_profile$', sites.client_profile),
    url(r'^admin/edit_profile$', sites.edit_profile),
    url(r'^admin/client_relations$', sites.client_relations),
    url(r'^admin/edit_relations$', sites.edit_relations),
    url(r'^admin/add_relation$', sites.add_relation),
    url(r'^admin/client_limits$', sites.client_limits),
    url(r'^admin/edit_client_limits$', sites.edit_client_limits),
    url(r'^admin/save_client_limits$', sites.save_client_limits),
    url(r'^admin/edit_relation_limits$', sites.edit_relation_limits),
    url(r'^admin/save_relation_limits$', sites.save_relation_limits),
    url(r'^admin/client_users$', sites.client_users),
    url(r'^admin/client_open_invoices$', sites.client_open_invoices),
    url(r'^admin/save_financing$', sites.save_financing),
    url(r'^admin/save_invoice_repayment$', sites.save_invoice_repayment),
    url(r'^admin/client_repayment$', sites.client_repayment),
    url(r'^admin/save_client_repayment$', sites.save_client_repayment),
    url(r'^admin/client_history$', sites.client_history),
    url(r'^admin/logout$', sites.logout)
]

urlpatterns = access_urls + admin_urls
