# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.utils import translation
# ______________________________________________________________________________
#                                                                        Contrib
from filer.models import File
# ______________________________________________________________________________
#                                                                        Package
from django.test.testcases import TestCase
from filersets.tests.helpers import create_superuser, create_controlled_categories
from filersets.models import Category


class SetModelTests(TestCase):
    # TODO  Test creation of one unprocessed set
    # TODO  Test update of one already processed but unchanged set
    # TODO  Test update of one already processed and changed set
    # TODO  Test creation of multiple unprocessed sets
    # TODO  Test update of multiple already processed but unchanged sets
    # TODO  Test update of multiple already processed and changed sets
    pass


class CategoryModelTests(TestCase):

    def setUp(self):
        translation.activate('en')
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')

    def tearDown(self):
        self.client.logout()
        for f in File.objects.all():
            f.delete()
        translation.deactivate()

    def test_create_category_with_minimum_values(self):
        """
        Test creation of a single category using special characters and assert
        that values inserted into the database match configured defaults
        """
        Category.add_root(name=u'Foo üß çś —')
        result = Category.objects.all()
        cat = result[0]
        self.assertEqual(result.count(), int(1))
        self.assertEqual(cat.is_active, False)
        self.assertEqual(cat.name, u'Foo üß çś —')
        self.assertEqual(cat.description, None)
        self.assertEqual(cat.slug, u'foo-u-cs')  # TODO How to get better I18N?
        self.assertEqual(cat.slug_composed, u'foo-u-cs/')
        self.assertEqual(cat.parent, None)

    def test_update_slug_for_category_in_root_leaf(self):
        """
        Test that updating the name of a category updates `slug`and
        `slug_composed` accordingly.
        """
        Category.add_root(name=u'Foobar')
        result = Category.objects.all()
        cat = result[0]
        self.assertEqual(cat.slug, u'foobar')
        self.assertEqual(cat.slug_composed, u'foobar/')

        cat.name = u'Bazbam'
        cat.save()
        result = Category.objects.all()
        cat = result[0]
        self.assertEqual(cat.slug, u'bazbam')
        self.assertEqual(cat.slug_composed, u'bazbam/')

    def test_custom_field__get_level_compensation(self):
        """ The compensation value for different levels is correct """
        create_controlled_categories()
        root_cat = Category.get_root_nodes()[0]
        self.assertEqual(root_cat.get_level_compensation(), int(0))

        lvl1_cat = root_cat.get_last_child()
        self.assertEqual(lvl1_cat.get_level_compensation(), int(1))

        lvl2_cat = lvl1_cat.get_first_child()
        self.assertEqual(lvl2_cat.get_level_compensation(), int(2))


    # TODO  Test creation of slug_composed for a child item
    # TODO  Test creation of slug_composed for an item with parents and children
    # TODO  Test creation of slug_composed for an item with many children
    # TODO  Test creation of slug_composed with exceeding URL length