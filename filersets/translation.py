# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                        Contrib
from modeltranslation.translator import translator, TranslationOptions
# ______________________________________________________________________________
#                                                                        Package
from filersets.models import Item

class ItemTranslationOptions(TranslationOptions):
    fields = ('title', 'description',)

translator.register(Item, ItemTranslationOptions)