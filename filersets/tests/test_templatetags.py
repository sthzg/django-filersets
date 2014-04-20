# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Python
import re
# ______________________________________________________________________________
#                                                                         Django
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.template.loader import get_template
from django.test.client import RequestFactory
from django.utils import translation
from django.test.testcases import TestCase
# ______________________________________________________________________________
#                                                                        Package
from django.template import Template, Context
from filersets.models import Category
from filersets.tests.helpers import (
    create_superuser, create_categories, create_controlled_categories)

class FilersetsMenutagsTemplateTagsTests(TestCase):

    def setUp(self):
        translation.activate('en')
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')
        self.factory = RequestFactory()
        self.t_tree_item = get_template(
            'filersets/templatetags/_category_tree_item.html')

    def tearDown(self):
        Category.objects.all().delete()
        self.client.logout()
        translation.deactivate()

    def _reverse_listview(self, opts):
        """ Shorthand to retreive the request object for a list view """
        return self.factory.get(reverse('filersets:list_view', kwargs=(opts)))

    def _get_context_for_rendering(self, cat):
        """ Shorthand to retreive the Context object for the render method """
        cat_classes = list()
        lvl_compensate = cat.get_level_compensation()
        cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))
        return Context({'cat': cat,
                        'cat_classes': ' '.join(cat_classes),
                        'current_app': 'filersets'})

    def test_get_tree_with_no_param(self):
        """ The whole cat tree is rendered when no param is given """
        create_controlled_categories()
        Category.objects.all()
        request = self._reverse_listview({'cat_id': 1})
        request.session = self.client.session

        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        for cat in Category.objects.all():
            c = self._get_context_for_rendering(cat)
            self.assertInHTML(self.t_tree_item.render(c), out)

    def test_get_tree_with_existing_int_pk(self):
        """ The cat tree is rendered starting from cat with given pk """
        create_controlled_categories()
        Category.objects.all()
        pk_as_val = Category.objects.all().order_by('id')[0].pk
        request = self._reverse_listview({'cat_id': 1})
        request.session = self.client.session

        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree " + str(pk_as_val) + " %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        # Assert items that should be included
        for cat in Category.objects.get(pk=pk_as_val).get_descendants():
            c = self._get_context_for_rendering(cat)
            self.assertInHTML(self.t_tree_item.render(c), out)

        # Assert that items outside of the given branch are not included
        for cat in Category.objects.get(pk=pk_as_val).get_siblings():
            c = self._get_context_for_rendering(cat)
            self.assertNotIn(self.t_tree_item.render(c), out)

    def test_get_empty_tree_with_nonexisting_int_pk(self):
        """ The cat tree returns no result display """
        request = self._reverse_listview({'cat_id': 1})
        request.session = self.client.session
        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree 1 %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))
        self.assertInHTML('<p>No categories available</p>', out)

    def test_get_tree_with_existing_variable_param(self):
        """ The cat tree is rendered starting with pk given as variable """
        create_controlled_categories()
        Category.objects.all()
        request = self._reverse_listview({'cat_id': 1})
        request.session = self.client.session
        pk_as_val = Category.objects.all().order_by('id')[0].pk
        out = Template(
            "{% with pk_var=" + str(pk_as_val) + " %}"
            "{% load filersets_menutags %}"
            "{% fs_category_tree pk_var %}"
            "{% endwith %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        for cat in Category.objects.get(pk=pk_as_val).get_descendants():
            c = self._get_context_for_rendering(cat)
            self.assertInHTML(self.t_tree_item.render(c), out)

    def test_get_empty_tree_with_nonexisting_variable_param(self):
        """ The cat tree return no result display """
        request = self._reverse_listview({'cat_id': 1})
        request.session = self.client.session
        out = Template(
            "{% with pk_var=1 %}"
            "{% load filersets_menutags %}"
            "{% fs_category_tree pk_var %}"
            "{% endwith %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))
        self.assertInHTML('<p>No categories available</p>', out)

    def test_raises_exception_with_invalid_variable(self):
        """ The cat tree raises VariableDoesNotExist with invalid param """
        request = self._reverse_listview({'cat_id': 1})
        request.session = self.client.session
        with self.assertRaises(ValueError):
            Template(
                "{% with pk_var='foobar' %}"
                "{% load filersets_menutags %}"
                "{% fs_category_tree pk_var %}"
                "{% endwith %}"
            ).render(RequestContext(request, {'current_app': 'filersets'}))

    def test_active_item_from_id_view(self):
        """ The active item is highlighted in the menu tree """
        cat = Category.add_root(name='Category 01', parent=None)
        request = self._reverse_listview({'cat_id': cat.pk})
        request.session = self.client.session
        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))
        out = out.replace("\n", "")
        m = re.search(r'(?i)<a([^>]+class="(.+?)")>(.+?)</a>', out, re.M | re.U)
        self.assertTrue('active' in m.group(2))

    def test_active_item_from_slug_view(self):
        """ The active item is highlighted in the menu tree """
        cat = Category.add_root(name='Category 01', parent=None)
        request = self._reverse_listview({'cat_slug': cat.slug_composed})
        request.session = self.client.session
        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))
        out = out.replace("\n", "")
        m = re.search(r'(?i)<a([^>]+class="(.+?)")>(.+?)</a>', out, re.M | re.U)
        self.assertTrue('active' in m.group(2))

    def test_only_one_active_cat_when_switching_categories(self):
        """ Only the current item is active when switching categories """
        cat1 = Category.add_root(name='Category 01', parent=None)
        cat2 = Category.add_root(name='Category 02', parent=None)

        # Write session entries as if we come from cat1 category list page
        request = self._reverse_listview({'cat_id': cat1.pk})
        cat1_fullpath = request.get_full_path()

        # Hit cat2 category list page to check the active class on the tree
        request = self._reverse_listview({'cat_id': cat2.pk})
        request.session = self.client.session
        request.session['has_back_base'] = True
        request.session['back_base_url'] = cat1_fullpath
        request.session['fs_referrer'] = 'filersets:list_view'
        request.session.save()

        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        out = out.replace("\n", "")
        m = re.findall(r'(?i)<a([^>]+class="(.+?)")>(.+?)</a>', out, re.M | re.U)

        self.assertFalse('active' in m[0][1])
        self.assertTrue('active' in m[1][1])