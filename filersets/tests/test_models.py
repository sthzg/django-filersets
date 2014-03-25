# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test.testcases import TestCase
from filersets.models import Set, Item, Category


class CategoryModelTests(TestCase):
    # TODO  Test creation of slug_composed for a root item
    # TODO  Test creation of slug_composed for a child item
    # TODO  Test creation of slug_composed for an item with parents and children
    # TODO  Test creation of slug_composed for an item with many children
    # TODO  Test creation of slug_composed with exceeding URL length
    pass