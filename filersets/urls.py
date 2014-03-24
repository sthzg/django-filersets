# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import permission_required
from filersets import views

# TODO  Make url components configurable
# TODO  Make url components translatable

urlpatterns = patterns('',

    url(  # Show a list page ordered chronologically
        r'^$', views.ListView.as_view(),
        name='list_view'
    ),

    url( # Show a category list page referenced by its id
        r'^category/(?P<cat_id>\d+)/$',
        views.ListView.as_view(),
        name='list_view'
    ),

    url( # Show a category list page referenced by its slug
        r'^category/(?P<cat_slug>.+?)/$',
        views.ListView.as_view(),
        name='list_view'
    ),

    url(  # Show the detail page of a set referenced by its set_id
          # TODO Make detail view back button and list position aware
        r'^filerset/(?P<set_id>\d+)/$',
        views.SetView.as_view(),
        name='set_by_id_view'
    ),

    url(  # Show the detail page of a set referenced by its slug
        r'^filerset/(?P<set_slug>[-\w]+)/$',
        views.SetView.as_view(),
        name='set_by_slug_view'
    ),
)