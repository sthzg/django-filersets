# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import permission_required
from filersets import views


urlpatterns = patterns('',

    url(  # Process set with given set_id
        r'^(?P<set_id>\d+)/process/$',
        permission_required('filersets.add_set', 'filersets.change_set')
        (views.ProcessSetView.as_view()),
        name='set_process_view'
    ),

)