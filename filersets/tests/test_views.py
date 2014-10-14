# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import translation
from filer.models import File
from filersets.models import Set
from filersets.tests.helpers import (create_superuser,
                                     create_set_type,
                                     create_set)


class SetViewTests(TestCase):
    """
    Tests for the detail views of filersets.
    """
    def setUp(self):
        translation.activate('en')
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')

    def tearDown(self):
        self.client.logout()
        for f in File.objects.all():
            f.delete()
        translation.deactivate()

    def test_set_view_with_valid_set_id_200(self):
        """
        Check that we get a successful response when hitting the URL of an
        existing set.
        """
        fset = create_set(self, 'Foobar', 'My Foobar', do_categorize=True)

        response = self.client.get(
            reverse('filersets:set_by_id_view',
                    kwargs={'set_type': fset.get_set_type_slug(),
                            'set_id': fset.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fset.title)

    def test_set_view_with_invalid_set_id_404(self):
        """
        Check that we get a 404 when hitting the URL of a set that does not
        exist
        """
        set_type = create_set_type()
        id_404 = Set.objects.all().count()

        response = self.client.get(
            reverse('filersets:set_by_id_view',
                    kwargs={'set_type': set_type.slug,
                            'set_id': id_404}))

        self.assertEqual(response.status_code, 404)

    def test_set_view_with_valid_set_slug_200(self):
        """
        Check that we get a successful response when hitting the URL of an
        existing with usage of the slug parameter.
        """
        fset = create_set(self, 'Foobar', 'My Foobar', do_categorize=True)
        response = self.client.get(
            reverse('filersets:set_by_slug_view',
                    kwargs={'set_type': fset.get_set_type_slug(),
                            'set_slug': fset.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fset.title)

    def test_set_view_with_invalid_set_slug_404(self):
        """
        Check that we get a 404 when hitting the URL of a set with a slug
        parameter that does not exist
        """
        set_type = create_set_type()
        slug_404 = 'foo_-_bar_-_baz'

        response = self.client.get(
            reverse('filersets:set_by_slug_view',
                    kwargs={'set_type': set_type.slug,
                            'set_slug': slug_404}))

        self.assertEqual(response.status_code, 404)


    # TODO(sthzg) Test that set is only displayed if set type and slug match.
    # TODO(sthzg) Test that set is only displayed if set type and id match.


class ListViewTests(TestCase):
    """
    Tests for the list views of filersets.
    """
    def setUp(self):
        translation.activate('en')
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')

    def tearDown(self):
        self.client.logout()
        for f in File.objects.all():
            f.delete()
        translation.deactivate()

    def test_list_view_with_no_results_200(self):
        """ Check that we get a 200 on an empty list view """
        response = self.client.get(reverse('filersets:list_view'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_with_one_result_200(self):
        """ Check that we get a 200 on a list page with one entry """
        fset = create_set(self, 'Foobar', 'My Foobar')
        response = self.client.get(reverse('filersets:list_view'))
        self.assertEqual(response.status_code, 200)

    # TODO  Test pagination
    # TODO  Test category list views
    # TODO  Test back button behavior


class ProcessViewTests(TestCase):

    def setUp(self):
        translation.activate('en')
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')

    def tearDown(self):
        self.client.logout()
        for f in File.objects.all():
            f.delete()
        translation.deactivate()

    # TODO  Test invocation of processing with nonexisting set
    # TODO  Test invocation of processing with no privilidges
    # TODO  Test invocation of processing through admin actions
    # TODO  Test invocation of processing through ./manage.py command


class CategoryListViewTests(TestCase):
    """
    Tests for category list views for filersets.
    """
    def setUp(self):
        translation.activate('en')
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')

    def tearDown(self):
        self.client.logout()
        for f in File.objects.all():
            f.delete()
        translation.deactivate()

    def test_list_view_with_category_in_root_leaf_200(self):
        """
        Check 200 when hitting a list view with `cat_id` or `cat_slug` in
        a root leaf without siblings
        """
        fset = create_set(self, do_categorize=True)
        cat_slug = fset.category.all()[0].slug_composed
        cat_id = fset.category.all()[0].pk
        set_type_slug  = fset.get_set_type_slug()

        url_slug = reverse(
            'filersets:list_view', kwargs={'set_type': set_type_slug,
                                           'cat_slug': cat_slug})
        url_id = reverse(
            'filersets:list_view', kwargs={'set_type': set_type_slug,
                                           'cat_id': cat_id})

        response = self.client.get(url_slug)
        self.assertEqual(response.status_code, 200, "200 by slug failed")

        response = self.client.get(url_id)
        self.assertEqual(response.status_code, 200, "200 by id failed")

    def test_list_view_with_no_matching_category_404(self):
        """
        Check 404 when hitting a category list view with a non-existent category
        """
        set_type = create_set_type()

        url_slug = reverse(
            'filersets:list_view', kwargs={'set_type': set_type.slug,
                                           'cat_slug': 'foo/'})

        response = self.client.get(url_slug)
        self.assertEqual(response.status_code, 404, "404 by slug failed")

        url_id = reverse(
            'filersets:list_view', kwargs={'set_type': set_type.slug,
                                           'cat_id': 1})

        response = self.client.get(url_id)
        self.assertEqual(response.status_code, 404, "404 by id failed")

    # TODO  Test 200 for list with a category in root with one child
    # TODO  Test 200 for list with a category in root with two children
    # TODO  Test 200 for list with a category in child leaf with one ancestor
    # TODO  Test 200 for list with a category in child leaf with two ancestors
    # TODO  Test 200 for list with a category in child leaf with one child
    # TODO  Test 200 for list with a category in child leaf with two chilrdren
