# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ugettext

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

    def watch_online(self, obj):
        """ Display link on change list to the category view on the website """
        cat_url = reverse('filersets:set_by_slug_view',
                          kwargs={'set_slug': obj.slug})
        label = ugettext('Watch online')
        link = '<a href="{}"><span class="icon-eye-open icon-alpha75"></span> {}</a>'
        return link.format(cat_url, label)
    watch_online.allow_tags = True

    def process_set(self, obj):
        """
        Extra field for change list displays a link to create / update a set
        """
        set_url = reverse('filersets_api:set_process_view',
                          kwargs={'set_id': obj.pk})
        query = '?redirect={}'.format(self.current_url)
        label = _('Create / Update Set')
        wrap = _('<a href="{0}{1}"><span class="icon-refresh icon-alpha75"></span> {2}</a>')
        return wrap.format(set_url, query, label)

    process_set.allow_tags = True

    def changelist_view(self, request, extra_context=None):
        """ Provide current_url parameter to the change list """
        self.current_url = request.get_full_path()
        return super(SetAdmin, self).changelist_view(
            request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """ Provide the filer folder id of the edited set to the change page """
        if not extra_context:
            extra_context = dict()

        try:
            fset = Set.objects.get(pk=object_id)
            is_processed = fset.is_processed
            try:
                el = fset.set_root.all()[0]
                sffid = el.pk
            except KeyError:
                sffid = -1
        except ObjectDoesNotExist:
            sffid = -1
            is_processed = False

        extra_context['set_filer_folder_id'] = sffid
        extra_context['set_is_processed'] = is_processed
        return super(SetAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context)

    search_fields = ('title',)
    list_filter = ('date', 'is_processed',)
    ordering = ('-date',)
    list_display = ('title', 'date', 'is_processed',
                    'watch_online', 'process_set',)
    inlines = (ItemInlineAdmin,)
    actions = [create_or_update_filerset]
    readonly_fields = ('is_processed',)


class CategoryAdmin(MPTTModelAdmin, SortableModelAdmin):

    def watch_online(self, obj):
        """ Display link on change list to the category view on the website """
        cat_url = reverse('filersets:list_view',
                          kwargs={'cat_slug': obj.slug_composed})
        label = ugettext('Watch online')
        extra = 'icon-alpha5' if obj.number_of_sets() < int(1) else ''
        link = '<a href="{}"><span class="icon-eye-open {}"></span> {}</a>'
        return link.format(cat_url, extra, label)

    watch_online.allow_tags = True

    mptt_level_indent = 20
    list_display = ('name', 'number_of_sets', 'slug',
                    'is_active', 'watch_online',)
    list_editable = ('is_active',)
    exclude = ('slug_composed',)
    sortable = 'order'

admin.site.register(Set, SetAdmin)
admin.site.register(Category, CategoryAdmin)
