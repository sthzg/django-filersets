# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from suit.admin import SortableModelAdmin, SortableTabularInline
from mptt.admin import MPTTModelAdmin
from filersets.models import Set, Item

# TODO  Try to make any use of third party packages like suit and cms optional


class ItemInlineAdmin(SortableTabularInline):
    """
    Allows to view filer_files referenced in a set to be sorted in an inline
    """
    fields = ('filer_file', 'is_cover')
    list_display = ('is_cover',)
    list_editable = ('is_cover',)
    model = Item
    sortable = 'order'


class ItemAdmin(MPTTModelAdmin, SortableModelAdmin):
    """
    Configures the admin page for a single item. This however should only be
    necessary during development or to take a quick look. In production this
    admin view should be completely abstracted from the user.
    """
    mptt_level_indent = 20
    list_display = ('set', 'filer_file', 'is_cover',)
    list_editable = ('is_cover',)
    sortable = 'order'


class SetAdmin(ModelAdmin):
    """
    Administer a single set and show the referenced filer_files in an inline
    """
    inlines = (ItemInlineAdmin,)


admin.site.register(Set, SetAdmin)
admin.site.register(Item, ItemAdmin)