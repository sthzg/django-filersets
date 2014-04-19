# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
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

    def tearDown(self):
        Category.objects.all().delete()
        self.client.logout()
        translation.deactivate()

    def test_get_tree_with_no_param(self):
        """ The whole cat tree is rendered when no param is given """
        create_controlled_categories()
        Category.objects.all()
        request = self.factory.get(reverse('filersets:list_view',
                                           kwargs=({'cat_id': 1})))
        request.session = self.client.session
        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        t = get_template('filersets/templatetags/_category_tree_item.html')
        for cat in Category.objects.all():
            lvl_compensate = 0
            cat_classes = list()
            cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))
            c = Context({'cat': cat,
                         'cat_classes': ' '.join(cat_classes),
                         'current_app': 'filersets'})
            self.assertInHTML(t.render(c), out)

    def test_get_tree_with_existing_int_pk(self):
        """ The cat tree is rendered starting from cat with given pk """
        create_controlled_categories()
        Category.objects.all()
        request = self.factory.get(reverse('filersets:list_view',
                                           kwargs=({'cat_id': 1})))
        request.session = self.client.session
        out = Template(
            "{% load filersets_menutags %}"
            "{% fs_category_tree 3 %}"
        ).render(RequestContext(request, {'current_app': 'filersets'}))

        t = get_template('filersets/templatetags/_category_tree_item.html')
        for cat in Category.objects.get(pk=3).get_descendants():
            lvl_compensate = 1
            cat_classes = list()
            cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))
            c = Context({'cat': cat,
                         'cat_classes': ' '.join(cat_classes),
                         'current_app': 'filersets'})
            self.assertInHTML(t.render(c), out)

        cat = Category.objects.get(pk=8)
        lvl_compensate = 0
        cat_classes = list()
        cat_classes.append('cat-level-{}'.format(cat.depth-lvl_compensate))
        c = Context({'cat': cat,
                     'cat_classes': ' '.join(cat_classes),
                     'current_app': 'filersets'})
        self.assertNotIn(t.render(c), out)


    def test_get_empty_tree_with_nonexisting_int_pk(self):
        """ The cat tree return no result display """
        pass

    def test_get_tree_with_existing_variable_param(self):
        """ The cat tree is rendered starting with pk given as variable """
        pass

    def test_get_empty_tree_with_nonexisting_variable_param(self):
        """ The cat tree return no result display """
        pass

    def test_raises_exception_with_invalid_variable(self):
        """ The cat tree raises VariableDoesNotExist with invalid param """
        pass

    def test_level_compensate(self):
        """ The indentation is compensated when starting cat > level 1 """
        pass

    def test_active_item_from_id_view(self):
        """ The active item is highlighted in the menu tree """
        pass

    def test_active_item_from_slug_view(self):
        """ The active item is highlighted in the menu tree """
        pass

    def test_only_one_active_cat_when_switching_categories(self):
        """ Only the current item is rendered when switching categories """
        pass





