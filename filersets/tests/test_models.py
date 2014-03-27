# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.utils import translation
from django.test.testcases import TestCase
from filersets.tests.helpers import create_superuser
from filer.models import File
from filersets.models import Set, Item, Category


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
        category = Category(name=u'Foo üß çś —')
        category.save()
        result = Category.objects.all()
        cat = result[0]
        self.assertEqual(result.count(), int(1))
        self.assertEqual(cat.is_active, False)
        self.assertEqual(cat.name, u'Foo üß çś —')
        self.assertEqual(cat.description, None)
        self.assertEqual(cat.slug, u'foo-u-cs')  # TODO How to get better I18N?
        self.assertEqual(cat.slug_composed, u'foo-u-cs/')
        self.assertEqual(cat.parent, None)
        self.assertEqual(cat.order, int(0))

    def test_update_slug_for_category_in_root_leaf(self):
        """
        Test that updating the name of a category updates `slug`and
        `slug_composed` accordingly.
        """
        category = Category(name=u'Foobar')
        category.save()
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


    # TODO  Test creation of slug_composed for a child item
    # TODO  Test creation of slug_composed for an item with parents and children
    # TODO  Test creation of slug_composed for an item with many children
    # TODO  Test creation of slug_composed with exceeding URL length