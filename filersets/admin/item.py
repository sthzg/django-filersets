# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.contrib import admin
from django.conf.urls import patterns, url
from django.forms.models import ModelForm
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ugettext
from easy_thumbnails.files import get_thumbnailer
from filersets.models import Set, Item, Category, Settype
from .constants import *


# TODO(sthzg) Refactor django-suit support to addon-app.
try:
    from suit.admin import SortableModelAdmin, SortableTabularInline
    from suit.widgets import AutosizedTextarea, LinkedSelect
    has_suit = True
except ImportError:
    has_suit = False


class ItemInlineForm(ModelForm):
    """Item inline form."""
    class Meta:
        model = Item
        if has_suit:
            widgets = {'description': AutosizedTextarea}


class ItemForm(ModelForm):
    """Item form."""
    class Meta:
        model = Item
        if has_suit:
            widgets = {
                'description': AutosizedTextarea,
                'set': LinkedSelect}


class ItemInlineAdmin(admin.TabularInline):
    """Allows to view filer_files referenced in a set."""
    if has_suit:
        suit_classes = 'suit-tab suit-tab-items'

    form = ItemInlineForm
    fields = (
        'get_sort_position',
        'get_item_thumb',
        'filer_file',
        'get_original_filename',
        'title',
        'description',
        'is_cover',
        'is_locked',)

    readonly_fields = (
        'get_sort_position',
        'get_item_thumb',
        'get_original_filename',)

    model = Item
    extra = 0
    list_per_page = 30
    template = 'filersets/set_inline_suit.html'


class ItemAdmin(admin.ModelAdmin):
    class Media:
        """Provides additional static files for the set admin."""
        js = [JS_JQUERY_UI, JS_FILERSETS_ADMIN]
        css = {'all': [CSS_FILERSETS_ADMIN, CSS_FONTAWESOME]}

    def get_urls(self):
        """Provides pre-filtered change list views for set types.

        Deprecated: functionality will be provided in django-filerstreams.
        """
        urls = super(ItemAdmin, self).get_urls()

        # Queries set types and collects entries that need a stream view.
        my_urls = patterns('')
        for settype in Settype.objects.all():
            # Checks if we really need a custom view for this set type.
            if not settype.base_folder or not settype.has_mediastream:
                continue

            # If there is no set connected to the base folder continue.
            try:
                fset = Set.objects.get(folder=settype.base_folder)
            except Set.DoesNotExist:
                continue

            # Assembles the urls for the custom views.
            my_urls += patterns('', url(
                r'^'+settype.slug+'stream/$',
                self.admin_site.admin_view(self.settypestream_view),
                {
                    'modeladmin': self,
                    'fset': fset
                },
                name='{}stream'.format(settype.slug)
            ))

        return my_urls + urls

    def settypestream_view(self, request, modeladmin, fset):
        """Filters the queryset to show only items in the set type's base set.

        Deprecated: functionality will be provided in django-filerstreams.
        """
        class SettypeItemAdmin(admin.site._registry[Item].__class__):

            def __init__(self, model, admin_site, request):
                self.request = request
                super(SettypeItemAdmin, self).__init__(model, admin_site)

            def get_queryset(self, request):
                qs = super(ItemAdmin, self).get_queryset(request)
                return qs.filter(set=Set.objects.get(pk=fset.pk))

            # Remove the set filter on this view.
            for idx, lfilter in enumerate(self.list_filter):
                if lfilter == 'set':
                    del self.list_filter[idx]

        inst = SettypeItemAdmin(modeladmin.model, admin.site, request)
        return inst.changelist_view(request, extra_context={})

    class TimelineFilter(admin.SimpleListFilter):
        """Provides a filter for objects on timeline / not on timeline."""
        title = _('on timeline?')
        parameter_name = 'timeline'

        def lookups(self, request, model_admin):
            return (
                ('yes', _('yes')),
                ('no', _('no')),
            )

        def queryset(self, request, queryset):
            q_filter = {}
            q_exclude = {}

            if self.value() == 'yes':
                q_filter = {'filer_file__filemodelext_file__is_timeline': True}
                q_exclude = {}

            elif self.value() == 'no':
                q_filter = {}
                q_exclude = {'filer_file__filemodelext_file__is_timeline': True}

            return queryset.filter(**q_filter).exclude(**q_exclude)

    class CategoryFilter(admin.SimpleListFilter):
        """Provides a filter by object category."""
        title = _('category')
        parameter_name = 'category'

        def lookups(self, request, model_admin):
            # TODO Respect set type settings
            data = list()
            for category in Category.objects.all().order_by('name'):
                data.append((category.pk, category.name,))
            return data

        def queryset(self, request, queryset):
            if self.value():
                q_filter = {
                    'filer_file__filemodelext_file__category': self.value()
                }
                return queryset.filter(**q_filter)
            else:
                return queryset

    form = ItemForm
    list_display = (
        'item_thumb',
        'set_admin_link',
        'current_categories',
        'title',
        'description',
        'created',
        'get_is_timeline',)

    readonly_fields = ('get_is_timeline',)
    list_editable = ('title', 'description',)
    list_filter = ['set',
                   CategoryFilter,
                   'is_cover',
                   'created',
                   'modified',
                   TimelineFilter]

    list_display_links = ('item_thumb',)
    list_per_page = 25
    fields = ('filer_file', 'title', 'description',)
    search_fields = ('filer_file__file', 'title', 'set__title')
    ordering = ['-created']

    def __init__(self, *args, **kwargs):
        super(ItemAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None,)

    def item_thumb(self, obj):
        """Returns a thumbnail representation of the current item."""
        if obj.filer_file.polymorphic_ctype.name == 'image':
            options = {'size': (80, 0), 'crop': True}
            thumb_url = get_thumbnailer(
                obj.filer_file.file).get_thumbnail(options).url
            output = '<img class="fs_filepk" src="{}"  data-filepk="{}">'
            output = output.format(thumb_url, obj.filer_file.id)
        else:
            output = '{}'.format(ugettext('Edit'))

        link = '<a href="{}?_popup=1" onclick="return showAddAnotherPopup(this);">{}</a>'
        url = obj.filer_file.get_admin_url_path()
        return link.format(url, output)

    def set_admin_link(self, obj):
        """Returns a link to th admin change page of the set"""
        url = reverse('admin:filersets_set_change', args={(obj.set.pk)})
        link = u'<a href="{}">{}</a>'
        return link.format(url, obj.set.title)

    def current_categories(self, obj):
        """Returns currently assigned categories of an item as string.

        Deprecated: functionality will be provided in django-filerstreams.
        """
        try:
            span = '<span class="label cat">{} ' \
                   '<a class="cat-del" data-catpk="{}" data-filepk="{}">x</a>' \
                   '</span>'
            cats = u''.join([span.format(cat.name, cat.pk, obj.filer_file.pk)
                             for cat in obj.filer_file.filemodelext_file.all()[0].category.all()])

        except (TypeError, IndexError):
            cats = _(u'None')
        return cats

    def get_changelist_form(self, request, **kwargs):
        """Alters change list to use custom widgets."""
        kwargs.setdefault('form', ItemForm)
        return super(ItemAdmin, self).get_changelist_form(request, **kwargs)

    current_categories.allow_tags = True
    item_thumb.short_description = _('file')
    item_thumb.allow_tags = True
    set_admin_link.short_description = _('set')
    set_admin_link.allow_tags = True