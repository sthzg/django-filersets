# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.utils.translation import ugettext_lazy as _
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

    def create_or_update_filerset(self, request, queryset):
        """
        This is an action that triggers the creation or update process for the
        selected filersets. It displays in the admin change list.

        TODO    Make the update routine available in different ways. e.g.
                calling the command, using a celery if enabled, etc.
        """
        for fset in queryset:
            Set.objects.create_or_update_set(fset.id)

    create_or_update_filerset.short_description = _('Create/Update filerset')

    list_display = ('title', 'date', 'is_processed')
    inlines = (ItemInlineAdmin,)
    actions = [create_or_update_filerset]


admin.site.register(Set, SetAdmin)
admin.site.register(Item, ItemAdmin)