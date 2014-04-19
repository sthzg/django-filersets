# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Python
import os
# ______________________________________________________________________________
#                                                                         Django
from django.test import TestCase
from django.test.utils import override_settings
# ______________________________________________________________________________
#                                                                        Package
from filersets.config import get_template_settings, _get_filersets_defaults

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
T_DIR = '{}/templates'.format(BASE_DIR)

class ConfigTests(TestCase):

    def test_get_default_template_settings(self):
        """ Check all default settings to exist and to be of expected type """

        t_conf = _get_filersets_defaults()
        self.assertEqual(type(t_conf), type(dict()))
        self.assertEqual(len(t_conf), int(1))
        self.assertTrue('FILERSETS_TEMPLATES' in t_conf)
        self.assertTrue('base' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('set' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('list' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('list_item' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('cat_tree_wrap' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue('cat_tree_item' in t_conf['FILERSETS_TEMPLATES'])
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['base'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['set'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['list'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['list_item'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['cat_tree_wrap'])))
        self.assertTrue(os.path.exists('{}/{}'.format(
            T_DIR, t_conf['FILERSETS_TEMPLATES']['cat_tree_item'])))

    @override_settings(
        FILERSETS_TEMPLATES={
            'base': 'overridden/base.html',
            'set': 'overridden/set.html',
            'list': 'overridden/list.html',
            'list_item': 'overridden/_list_item.html',
            'cat_tree_wrap': 'overridden/cat_tree_wrap.html',
            'cat_tree_item': 'overridden/cat_tree_item.html',
        })
    def test_override_all_default_template_by_global_settings(self):
        """
        Check that overriding all default template settings in settings.py
        reflects correctly in the package.
        """
        t_conf = get_template_settings()
        self.assertEqual(type(t_conf), type(dict()))
        self.assertEqual(len(t_conf), int(6))
        self.assertTrue('base' in t_conf)
        self.assertTrue('set' in t_conf)
        self.assertTrue('list' in t_conf)
        self.assertTrue('list_item' in t_conf)
        self.assertTrue('cat_tree_wrap' in t_conf)
        self.assertTrue('cat_tree_item' in t_conf)
        self.assertTrue('overridden' in t_conf['base'])
        self.assertTrue('overridden' in t_conf['set'])
        self.assertTrue('overridden' in t_conf['list'])
        self.assertTrue('overridden' in t_conf['list_item'])
        self.assertTrue('overridden' in t_conf['cat_tree_wrap'])
        self.assertTrue('overridden' in t_conf['cat_tree_item'])

    @override_settings(
        FILERSETS_TEMPLATES={
            'base': 'overridden/base.html',
            'set': 'overridden/set.html',
        })
    def test_override_partial_default_template_by_global_settings(self):
        t_conf = get_template_settings()
        self.assertEqual(type(t_conf), type(dict()))
        self.assertEqual(len(t_conf), int(6))
        self.assertTrue('base' in t_conf)
        self.assertTrue('set' in t_conf)
        self.assertTrue('list' in t_conf)
        self.assertTrue('list_item' in t_conf)
        self.assertTrue('overridden' in t_conf['base'])
        self.assertTrue('overridden' in t_conf['set'])
        self.assertTrue('filersets' in t_conf['list'])
        self.assertTrue('filersets' in t_conf['list_item'])

    @override_settings(
        FILERSETS_TEMPLATES={
            'list': 'global/list.html',
            'list_item': 'global/list_item.html',
            'my_namespace': {
                'list': 'namespaced/list.html',
                'list_item': 'namespaced/list_item.html'
            }
        })
    def test_override_partial_global_template_by_namespaced_settings(self):
        t_conf = get_template_settings(namespace='my_namespace')
        self.assertEqual(type(t_conf), type(dict()))
        self.assertEqual(len(t_conf), int(7))
        self.assertTrue('base' in t_conf)
        self.assertTrue('set' in t_conf)
        self.assertTrue('list' in t_conf)
        self.assertTrue('list_item' in t_conf)
        self.assertTrue('filersets' in t_conf['base'])
        self.assertTrue('filersets' in t_conf['set'])
        self.assertTrue('namespaced' in t_conf['list'])
        self.assertTrue('namespaced' in t_conf['list_item'])