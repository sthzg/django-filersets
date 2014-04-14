# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.utils import translation
from django.test.testcases import TestCase
# ______________________________________________________________________________
#                                                                        Package
from django.template import Template, Context, TemplateSyntaxError
from filersets.models import Category
from filersets.tests.helpers import create_superuser, create_categories


class FilersetsMenutagsTemplateTagsTests(TestCase):

    def setUp(self):
        translation.activate('en')
        self.superuser = create_superuser()
        self.client.login(username='admin', password='secret')

    def tearDown(self):
        Category.objects.all().delete()
        self.client.logout()
        translation.deactivate()

    def test_get_tree_with_no_param(self):
        """ The whole cat tree is rendered when no param is given """
        create_categories(3, 5)
        categories = Category.objects.all()
        out = Template(
            "{% load filersets_menutags %}"
        ).render(Context())
        #import ipdb; ipdb.set_trace()

    def test_get_tree_with_existing_int_pk(self):
        """ The cat tree is rendered starting from cat with given pk """
        pass

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





