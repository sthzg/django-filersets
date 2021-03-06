# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import patterns, url
from filersets import views

# TODO  Make url components configurable
# TODO  Make url components translatable

urlpatterns = patterns('',

    # Show a list page ordered chronologically
    url(r'^$', views.ListView.as_view(), name='list_view'),

    # Show a list of sets belonging to a given set type
    url(r'^(?P<set_type>[\w-]+)/$', views.ListView.as_view(), name='list_view_by_settype'),

    # Show a category list page referenced by its id
    url(r'^(?P<set_type>[\w-]+)/category/(?P<cat_id>\d+)/$', views.ListView.as_view(), name='list_view'),

    # Show a category list page referenced by its slug
    url(r'^(?P<set_type>[\w-]+)/category/(?P<cat_slug>[\w\-/]+)$', views.ListView.as_view(), name='list_view'),

    # Show the detail page of a set referenced by its set_id
    url( r'^(?P<set_type>[\w-]+)/set/(?P<set_id>\d+)/$', views.SetView.as_view(), name='set_by_id_view'),

    # Show the detail page of a set referenced by its slug
    url(r'^(?P<set_type>[\w-]+)/set/(?P<set_slug>[\w-]+)/$', views.SetView.as_view(), name='set_by_slug_view'),

    # Partials
    # Category tree
    url(r'^partials/categorymenu/$', views.CategoryMenuPartial.as_view(), name='partial_categorymenu'),

)