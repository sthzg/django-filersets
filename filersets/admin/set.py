# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.core.exceptions import ValidationError
from django.http.request import QueryDict
from django.forms.models import ModelForm
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ugettext
from easy_thumbnails.files import get_thumbnailer
from filersets.fields import (TreeNodeMultipleChoiceField,
                              TreeNodeCheckboxSelectMultiple)
from filersets.models import Set, Item, Category, Settype
from jssettings.jssettings import JsSettings
from .constants import *
from .item import ItemInlineAdmin

# TODO(sthzg) Refactor django-suit support to addon-app.


try:
    from suit.admin import SortableModelAdmin, SortableTabularInline
    from suit.widgets import AutosizedTextarea, LinkedSelect
    has_suit = True
except ImportError:
    has_suit = False

try:
    from suit_redactor.widgets import RedactorWidget
    has_redactor = True
except ImportError:
    has_redactor = False

try:
    from django_select2 import AutoSelect2MultipleField, Select2MultipleWidget
    has_select2 = True
except ImportError:
    has_select2 = False


class SetForm(ModelForm):
    item_sort_positions = forms.Field()
    category = TreeNodeMultipleChoiceField(
        required=False,
        queryset=Category.objects.all(),
        widget=TreeNodeCheckboxSelectMultiple(attrs={'class': 'show_categories'}))

    class Media:
        css = {'all': [CSS_FILERSETS_ADMIN, CSS_FONTAWESOME]}
        js = [JS_JQUERY_UI, JS_JQ_AUTOSIZE, JS_FILERSETS_ADMIN]

    class Meta:
        model = Set

        widgets = {
            'date': AdminDateWidget(attrs={'class': 'vDateField show_set_date'}),
            'description': forms.Textarea(attrs={'class': 'vLargeTextField show_description'})
        }

        if has_redactor:
            widgets.update({'description': RedactorWidget(editor_options={'lang': 'en'})})  # NOQA

    def __init__(self, *args, **kwargs):
        """Adds HiddenInput for sorting and populates it w/ current value."""
        super(SetForm, self).__init__(*args, **kwargs)

        self.fields['item_sort_positions'] = forms.CharField(widget=forms.HiddenInput())  # NOQA
        self.fields['item_sort_positions'].required = False

        if 'instance' in kwargs.keys():
            self.fields['item_sort_positions'].initial = Set.objects.get(
                pk=kwargs['instance'].pk).get_items_sorted_pks_serialized()
        else:
            self.fields['item_sort_positions'].initial = ''

    def clean(self):
        """Adds validation to categories and prepares sorting values."""
        cleaned_data = super(SetForm, self).clean()

        # Validate that only categories from the current set type are assigned.
        try:
            set_type = cleaned_data['settype']
            for category in cleaned_data['category']:
                if category.get_root() != set_type.category.first():
                    msg = _('You may only select categories belonging to this '
                            'set type.')
                    raise ValidationError(msg)

            # Make sure that root category for set type is checked.
            if set_type.category.first() not in cleaned_data['category']:
                cleaned_data['category'] = list(cleaned_data['category']) + \
                    [set_type.category.first()]

        except KeyError:
            # If settype is not available on cleaned_data it means that the
            # input was hidden because there is only one settype available.
            pass

        # We only need to care about this if the user uses custom sorting.
        if cleaned_data.get('ordering') != 'custom':
            return cleaned_data

        # We have a set without items
        if not cleaned_data.get('item_sort_positions'):
            return cleaned_data

        # We are reading the sorting order from jQuery's sortable.
        item_sort_positions = cleaned_data.get('item_sort_positions')
        item_pks = QueryDict(item_sort_positions).getlist('itempk[]')

        # Check all items and clean up the list.
        del_keys = list()
        for idx, item_pk in enumerate(item_pks):
            if 'filepk:' in item_pk:
                # When adding new items inline we don't have a PK before saving.
                # Instead they pass the PK of the filer object so that we can
                # afterwards look the item PK through the file pk. If this is
                # the case then entries are prefixed with 'filepk:'
                continue
            else:
                # All other entries need to be of type int in order to be valid.
                try:
                    item_pks[idx] = int(item_pk)
                except ValueError:
                    del_keys.append(idx)

        del_keys = sorted(del_keys, reverse=True)
        for key in del_keys:
            del item_pks[key]

        cleaned_data['item_sort_positions'] = item_pks

        return cleaned_data


class SetAdmin(admin.ModelAdmin):
    """Administer a set and show the referenced filer_files in an inline."""
    form = SetForm

    class Media:
        js = (JS_JQUERY_UI, JS_FILERSETS_ADMIN,)
        css = {'all': [CSS_FILERSETS_ADMIN, CSS_FONTAWESOME]}

    def save_formset(self, request, form, formset, change):
        formset.save(commit=True)

        # All items are saved now, so we can update the sort positions.
        cleaned_data = form.cleaned_data
        if cleaned_data.get('ordering') != 'custom':
            form.instance.save_item_sort()
        else:
            item_pks = cleaned_data.get('item_sort_positions')

            del_keys = list()
            for idx, item_pk in enumerate(item_pks):
                if 'filepk:' in str(item_pk):
                    # This is a new item. Look it up by the file id.
                    fpk = int(item_pk.split(':')[1])
                    item_pks[idx] = Item.objects.get(
                        filer_file__id=fpk, set=form.instance).pk
                else:
                    # Make sure that the item exists (relevant after deleting).
                    try:
                        Item.objects.get(pk=item_pk)
                    except Item.DoesNotExist:
                        del_keys.append(idx)

            del_keys = sorted(del_keys, reverse=True)
            for key in del_keys:
                del item_pks[key]

            form.instance.save_item_sort(item_pks)

    def create_or_update_filerset(self, request, queryset):
        """Action triggers the creation or update process for selected sets."""
        for fset in queryset:
            Set.objects.create_or_update_set(fset.id)

    def watch_online(self, obj):
        """Display link on change list to the detail view on the website."""
        fset_url = self.get_fset_url(obj)
        label = ugettext('Watch online')
        link = '<a href="{}">' \
               '<i class="fa fa-eye" title="{}"></i>' \
               '</a>'

        return link.format(fset_url, label)

    def get_fset_url(self, obj):
        """Returns url to filerset detail page.

        .. note::

            You can override this method in your modules. To do so, extend
            from SetAdmin and re-register your extended admin. By overriding
            ``get_fset_url`` 'watch online' can link to arbitrary urls.

        """
        view = 'filersets:set_by_slug_view'
        return reverse(view, kwargs={
            'set_type': obj.settype.slug,
            'set_slug': obj.slug})

    def get_cover_item_thumbnail(self, obj):
        """Returns image tag w/ thumbnail of the media item marked as cover."""
        output = ''
        if obj.filer_set.count() > 0:
            q_order = ('item_sort__sort',)
            if obj.filer_set.filter(is_cover=True).count() > 0:
                cover_item = obj.filer_set.filter(is_cover=True) \
                                .order_by(*q_order)[0]
            else:
                cover_item = obj.filer_set.all().order_by(*q_order)[0]

            if cover_item.ct.name == u'image':
                options = {'size': (50, 0), 'crop': True}
                thumb_url = get_thumbnailer(
                    cover_item.filer_file).get_thumbnail(options).url
                output = '<img class="" src="{}"  data-filepk="{}">'
                output = output.format(thumb_url, cover_item.filer_file.id)

        return output

    def process_set(self, obj):
        """Extra field for change list displays a link to process a set."""
        is_dirty = obj.check_dirty()

        set_url = reverse('filersets_api:set_process_view',
                          kwargs={'set_id': obj.pk})
        query = '?redirect={}'.format(self.current_url)
        label = ugettext('Process set')

        if is_dirty:
            link = '<a href="{0}{1}" data-behavior="lock_on_click">' \
                   '<i class="fa fa-refresh" title="{2}"></span>' \
                   '</a>'
            ret = link.format(set_url, query, label)

        else:
            ret = '<i class="fa fa-refresh" title="{2}" style="opacity: .3"></span>'

        return ret

    def changelist_view(self, request, extra_context=None):
        """Provides current_url parameter to the change list."""
        self.__setattr__('current_url', request.get_full_path())
        return super(SetAdmin, self).changelist_view(
            request, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        """Provides configuration for JsSettings object on add view."""
        settype_config = Settype.objects.get_settype_config_dict()
        jss = JsSettings(request)
        jss.set_jssetting('filersets.setconfig', settype_config)

        return super(SetAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Provides additional context to the admin change page template."""
        try:
            fset = Set.objects.get(pk=object_id)
            is_processed = fset.is_processed
            fset_url = self.get_fset_url(fset)
            try:
                el = fset.folder
                sffid = el.pk
            except KeyError:
                sffid = -1

        except Set.DoesNotExist:
            fset_url = None
            sffid = -1
            is_processed = False

        # To enhance the admin forms we hide certain input fields depending
        # on the set type instance configuration. To enable this in admin,
        # we need to pass the configuration settings to Javascript.
        settype_config = Settype.objects.get_settype_config_dict()
        jss = JsSettings(request)
        jss.set_jssetting('filersets.setconfig', settype_config)

        if not extra_context:
            extra_context = dict()

        extra_context['set_is_dirty'] = fset.check_dirty()
        extra_context['set_url'] = fset_url
        extra_context['set_filer_folder_id'] = sffid
        extra_context['set_is_processed'] = is_processed

        return super(SetAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context)

    def get_fieldsets(self, request, obj=None):
        """Alters fieldsets depending on actual data and set type settings."""
        fieldsets = super(SetAdmin, self).get_fieldsets(request, obj)

        # Removes settype field if only one set type is configured.
        if Settype.objects.all().count() < 2:
            try:
                fieldsets[0][1]['fields'].remove('settype')

            except ValueError:
                pass

        return fieldsets

    create_or_update_filerset.short_description = _('Create/Update filerset')
    watch_online.allow_tags = True
    watch_online.short_description = ''
    process_set.allow_tags = True
    process_set.short_description = ''
    get_cover_item_thumbnail.allow_tags = True
    get_cover_item_thumbnail.short_description = _('Cover thumb')

    ordering = ('-date',)
    search_fields = ('title',)
    inlines = (ItemInlineAdmin,)
    actions = [create_or_update_filerset]
    readonly_fields = ('get_cover_item_thumbnail', 'is_processed',)
    list_filter = ('date', 'is_processed', 'status', 'settype',)
    list_display = ('get_cover_item_thumbnail', 'title', 'date', 'status',
                    'is_processed', 'watch_online', 'process_set',
                    'is_autoupdate',)
    list_editable = ('status', 'is_autoupdate',)
    list_display_links = ('get_cover_item_thumbnail', 'title',)

    fieldsets = [
        (None, {
            'classes': ('suit-tab suit-tab-general',),
            'fields': ['settype', 'status', 'date', 'ordering', 'title',
                       'folder', 'recursive', 'is_autoupdate', 'category',
                       'is_processed', 'item_sort_positions']}),
        ('Description', {
            'classes': ('show_description suit-tab suit-tab-show_description full-width',),
            'fields': ['description']})]

    if has_suit:
        suit_form_tabs = (
            ('general', _('Info')),
            ('show_description', _('Text')),
            ('items', _('Set media')))