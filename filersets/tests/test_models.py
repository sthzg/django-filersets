# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test.testcases import TestCase
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
    # TODO  Test creation of slug_composed for a root item
    # TODO  Test creation of slug_composed for a child item
    # TODO  Test creation of slug_composed for an item with parents and children
    # TODO  Test creation of slug_composed for an item with many children
    # TODO  Test creation of slug_composed with exceeding URL length
    pass