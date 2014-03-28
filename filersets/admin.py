# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
try:
    from suit.admin import SortableModelAdmin, SortableTabularInline
    has_suit = True
except ImportError:
    has_suit = False
from mptt.admin import MPTTModelAdmin
from filersets.models import Set, Item, Category

# TODO  Try to make any use of third party packages like suit and cms optional

if has_suit:
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
        extra = 0
        max_num = 0
else:
    class ItemInlineAdmin(admin.TabularInline):
        """
        Allows to view filer_files referenced in a set to be sorted in an inline
        form inside of the SetAdmin.
        """
        fields = ('filer_file', 'is_cover')
        list_editable = ('is_cover',)
        list_display = ('is_cover',)
        model = Item
        extra = 0
        max_num = 0


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

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = dict()

        try:
            fset = Set.objects.get(pk=object_id)
            try:
                el = fset.set_root.all()[0]
                sffid = el.pk
            except KeyError:
                sffid = -1
        except ObjectDoesNotExist:
            sffid = -1

        extra_context['set_filer_folder_id'] = sffid
        return super(SetAdmin, self).change_view(request, object_id,
            form_url, extra_context=extra_context)

    search_fields = ('title',)
    list_filter = ('date', 'is_processed',)
    ordering = ('-date',)
    list_display = ('title', 'date', 'is_processed', 'process_set',)
    inlines = (ItemInlineAdmin,)
    actions = [create_or_update_filerset]
    readonly_fields = ('is_processed',)


class CategoryAdmin(MPTTModelAdmin, SortableModelAdmin):
    mptt_level_indent = 20
    list_display = ('name', 'number_of_sets', 'slug', 'is_active',)
    list_editable = ('is_active',)
    exclude = ('slug_composed',)

    # Specify name of sortable property
    sortable = 'order'

admin.site.register(Set, SetAdmin)
admin.site.register(Category, CategoryAdmin)
