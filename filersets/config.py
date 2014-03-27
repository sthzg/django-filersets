# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings


def get_template_settings(overrides=None):
    """ Returns a dictionary with template settings

    Currently there are three layers for settings, two of them can be overridden
    by users. (only global Settings are currently implemented)

    Prio -1: Package defaults
    if no other settings are defined the defaults will be taken

    Prio  0: Global settings
    The global settings, usually defined in settings.py

    Prio +1: Method overrides
    TODO

    :param overrides: Settings that should take precedence
    :type overrides: dict
    :rtype: dict
    """

    if not overrides:
        overrides = dict()

    s_defaults = get_filersets_defaults('FILERSETS_TEMPLATES')  # prio -1
    s_globals = get_filersets_globals('FILERSETS_TEMPLATES')    # prio  0
    s_overrides = overrides                                     # prio +1

    ret = dict()
    ret.update(s_defaults)
    ret.update(s_globals)
    ret.update(s_overrides)

    return ret


def get_filersets_defaults(key=None):
    """ Return default settings for the given key

    :param key: string of the required key or None for all settings
    :type key: None or string
    :rtype: dict
    """

    defaults = {
        'FILERSETS_TEMPLATES': {
            'base': 'filersets/base.html',
            'set': 'filersets/set.html',
            'list': 'filersets/list.html',
            'list_item': 'filersets/_list_item.html',
        },
    }

    if not key:
        return defaults

    if not key in defaults:
        raise KeyError

    return defaults[key]


def get_filersets_globals(key=None):
    """ Returns filerset settings from settings module by key

    :param key: name of the setting as used in settings.py
    :type key: string
    :rtype: dict
    """
    try:
        return settings.__getattr__(key)
    except AttributeError:
        return dict()