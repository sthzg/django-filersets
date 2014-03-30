# -*- coding: utf-8 -*-
"""
Taken from a code snippet in a post on:
http://python.6.x6.nabble.com/INSTALLED-APPS-from-a-template-td198137.html
"""
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def installed(value):
    """ Returns whether passed APP is in INSTALLED_APPS """
    apps = settings.INSTALLED_APPS
    if "." in value:
        for app in apps:
            if app == value:
                return True
    else:
        for app in apps:
            fields = app.split(".")
            if fields[-1] == value:
                return True
    return False