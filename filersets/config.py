# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings


def get_template_settings(overrides=None, namespace=None):
    """ Returns a dictionary with template settings

    Currently there are three layers for settings, two of them can be overridden
    by users. (but only default and global settings are currently implemented)

    Prio -1: Package defaults
    if no other settings are defined the defaults will be taken

    Prio  0: Global settings
    The global settings, usually defined in settings.py. Note that for each
    setting that is not overridden by you the default setting will be taken

    Prio +1: Method overrides
    TODO

    :param overrides: Settings that should take precedence
    :type overrides: dict
    :rtype: dict
    """

    if not overrides:
        overrides = dict()

    s_defaults = _get_filersets_defaults('FILERSETS_TEMPLATES')  # prio -1
    s_globals = _get_filersets_globals('FILERSETS_TEMPLATES')    # prio  0
    s_namespace = s_globals[namespace] if namespace in s_globals else dict()
    s_overrides = overrides                                      # prio +1

    ret = dict()
    ret.update(s_defaults)
    ret.update(s_globals)
    ret.update(s_namespace)
    ret.update(s_overrides)

    return ret


def _get_filersets_defaults(key=None):
    """ Return default settings for the given key

    :param key: string of the required key or None for all settings
    :type key: None or string
    :rtype: dict
    """

    # !!!
    # CAUTION:
    # Each time default settings are changed don't forget to update the
    # ConfigTests in filersets.tests.tests_config
    # !!!

    defaults = {
        'FILERSETS_TEMPLATES': {
            # page and page element templates
            'base': 'filersets/base.html',
            'set': 'filersets/set.html',
            'list': 'filersets/list.html',
            'list_item': 'filersets/_list_item.html',

            # templatetags
            'cat_tree_wrap': 'filersets/templatetags/_category_tree.html',
            'cat_tree_item': 'filersets/templatetags/_category_tree_item.html',
        },
    }

    if not key:
        return defaults

    if not key in defaults:
        raise KeyError

    return defaults[key]


def _get_filersets_globals(key=None):
    """ Returns filerset settings from settings module by key

    :param key: name of the setting as used in settings.py
    :type key: string
    :rtype: dict
    """
    try:
        return settings.__getattr__(key)
    except AttributeError:
        return dict()
