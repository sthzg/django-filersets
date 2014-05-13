# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Django
from django.contrib import admin
from django.forms.models import ModelForm
from django.forms.widgets import SelectMultiple
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ugettext
# ______________________________________________________________________________
#                                                                        Contrib
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from easy_thumbnails.files import get_thumbnailer
# ______________________________________________________________________________
#                                                                         Custom
from filersets.models import Set, Item, Category, Affiliate
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
        fields = ('filer_file', 'title', 'description', 'is_cover', 'is_locked',)
        list_editable = ('description', 'is_cover',)
        list_display = ('title', 'is_cover', 'description', 'is_cover',)
        list_display_links = ('title',)
        model = Item
        extra = 0
        list_per_page = 30

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
        fields = ('filer_file', 'title', 'description', 'is_cover', 'is_locked',)
        list_editable = ('description', 'is_cover',)
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
        """ Provide additional static files for the set admin """
        css = {'all': ('filersets/css/filersets_admin.css',)}

    form = ItemForm
    list_display = ('item_thumb', 'set_admin_link', 'current_categories', 'title', 'description', 'created',)
    list_editable = ('title', 'description',)
    list_filter = ('set', 'is_cover', 'category', 'created', 'modified',)
    list_display_links = ('item_thumb',)
    fields = ('filer_file', 'title', 'description', 'category',)
    filter_horizontal = ('category',)
    search_fields = ('filer_file__file', 'title', 'set__title')
    list_per_page = 25

    def item_thumb(self, obj):
        """
        Return a thumbnail represenation of the current item.
        """
        if obj.filer_file.polymorphic_ctype.name == 'image':
            options = {'size': (50,50), 'crop': True}
            thumb_url = get_thumbnailer(
                obj.filer_file.file).get_thumbnail(options).url
            output = '<img src="{}">'.format(thumb_url)
        else:
            output = '{}'.format(ugettext('Edit'))

        return output

    def set_admin_link(self, obj):
        """
        Return a link to th admin change page of the set
        """
        url = reverse('admin:filersets_set_change', args={(obj.set.pk)})
        link = '<a href="{}">{}</a>'
        return link.format(url, obj.set.title)

    def current_categories(self, obj):
        """
        Return a string of currently assign categories to one item.
        """
        try:
            cats = u', '.join([cat.name for cat in obj.category.all()])
        except TypeError:
            cats = _(u'None')
        return cats

    def get_changelist_form(self, request, **kwargs):
        """
        Alter change list to use custom widgets
        """
        kwargs.setdefault('form', ItemForm)
        return super(ItemAdmin, self).get_changelist_form(request, **kwargs)

    item_thumb.short_description = _('Item')
    item_thumb.allow_tags = True
    set_admin_link.short_description = _('Set')
    set_admin_link.allow_tags = True


# ______________________________________________________________________________
#                                                                 ModelForm: Set
class SetForm(ModelForm):
    class Meta:
        model = Set
        widgets = {'category': SelectMultiple(attrs={'size': '12'})}


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
    list_filter = ('date', 'is_processed', 'status',)
    list_display = ('title', 'date', 'status', 'is_processed', 'watch_online',
                    'process_set',)
    list_editable = ('status',)


# ______________________________________________________________________________
#                                                         InlineAdmin: Affiliate
class AffiliateInlineAdmin(admin.StackedInline):
    """ Adds affiliate settings as inline to category admin """
    model = Affiliate.category.through
    extra = 0


# ______________________________________________________________________________
#                                                               Admin: Affiliate
class AffiliateAdmin(admin.ModelAdmin):
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
    list_display = ('name', 'slug', 'is_active',)

    list_display = ('name', 'number_of_sets', 'slug',
                    'is_active',)
    list_editable = ('is_active',)
    exclude = ('slug_composed', 'path', 'depth', 'numchild', 'parent',)
    inlines = [AffiliateInlineAdmin]


# ______________________________________________________________________________
#                                                                   Registration
admin.site.register(Set, SetAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Affiliate, AffiliateAdmin)
