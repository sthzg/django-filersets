# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
import os
from django.core.urlresolvers import reverse
# from django.forms.models import modelform_factory
from django.http.response import Http404
from django.test import TestCase
# from django.test.client import Client
# from django.test.utils import setup_test_environment
from django.core.files import File as DjangoFile
from django.utils import translation
from django.utils.timezone import now
from filer.models import File, Image, Folder
from filersets.models import Set, Category
from filersets.tests.helpers import create_superuser

# TODO  Testing boilerplate for Django CMS should be handled by another class
#       https://github.com/divio/django-cms/blob/develop/cms/tests/apphooks.py
#       As long as this is not ready (low priority) the tests will explicitly
#       use settings without CMS installed


def create_category(name='Foo', parent=None, is_active=False,
                    description='', order=int(0)):
    """
    Creates a single category and returns its object instance

    :param name: name of the category to be created
    :param parent: parent category (mptt tree)
    :param is_active: flag to set is_active on the model
    :param description: description to set in the model
    :param order: order for item in the mptt tree
    """
    category = Category(
        is_active=is_active,
        name=name,
        description=description,
        parent=parent,
        order=order)

    category.save()
    return category


def create_set(self, filer_root=None, filerdir_name='Filerset Tests',
               set_name='Filerset Tests', media_types=None,
               do_categorize=False, category_config=None):
    """
    Creates a set with the given `set_name` and uploads all assets of given
    `media_types` to the filer test directory.

    In order to create this set we need to create dependencies in filer

    1.  Create filer directories: `/Filersets Tests/<filerdir_name>/'
    2.  Upload media to the newly created directory

    TODO   category_config

    :param filer_root: the root folder for our operations in filer
    :param filerdir_name: the name of the directory in filer that is created
    :param set_name: the name of the set to be creted in the test
    :param media_types: a list of configurable file types to add to the set
    :param do_categorize: flag whether to assign the set to a category or not
    :param category_config: config-object to specify structure of categories
    """
    if not media_types:
        media_types = [{'all'}]

    category = None
    if do_categorize:
        if category_config is None:
            category = create_category()

    folder_root = Folder(name='Filerset Tests', parent=None)
    folder_root.save()
    folder_set = Folder(name=filerdir_name, parent=folder_root)
    folder_set.save()

    assets_dir = '{}{}'.format(os.path.abspath(os.path.dirname(__file__)),
                               '/assets/')

    # TODO Make the recursive import a feature
    parent = folder_set
    for (dirname, dirnames, filenames) in os.walk(assets_dir):
        # Create all folders
        # TODO  Respect the media_types parameter
        rel_path_tokens = dirname.replace(assets_dir, "").split(os.sep)
        get_query = {'name': rel_path_tokens[-1], 'parent_id': parent.pk}

        if rel_path_tokens[-1] != '':
            if Folder.contains_folder(parent, rel_path_tokens[-1]):
                parent = Folder.objects.get(**get_query)
            else:
                parent = Folder.objects.create(**get_query)

        # Save the file objects
        # TODO  Check file type and create Image or File accordingly
        for filename in filenames:
            furl = os.path.join(dirname,filename)
            file_obj = DjangoFile(open(furl, 'rb'), name=filename)
            image = Image.objects.create(owner=self.superuser,
                                         original_filename=filename,
                                         file=file_obj)

            file = File.objects.get(pk=image.file_ptr_id)
            file.folder_id = parent.pk
            file.save()

    fset = Set.objects.create(title=set_name, description='', date=now())
    if do_categorize:
        fset.category = [category]
        fset.save()

    Set.objects.create_or_update_set(fset.pk)
    return fset


class SetViewTests(TestCase):

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
        response = self.client.get(reverse('filersets:set_by_id_view',
                                           kwargs={'set_id': fset.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fset.title)

    def test_set_view_with_invalid_set_id_404(self):
        """
        Check that we get a 404 when hitting the URL of a set that does not
        exist
        """
        id_404 = Set.objects.all().count()
        response = self.client.get(reverse('filersets:set_by_id_view',
                                           kwargs={'set_id': id_404}))
        self.assertEqual(response.status_code, 404)

    def test_set_view_with_valid_set_slug_200(self):
        """
        Check that we get a successful response when hitting the URL of an
        existing with usage of the slug parameter.
        """
        fset = create_set(self, 'Foobar', 'My Foobar')
        response = self.client.get(reverse('filersets:set_by_slug_view',
                                           kwargs={'set_slug': fset.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fset.title)

    def test_set_view_with_invalid_set_slug_404(self):
        """
        Check that we get a 404 when hitting the URL of a set with a slug
        parameter that does not exist
        """
        slug_404 = 'foo_-_bar_-_baz'  # Big-ups if you name your set like that
        response = self.client.get(reverse('filersets:set_by_slug_view',
                                           kwargs={'set_slug': slug_404}))
        self.assertEqual(response.status_code, 404)


class ListViewTests(TestCase):

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

        url_slug = reverse('filersets:list_view', kwargs={'cat_slug': cat_slug})
        url_id = reverse('filersets:list_view', kwargs={'cat_id': cat_id})
        response = self.client.get(url_slug)
        self.assertEqual(response.status_code, 200, "200 by slug failed")
        response = self.client.get(url_id)
        self.assertEqual(response.status_code, 200, "200 by id failed")

    def test_list_view_with_no_matching_category_404(self):
        """
        Check 404 when hitting a category list view with a non-existent category
        """
        fset = create_set(self, do_categorize=False)

        url_slug = reverse('filersets:list_view', kwargs={'cat_slug': 'foo/'})
        response = self.client.get(url_slug)
        self.assertEqual(response.status_code, 404, "404 by slug failed")

        url_id = reverse('filersets:list_view', kwargs={'cat_id': 1})
        response = self.client.get(url_id)
        self.assertEqual(response.status_code, 404, "404 by id failed")

    # TODO  Test 200 for list with a category in root with one child
    # TODO  Test 200 for list with a category in root with two children
    # TODO  Test 200 for list with a category in child leaf with one ancestor
    # TODO  Test 200 for list with a category in child leaf with two ancestors
    # TODO  Test 200 for list with a category in child leaf with one child
    # TODO  Test 200 for list with a category in child leaf with two chilrdren
