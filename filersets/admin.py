# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django import forms
from django.conf.urls import patterns
from django.contrib import admin
from django.http.request import QueryDict
from django.forms.models import ModelForm
from django.forms.widgets import SelectMultiple
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ugettext
# ______________________________________________________________________________
#                                                                        Contrib
from filer.admin.imageadmin import ImageAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from easy_thumbnails.files import get_thumbnailer
# ______________________________________________________________________________
#                                                                         Custom
from filersets.models import Set, Item, Category, Affiliate, FilemodelExt
# ______________________________________________________________________________
#                                                                    Django Suit
try:
    from suit.admin import SortableModelAdmin, SortableTabularInline
    from suit.widgets import AutosizedTextarea, LinkedSelect

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

    class ItemInlineAdmin(admin.TabularInline):
        """
        Allows to view filer_files referenced in a set.
        """
        form = ItemInlineForm
        fields = (
            'get_sort_position',
            'get_item_thumb',
            'filer_file',
            'get_original_filename',
            'title',
            'description',
            'is_cover',
            'is_locked',
        )
        readonly_fields = (
            'get_sort_position',
            'get_item_thumb',
            'get_original_filename',
        )
        model = Item
        extra = 0
        list_per_page = 30
        template = 'filersets/set_inline_suit.html'

    class ItemForm(ModelForm):
        class Meta:
            model = Item
            widgets = {
                'description': AutosizedTextarea,
                'set': LinkedSelect,
            }

else:
    class ItemInlineAdmin(admin.TabularInline):
        """
        Allows to view filer_files referenced in a set.
        """
        fields = (
            'filer_file',
            'title',
            'description',
            'is_cover',
            'is_locked',
            'is_timeline',
        )
        list_editable = (
            'description',
            'is_cover',
            'is_timeline',
        )
        list_display = ('title', 'is_cover', 'description', 'is_cover',)
        list_display_links = ('title',)
        model = Item
        extra = 0

    class ItemForm(ModelForm):
        class Meta:
            model = Item
            widgets = {}


# ______________________________________________________________________________
#                                                                    Admin: Item
class ItemAdmin(admin.ModelAdmin):

    class Media:
        """
        Provides additional static files for the set admin.
        """
        css = {'all': [
            'filersets/css/filersets_admin.css',
            '//netdna.bootstrapcdn.com/font-awesome/4.0.3/css/font-awesome.min.css'
        ]}
        js = ['filersets/js/filersets_admin.js']

    #                                                                ___________
    #                                                                Custom URLs
    def get_urls(self):
        """
        Provides custom admin views for affiliates that have their
        ``has_mediastream`` flag checked.
        """
        urls = super(ItemAdmin, self).get_urls()

        # Queries affiliates and collects entries that need a stream view.
        my_urls = patterns('')
        for affiliate in Affiliate.objects.all():

            # We don't need a view for this affiliate.
            if not affiliate.base_folder or not affiliate.has_mediastream:
                continue

            my_urls += patterns('', (
                r'^'+affiliate.slug+'stream/$',
                self.admin_site.admin_view(
                    self.affiliatestream_view
                ), {'fset': Set.objects.get(folder=affiliate.base_folder)}
            ))

        return my_urls + urls

    #                                                          _________________
    #                                                          View: Mediastream
    def affiliatestream_view(self, request, fset):
        """
        Filters the queryset to show only items in the affiliate's base set.
        """
        def get_queryset(request):
            qs = super(ItemAdmin, self).get_queryset(request)
            return qs.filter(set=Set.objects.get(pk=fset.pk))

        self.get_queryset = get_queryset

        # Remove the set filter on this view.
        for idx, lfilter in enumerate(self.list_filter):
            if lfilter == 'set':
                del self.list_filter[idx]

        return self.changelist_view(request)

    #                                                           ________________
    #                                                           Filter: Timeline
    class TimelineFilter(admin.SimpleListFilter):
        """
        Provides a filter for objects on timeline / not on timeline.
        """
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

    #                                                           ________________
    #                                                           Filter: Category
    class CategoryFilter(admin.SimpleListFilter):
        """
        Provides a filter by object category.
        """
        title = _('category')
        parameter_name = 'category'

        def lookups(self, request, model_admin):
            # TODO Respect affiliate settings
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
        'get_is_timeline',
    )
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

    #                                                                        ___
    #                                                                 item_thumb
    def item_thumb(self, obj):
        """
        Return a thumbnail representation of the current item.
        """
        if obj.filer_file.polymorphic_ctype.name == 'image':
            options = {'size': (80, 0), 'crop': True}
            thumb_url = get_thumbnailer(
                obj.filer_file.file).get_thumbnail(options).url
            output = '<img class="fs_filepk" src="{}"  data-filepk="{}">'
            output = output.format(thumb_url, obj.filer_file.id)
        else:
            output = '{}'.format(ugettext('Edit'))

        return output

    #                                                                        ___
    #                                                             set_admin_link
    def set_admin_link(self, obj):
        """
        Return a link to th admin change page of the set
        """
        url = reverse('admin:filersets_set_change', args={(obj.set.pk)})
        link = '<a href="{}">{}</a>'
        return link.format(url, obj.set.title)

    #                                                                        ___
    #                                                         current_categories
    def current_categories(self, obj):
        """
        Return a string of currently assign categories to one item.
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

    #                                                                        ___
    #                                                        get_changelist_form
    def get_changelist_form(self, request, **kwargs):
        """
        Alter change list to use custom widgets
        """
        kwargs.setdefault('form', ItemForm)
        return super(ItemAdmin, self).get_changelist_form(request, **kwargs)

    current_categories.allow_tags = True
    item_thumb.short_description = _('Item')
    item_thumb.allow_tags = True
    set_admin_link.short_description = _('Set')
    set_admin_link.allow_tags = True


# ______________________________________________________________________________
#                                                                 ModelForm: Set
class SetForm(ModelForm):

    item_sort_positions = forms.Field()

    class Media:
        """ Provide additional static files for the set admin """
        css = {'all': [
            'filersets/css/filersets_admin.css',
            '//netdna.bootstrapcdn.com/font-awesome/4.0.3/css/font-awesome.min.css'
        ]}
        js = [
            'filersets/vendor/jquery-ui-1.10.4/js/jquery-ui-1.10.4.min.js',
            'filersets/js/filersets_admin.js'
        ]

    class Meta:
        model = Set
        widgets = {
            'category': SelectMultiple(attrs={'size': '12'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Add a HiddenInput() to hold sorting and populate it with current value
        """
        super(SetForm, self).__init__(*args, **kwargs)
        self.fields['item_sort_positions'] = forms.CharField(
            widget=forms.HiddenInput())
        self.fields['item_sort_positions'].required = False
        if 'instance' in kwargs.keys():
            self.fields['item_sort_positions'].initial = Set.objects.get(
                pk=kwargs['instance'].pk).get_items_sorted_pks_serialized()
        else:
            self.fields['item_sort_positions'].initial = ''

    def clean(self):
        """
        Checks if we have custom ordering on the set and if so prepares the
        values for storing.
        """
        cleaned_data = super(SetForm, self).clean()

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


# ______________________________________________________________________________
#                                                                     Admin: Set
class SetAdmin(admin.ModelAdmin):
    """ Administer a set and show the referenced filer_files in an inline """
    form = SetForm

    class Media:
        """ Provide additional static files for the set admin """
        js = ("filersets/js/filersets.js",)

    #                                                               ____________
    #                                                               Save Formset
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

    #                                                              _____________
    #                                                              Model Methods
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
                el = fset.folder
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

    #                                                      _____________________
    #                                                      Model Methods Options
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
    list_filter = ('date', 'is_processed', 'status',)
    list_display = ('title', 'date', 'status', 'is_processed', 'watch_online',
                    'process_set', 'is_autoupdate',)
    list_editable = ('status', 'is_autoupdate',)


# ______________________________________________________________________________
#                                                         InlineAdmin: Affiliate
class AffiliateInlineAdmin(admin.StackedInline):
    """
    Adds affiliate settings as inline to category admin
    """
    model = Affiliate.category.through
    extra = 0


# ______________________________________________________________________________
#                                                           ModelForm: Affiliate
class AffiliateModelForm(forms.ModelForm):
    class Meta:
        model = Affiliate
        widgets = {
            'category': SelectMultiple(attrs={'size': '12'}),
        }

# ______________________________________________________________________________
#                                                               Admin: Affiliate
class AffiliateAdmin(admin.ModelAdmin):
    form = AffiliateModelForm
    list_display = ('label', 'namespace', 'memo',)


# ______________________________________________________________________________
#                                                                Admin: Category
class CategoryAdmin(TreeAdmin):

    def watch_online(self, obj):
        """ Display link on change list to the category view on the website """
        cat_url = reverse('filersets:list_view',
                          kwargs={'cat_slug': obj.slug_composed})
        label = ugettext('Watch online')
        extra = 'icon-alpha5' if obj.number_of_sets() < int(1) else ''
        link = '<a href="{}"><span class="icon-eye-open {}"></span> {}</a>'
        return link.format(cat_url, extra, label)

    watch_online.allow_tags = True

    form = movenodeform_factory(Category)
    list_display = ('name', 'number_of_sets', 'slug', 'is_active',)
    list_editable = ('is_active',)
    exclude = ('slug_composed', 'path', 'depth', 'numchild', 'parent',)
    inlines = [AffiliateInlineAdmin]


# ______________________________________________________________________________
#                                                      InlineAdmin: FilemodelExt
class FilemodelExtForm(ModelForm):

    class Media:
        """ Provide additional static files for the set admin """
        css = {'all': [
            'filersets/css/filersets_admin.css',
            '//netdna.bootstrapcdn.com/font-awesome/4.0.3/css/font-awesome.min.css'
        ]}
        js = [
            'filersets/vendor/jquery-ui-1.10.4/js/jquery-ui-1.10.4.min.js',
            'filersets/js/filersets_admin.js'
        ]

    class Meta:
        model = FilemodelExt
        widgets = {
            'category': SelectMultiple(attrs={'size': '9'}),
        }


class FilemodelExtInline(admin.StackedInline):
    form = FilemodelExtForm
    model = FilemodelExt
    extra = 0
    max_num = 1
    can_delete = False

ImageAdmin.inlines = ItemAdmin.inlines + [FilemodelExtInline]

# ______________________________________________________________________________
#                                                                   Registration
admin.site.register(Set, SetAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Affiliate, AffiliateAdmin)
