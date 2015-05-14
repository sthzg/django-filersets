# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import patterns, url
from filersets import views

# TODO  Make url components configurable
# TODO  Make url components translatable

urlpatterns = patterns(
    '',
    url(                                                                     # /
        r'^$',
        views.ListView.as_view(),
        name='list_view'
    ),

    url(                                                           # /:set_type/
        r'^(?P<set_type>[\w-]+)/$',
        views.ListView.as_view(),
        name='list_view_by_settype'
    ),

    url(                                          # /:set_type/category/:cat_id/
        r'^(?P<set_type>[\w-]+)/category/(?P<cat_id>\d+)/$',
        views.ListView.as_view(),
        name='list_view'
    ),

    url(                                        # /:set_type/category/:cat_slug/
        r'^(?P<set_type>[\w-]+)/category/(?P<cat_slug>[\w\-/]+)/$',
        views.ListView.as_view(),
        name='list_view'
    ),

    url(                                                         # /set/:set_id/
        r'^(?P<set_type>[\w-]+)/set/(?P<set_id>\d+)/$',
        views.SetView.as_view(),
        name='set_by_id_view'
    ),

    url(                                                       # /set/:set_slug/
        r'^(?P<set_type>[\w-]+)/set/(?P<set_slug>[\w-]+)/$',
        views.SetView.as_view(),
        name='set_by_slug_view'
    ),

    url(                                             # /set/:set_slug/:media_id/
        r'^(?P<set_type>[\w-]+)/set/(?P<set_slug>[\w-]+)/(?P<media_id>\d+)/$',
        views.MediaView.as_view(),
        name='media_by_id'
    ),
                                                       # /partials/categorymenu/
    url(
        r'^partials/categorymenu/$',
        views.CategoryMenuPartial.as_view(),
        name='partial_categorymenu'
    ),
)