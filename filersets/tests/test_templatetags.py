# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.template import Template, Context
from django.template.loader import get_template
from django.test.client import RequestFactory
from django.test.testcases import TestCase
from django.utils import translation
from filersets.models import Category
from filersets.tests.helpers import (create_superuser,
                                     create_controlled_categories,
                                     create_set_type)


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
        """ Shorthand to retrieve the request object for a list view """
        return self.factory.get(reverse('filersets:list_view', kwargs=(opts)))

    def _get_context_for_rendering(self, cat, set_type, request, lvl_compensate=0):
        """ Shorthand to retrieve the Context object for the render method """
        cat_classes = list()
        cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))

        cat_slug_url = reverse(
            'filersets:list_view',
            kwargs=({'set_type': set_type, 'cat_slug': cat.slug_composed}),
            current_app=set_type)

        cat_id_url = reverse(
            'filersets:list_view',
            kwargs=({'set_type': set_type, 'cat_id': cat.pk}),
            current_app=set_type)

        if request.get_full_path() in (cat_slug_url, cat_id_url):
            cat_classes.append('active')

        return Context({'cat': cat,
                        'set_type': set_type,
                        'cat_classes': ' '.join(cat_classes),
                        'current_app': 'filersets'})

    def test_get_tree_with_no_param(self):
        """ The whole cat tree is rendered when no param is given """
        create_controlled_categories()
        cats = Category.objects.all().order_by('id')

        params = {'set_type': cats[0].slug, 'cat_id': 1}
        request = self._reverse_listview(params)
        request.session = self.client.session

        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        for cat in Category.objects.all():
            c = self._get_context_for_rendering(cat, cats[0].slug, request)
            self.assertInHTML(self.t_tree_item.render(c), out)

    def test_get_tree_with_existing_int_pk(self):
        """ The cat tree is rendered starting from cat with given pk """
        create_controlled_categories()
        cats = Category.objects.all().order_by('id')
        pk_as_val = cats[0].pk
        request = self._reverse_listview({'set_type': cats[0].slug, 'cat_id': 1})
        request.session = self.client.session

        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree " + str(pk_as_val) + " %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        # Assert items that should be included
        for cat in Category.objects.get(pk=pk_as_val).get_descendants():
            c = self._get_context_for_rendering(cat, cats[0].slug, request)
            self.assertInHTML(self.t_tree_item.render(c), out)

        # Assert that items outside of the given branch are not included
        for cat in Category.objects.get(pk=pk_as_val).get_siblings():
            c = self._get_context_for_rendering(cat, cats[0].slug, request)
            self.assertNotIn(self.t_tree_item.render(c), out)

    def test_get_empty_tree_with_nonexisting_int_pk(self):
        """ The cat tree returns no result display """
        set_type = create_set_type()
        request = self._reverse_listview({'set_type': set_type.slug, 'cat_id': 1})
        request.session = self.client.session
        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree 99 %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))
        self.assertInHTML('<p>No categories available</p>', out)

    def test_get_tree_with_existing_variable_param(self):
        """ The cat tree is rendered starting with pk given as variable """
        create_controlled_categories()
        cats = Category.objects.all().order_by('pk')
        request = self._reverse_listview({'set_type': cats[0].slug, 'cat_id': 1})
        request.session = self.client.session
        pk_as_val = Category.objects.first().pk
        out = Template(
            "{% with pk_var=" + str(pk_as_val) + " %}"
            "{% load filersets_menutags %}"
            "{% fs_category_tree pk_var %}"
            "{% endwith %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        root_cat = Category.objects.get(pk=pk_as_val)
        lvl_compensate = root_cat.get_level_compensation()
        for cat in root_cat.get_descendants():
            c = self._get_context_for_rendering(cat, cats[0].slug, request, lvl_compensate)
            self.assertInHTML(self.t_tree_item.render(c), out)

    def test_get_empty_tree_with_nonexisting_variable_param(self):
        """ The cat tree return no result display """
        set_type = create_set_type()
        request = self._reverse_listview({'set_type': set_type.slug, 'cat_id': 1})
        request.session = self.client.session
        out = Template(
            "{% with pk_var=99 %}"
            "{% load filersets_menutags %}"
            "{% fs_category_tree pk_var %}"
            "{% endwith %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))
        self.assertInHTML('<p>No categories available</p>', out)

    def test_raises_exception_with_invalid_variable(self):
        """ The cat tree raises VariableDoesNotExist with invalid param """
        set_type = create_set_type()
        request = self._reverse_listview({'set_type': set_type.slug, 'cat_id': 1})
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
        set_type = create_set_type()
        request = self._reverse_listview({'set_type': set_type.slug, 'cat_id': set_type.get_root_category().pk})
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
        set_type = create_set_type()
        request = self._reverse_listview({'set_type': set_type.slug, 'cat_slug': set_type.get_root_category().slug_composed})
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
        set_type = create_set_type()
        cat1 = set_type.get_root_category().add_child(name='Category 01', is_active=True, parent=None)
        cat2 = set_type.get_root_category().add_child(name='Category 02', is_active=True, parent=None)

        # Write session entries as if we came from cat1 category list page.
        request = self._reverse_listview({'set_type': set_type.slug, 'cat_id': cat1.pk})
        cat1_fullpath = request.get_full_path()

        # Hit cat2 category list page to check the active class on the tree.
        request = self._reverse_listview({'set_type': set_type.slug, 'cat_id': cat2.pk})
        request.session = self.client.session
        request.session['has_back_base'] = True
        request.session['back_base_url'] = cat1_fullpath
        request.session['fs_referrer'] = '{}:list_view'.format(set_type.slug)
        request.session.save()

        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree " + str(set_type.get_root_category().pk) + " %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        out = out.replace("\n", "")
        m = re.findall(r'(?i)<a([^>]+class="(.+?)")>(.+?)</a>', out, re.M | re.U)

        self.assertFalse('active' in m[0][1])
        self.assertTrue('active' in m[1][1])
