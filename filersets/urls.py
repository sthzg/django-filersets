# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.conf.urls import patterns, url
from filersets import views

# TODO  Make url components configurable
# TODO  Make url components translatable

urlpatterns = patterns('',

    url(  # Show a list page ordered chronologically
          # TODO Extend list view to handle category lists
        r'^$', views.ListView.as_view(),
        name='list_view'
    ),

    url(  # Show the detail page of a set referenced by its set_id
          # TODO Make detail view back button and list position aware
        r'filerset/(?P<set_id>\d+)/$',
        views.SetView.as_view(),
        name='set_by_id_view'
    ),

    # TODO  Create view to reference detail page by slug
)