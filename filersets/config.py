# -*- coding: utf-8 -*-
from __future__ import absolute_import
import collections
import copy
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


def get_filersets_conf():
    """Returns filersets config dictionary or an empty dict."""
    try:
        conf = settings.FILERSETS_CONF
    except AttributeError:
        conf = dict()

    return conf


def get_template_settings(overrides=None, template_conf=None):
    """Returns a dictionary with template settings.

    Currently there are three layers for settings, two of them can be overridden
    by users. (but only default and global settings are currently implemented)

    Prio -1: Package defaults
    if no other settings are defined the defaults will be taken

    Prio  0: Global settings
    The global settings, usually defined in settings.py. Note that for each
    setting that is not overridden by you the default setting will be taken

    Prio +1: Method overrides
    TODO

    :param overrides: Settings that should take precedence.
    :type overrides: dict
    :param template_conf: String name of a template_conf to be returned.
    :type template_conf: string
    :rtype: dict
    """

    if not overrides:
        overrides = dict()

    s_defaults = _get_filersets_defaults('FILERSETS_TEMPLATES')  # prio -1
    s_globals = _get_filersets_globals('FILERSETS_TEMPLATES')    # prio  0
    s_overrides = overrides                                      # prio +1

    ret = dict()
    ret.update(s_defaults)
    ret = update(s_defaults, s_globals)
    ret = update(ret, s_overrides)

    # Iterate through all non-default settings and fill up settings that
    # might not be overridden w/ values from default.
    for key in ret.keys():
        if key == 'default':
            continue

        defaults_copy = copy.deepcopy(ret['default'])
        ret[key] = update(defaults_copy, ret[key])

    if template_conf:
        return ret[template_conf]
    else:
        return ret


def _get_filersets_defaults(key=None):
    """Returns default settings for the given key.

    :param key: string of the required key or None for all settings
    :type key: None or string
    :rtype: dict
    """
    # !!!
    # Each time default settings are changed don't forget to update the
    # ConfigTests in filersets.tests.tests_config
    defaults = {
        'FILERSETS_TEMPLATES': {
            'default': {
                'display_name': _('default'),
                'base': 'filersets/base.html',
                'set': 'filersets/set.html',
                'list': 'filersets/list.html',
                'list_item': 'filersets/_list_item.html',
                'set_categories': 'filersets/templatetags/_set_categories.html',
                'equalheightcols': 'filersets/templatetags/_equal_height_cols_row.html',
                'cat_tree_wrap': 'filersets/templatetags/_category_tree.html',
                'cat_tree_item': 'filersets/templatetags/_category_tree_item.html'}},}

    if not key:
        return defaults

    if not key in defaults:
        raise KeyError

    return defaults[key]


def _get_filersets_globals(key=None):
    """Returns filerset settings from settings module by key.

    :param key: name of the setting as used in settings.py
    :type key: string
    :rtype: dict
    """
    try:
        return settings.__getattr__(key)
    except AttributeError:
        return dict()


# Thanks to Alex Martelli @ http://stackoverflow.com/a/3233356/870769.
def update(d, u):
    """Updates a dictionary recursively."""
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
