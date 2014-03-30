# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required, permission_required
# ______________________________________________________________________________
#                                                                        Package
from filersets import views


urlpatterns = patterns('',

    url(  # Process set with given set_id
        r'^(?P<set_id>\d+)/process/$',
        permission_required('filersets.can_add', 'filersets.can_edit')
        (views.ProcessSetView.as_view()),
        name='set_process_view'
    ),

    # TODO  Create view to reference detail page by slug

)