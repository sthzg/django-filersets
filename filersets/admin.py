# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from suit.admin import SortableModelAdmin, SortableTabularInline
from mptt.admin import MPTTModelAdmin
from filersets.models import Set, Item

# TODO  Try to make any use of third party packages like suit and cms optional

class ItemInlineAdmin(SortableTabularInline):
    """
    Allows to view filer_files referenced in a set to be sorted in an inline
    form inside of the SetAdmin.
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


class SetAdmin(admin.ModelAdmin):
    """
    Administer a single set and show the referenced filer_files in an inline
    """

    class Media:
        js = ("filersets/filersets.js",)

    def create_or_update_filerset(self, request, queryset):
        """
        This action triggers the creation or update process for selected sets
        It displays in the admin change list.
        """
        for fset in queryset:
            Set.objects.create_or_update_set(fset.id)

    create_or_update_filerset.short_description = _('Create/Update filerset')

    def process_set(self, obj):
        """
        Extra field for change list displays a link to create / update a set
        """
        set_url = reverse('filersets_api:set_process_view',
                          kwargs={'set_id': obj.pk})
        query = '?redirect={}'.format(self.current_url)
        label = _('Create / Update Set')
        wrap = _('<a href="{0}{1}"><span class="icon-refresh"></span> {2}</a>')
        return wrap.format(set_url, query, label)

    process_set.allow_tags = True
    process_set.short_description = _('Create / Update Set')

    def changelist_view(self, request, extra_context=None):
        # We need to override the changelist_view to have the current_url
        # parameter available in the process_set function
        self.current_url = request.get_full_path()
        return super(SetAdmin, self).changelist_view(
            request, extra_context=extra_context
        )

    search_fields = ('title',)
    list_filter = ('date', 'is_processed',)
    ordering = ('-date',)
    list_display = ('title', 'date', 'is_processed', 'process_set',)
    inlines = (ItemInlineAdmin,)
    actions = [create_or_update_filerset]
    readonly_fields = ('is_processed',)


admin.site.register(Set, SetAdmin)
admin.site.register(Item, ItemAdmin)
