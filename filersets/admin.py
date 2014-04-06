# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.contrib import admin
from django.forms.models import ModelForm
from django.core.urlresolvers import reverse
from django.forms.widgets import SelectMultiple
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _, ugettext
# ______________________________________________________________________________
#                                                                        Contrib
from mptt.admin import MPTTModelAdmin
from filersets.models import Set, Item, Category
# ______________________________________________________________________________
#                                                                    Django Suit
try:
    from suit.admin import SortableModelAdmin, SortableTabularInline
    from suit.widgets import AutosizedTextarea
    has_suit = True
except ImportError:
    has_suit = False
# ______________________________________________________________________________
#                                                                 Django Select2
try:
    from django_select2 import AutoSelect2MultipleField, Select2MultipleWidget
    has_select2 = True
except ImportError:
    has_select2 = False


# TODO  Try to make any use of third party packages like suit and cms optional

# ______________________________________________________________________________
#                                                              InlineAdmin: Item
if has_suit:
    class ItemInlineForm(ModelForm):
        class Meta:
            model = Item
            widgets = {
                'description': AutosizedTextarea
            }

    class ItemInlineAdmin(SortableTabularInline):
        """
        Allows to view filer_files referenced in a set to be sorted in an inline
        form inside of the SetAdmin.
        """
        form = ItemInlineForm
        fields = ('filer_file', 'title', 'description', 'is_cover')
        list_editable = ('title', 'description', 'is_cover',)
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
        fields = ('filer_file', 'title', 'description', 'is_cover')
        list_editable = ('title', 'description', 'is_cover',)
        list_display = ('is_cover',)
        model = Item
        extra = 0
        max_num = 0


# ______________________________________________________________________________
#                                                                 ModelForm: Set
class SetForm(ModelForm):
    class Meta:
        model = Set

        # django-select2 is available -> use it to enhance the interface
        if has_select2:
            widgets = {
                'set_root': Select2MultipleWidget(
                    select2_options={
                        'width': '220px',
                        'placeholder': _('Pick folder(s)'),
                    }),
                'category': Select2MultipleWidget(
                    select2_options={
                        'width': '220px',
                        'placeholder': _('Pick one or more categories'),
                    }),
            }

        # no django-select2 -> extend the default size of multiselects
        else:
            widgets = {
                'set_root': SelectMultiple(attrs={'size': '12'}),
                'category': SelectMultiple(attrs={'size': '12'}),
            }


# ______________________________________________________________________________
#                                                                     Admin: Set
class SetAdmin(admin.ModelAdmin):
    """ Administer a set and show the referenced filer_files in an inline """
    form = SetForm

    class Media:
        """ Provide additional static files for the set admin """
        js = ("filersets/js/filersets.js",)

    #                                                                    _______
    #                                                                    Customs
    def create_or_update_filerset(self, request, queryset):
        """
        This action triggers the creation or update process for selected sets
        It displays in the admin change list.
        """
        for fset in queryset:
            Set.objects.create_or_update_set(fset.id)

    def watch_online(self, obj):
        """ Display link on change list to the category view on the website """
        cat_url = reverse('filersets:set_by_slug_view',
                          kwargs={'set_slug': obj.slug})
        label = ugettext('Watch online')
        link = '<a href="{}">' \
               '<span class="icon-eye-open icon-alpha75"></span> {}' \
               '</a>'
        return link.format(cat_url, label)

    def process_set(self, obj):
        """ Extra field for change list displays a link to process a set """
        set_url = reverse('filersets_api:set_process_view',
                          kwargs={'set_id': obj.pk})
        query = '?redirect={}'.format(self.current_url)
        label = ugettext('Process set')
        link = '<a href="{0}{1}">' \
               '<span class="icon-refresh icon-alpha75"></span> {2}' \
               '</a>'
        return link.format(set_url, query, label)

    #                                                                ___________
    #                                                                Change List
    def changelist_view(self, request, extra_context=None):
        """ Provide current_url parameter to the change list """
        self.__setattr__('current_url', request.get_full_path())
        return super(SetAdmin, self).changelist_view(
            request, extra_context=extra_context)

    #                                                                ___________
    #                                                                Change View
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

    #                                                            _______________
    #                                                            Customs Options
    create_or_update_filerset.short_description = _('Create/Update filerset')
    watch_online.allow_tags = True
    process_set.allow_tags = True

    #                                                               ____________
    #                                                               Admin Config
    ordering = ('-date',)
    search_fields = ('title',)
    inlines = (ItemInlineAdmin,)
    actions = [create_or_update_filerset]
    readonly_fields = ('is_processed',)
    list_filter = ('date', 'is_processed',)
    list_display = (
        'title', 'date', 'is_processed', 'watch_online', 'process_set',)


# ______________________________________________________________________________
#                                                                Admin: Category
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


# ______________________________________________________________________________
#                                                                   Registration
admin.site.register(Set, SetAdmin)
admin.site.register(Category, CategoryAdmin)
