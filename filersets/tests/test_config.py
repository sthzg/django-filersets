# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from django.test import TestCase
from django.test.utils import override_settings
from filersets.config import get_template_settings, get_filersets_defaults

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
T_DIR = '{}/templates'.format(BASE_DIR)

class ConfigTests(TestCase):

    def test_get_default_template_settings(self):
        """ Check all default settings to exist and to be of expected type """

        t_conf = get_filersets_defaults()
        self.assertEqual(type(t_conf), type(dict()))
        self.assertEqual(len(t_conf), int(1))
        self.assertTrue('FILERSETS_TEMPLATES' in t_conf)
        self.assertTrue('base' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('set' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('list' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('list_item' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['base'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['set'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['list'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['list_item'])))

    @override_settings(
        FILERSETS_TEMPLATES={
            'base': 'overridden/base.html',
            'set': 'overridden/set.html',
            'list': 'overridden/list.html',
            'list_item': 'overridden/_list_item.html',
        })
    def test_override_all_default_template_by_global_settings(self):
        """
        Check that overriding all default template settings in settings.py
        reflects correctly in the package.
        """
        t_conf = get_template_settings()
        self.assertEqual(type(t_conf), type(dict()))
        self.assertEqual(len(t_conf), int(4))
        self.assertTrue('base' in t_conf)
        self.assertTrue('set' in t_conf)
        self.assertTrue('list' in t_conf)
        self.assertTrue('list_item' in t_conf)
        self.assertTrue('overridden' in t_conf['base'])
        self.assertTrue('overridden' in t_conf['set'])
        self.assertTrue('overridden' in t_conf['list'])
        self.assertTrue('overridden' in t_conf['list_item'])

    @override_settings(
        FILERSETS_TEMPLATES={
            'base': 'overridden/base.html',
            'set': 'overridden/set.html',
        })
    def test_override_partial_default_template_by_global_settings(self):
        t_conf = get_template_settings()
        self.assertEqual(type(t_conf), type(dict()))
        self.assertEqual(len(t_conf), int(4))
        self.assertTrue('base' in t_conf)
        self.assertTrue('set' in t_conf)
        self.assertTrue('list' in t_conf)
        self.assertTrue('list_item' in t_conf)
        self.assertTrue('overridden' in t_conf['base'])
        self.assertTrue('overridden' in t_conf['set'])
        self.assertTrue('filersets' in t_conf['list'])
        self.assertTrue('filersets' in t_conf['list_item'])