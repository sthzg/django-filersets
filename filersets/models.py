# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import inspect
import logging
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, post_delete
from django_extensions.db.models import TimeStampedModel
from django.utils.datetime_safe import datetime
from django.utils.translation import ugettext_lazy as _, ugettext
from autoslug import AutoSlugField
from easy_thumbnails.files import get_thumbnailer
from filersets.fields import TreeManyToManyField
from model_utils.choices import Choices
from treebeard.mp_tree import MP_Node, MP_NodeManager
from filersets.signals import fset_processed
from filer.fields.file import FilerFileField
from filer.fields.folder import FilerFolderField
from filer.models import File, Image

try:
    from taggit_autosuggest_select2.managers import TaggableManager
except ImportError:
    from taggit.managers import TaggableManager


logger = logging.getLogger(__name__)


# ______________________________________________________________________________
#                                                                   Manager: Set
class SetManager(models.Manager):
    def create_or_update_all_sets(self):
        """
        Creates or updates all filersets.
        """
        # TODO  Write it

        logsig = str(inspect.stack()[0][3]) + '() '


# ______________________________________________________________________________
#                                                              Manager: Category
class CategoryManager(MP_NodeManager):
    def get_categories_by_level(self, level_start=0, depth=0, skip_empty=False):
        """ Retreive a queryset with categories

        :param level_start: defines at which level to start
        :param depth: defines how many child levels to deliver (0 = All)
        :param skip_empty: flag, deliver categories without entries or not
        :rtype: queryset
        """
        q_filter = dict()
        q_filter.update({'is_active': True})
        q_filter.update({'depth__gte': level_start})

        if depth > int(0):
            q_filter.update({'depth__lt': level_start + depth})

        if skip_empty:
            q_filter.update({'num_sets__gt': 0})

        qs = self.annotate(num_sets=Count('category_set')).filter(**q_filter)

        return qs


# ______________________________________________________________________________
#                                                                     Model: Set
class Set(TimeStampedModel):
    """
    The Set model is a thin wrapper around one ore more django filer folders.
    It allows creating filer sets with various meta data.

    TODO    Make this model pluggable, maybe abstract
    TODO    Make a generic categorisation layer that allows to configure
            which model should be used to display available categories
    """

    class Meta:
        verbose_name = _('filer set')
        verbose_name_plural = _('filer sets')

    objects = SetManager()

    ORDERING_OPTIONS = Choices(
        ('filer_file__original_filename', _('filename ascending')),
        ('-filer_file__original_filename', _('filename descending')),
        ('filer_file__name', _('title in filer ascending')),
        ('-filer_file__name', _('title in filer descending')),
        ('title', _('title in set ascending')),
        ('-title', _('title in set descending')),
        ('filer_file__uploaded_at', _('upload date ascending')),
        ('-filer_file__uploaded_at', _('upload date descending')),
        ('filer_file__modified_at', _('modified date ascending')),
        ('-filer_file__modified_at', _('modified date descending')),
        ('custom', _('custom sort order')), )

    STATUS_OPTIONS = Choices(
        ('unpublished', _('unpublished')),
        ('published', _('published')), )

    settype = models.ForeignKey(
        'Settype',
        verbose_name=_('set type'),
        related_name='settype_set',
        blank=True,
        null=False,
        default=1)

    status = models.CharField(
        _('status'),
        choices=STATUS_OPTIONS,
        max_length=15,
        blank=True,
        default='unpublished',
        null=False)

    date = models.DateField(
        _('date'),
        blank=True,
        null=False,
        default=datetime.now())

    ordering = models.CharField(
        _('ordering rule'),
        help_text=_('Select the file attribute you wish to be respected for '
                    'order of display. Once you start reordering media by '
                    'drag and drop this value will be automatically set '
                    'to custom sort order.'),
        max_length=50,
        blank=True,
        choices=ORDERING_OPTIONS,
        default='filer_file__original_filename',
        null=True)

    title = models.CharField(
        _('title'),
        max_length=60,
        blank=False,
        default=None)

    slug = AutoSlugField(
        _('slug'),
        always_update=True,
        max_length=80,
        blank=True,
        default=None,
        populate_from='title')

    description = models.TextField(
        _('description'),
        blank=True,
        default=None,
        null=True)

    folder = FilerFolderField(
        verbose_name=_('set folders'),
        help_text=_('Choose the directory you wish to have integrated into '
                    'the current set.'))

    recursive = models.BooleanField(
        verbose_name=_('include sub-folders?'),
        help_text=_('If checked, items from all subfolders will be included '
                    'into the set as well.'),
        blank=True,
        default=False,
        null=False)

    is_autoupdate = models.BooleanField(
        _('autoupdate?'),
        help_text=_('If autoupdate is activated, new files uploaded to '
                    'the folder will be automatically added, deleted files '
                    'automatically removed from the set. If you leave this '
                    'setting off you can update a set manually by clicking '
                    'the process set button on the list or edit page.'),
        blank=False,
        default=False,
        null=False)

    category = TreeManyToManyField(
        'Category',
        verbose_name=_('category'),
        related_name='category_set',
        help_text=_('Assign the set to as many categories as you like'),
        blank=True,
        default=None,
        null=True)

    # Sets are not directly available for displaying when they are saved. First
    # a task needs to process all the items and after success sets flag to True
    is_processed = models.BooleanField(
        _('processed?'),
        null=False,
        blank=True,
        default=False
    )

    #                                                          _________________
    #                                                          Create/Update Set
    def create_or_update_set(self):
        """
        Creates items and removes orphans in the current set.

        In general the items contained within a set derive from the files
        listed in one or more filer folders. This method checks all files
        in the relevant folders and creates an Item object connected to
        the set.

        When files that were previously included in a folder are no longer
        found present, they get deleted from the set, unless their ``is_locked``
        flag is set to True.
        """
        # TODO  Solution for edge case, when is_locked item's file is deleted

        logsig = str(inspect.stack()[0][3]) + '() '

        if self.recursive:
            folder_ids = self.folder.get_descendants(include_self=True)
            filter_query = {'folder_id__in': [f.id for f in folder_ids]}
        else:
            filter_query = {'folder_id': self.folder.id}

        op_stats = dict({'added': [], 'updated': [], 'removed': [], 'noop': []})

        #                                                                    ___
        #                                                         Remove Orphans
        files_in_db = [it.filer_file.id for it
                       in Item.objects.filter(set=self, is_locked=False)]

        files_in_folders = [f.id for f in File.objects.filter(**filter_query)]

        diff = set(files_in_db) - set(files_in_folders)
        for item in Item.objects.filter(filer_file__id__in=list(diff)):
            item.delete()
            msg = 'Deleted item {}, {} from set.'
            msg = msg.format(item.pk, item.filer_file.original_filename)
            op_stats['removed'].append(msg)

        #                                                                    ___
        #                                                           Create Items
        for f in File.objects.filter(**filter_query):

            # Only create if it does not already exist
            try:
                Item.objects.get(set=self.pk, filer_file__id=f.id)

                msg = '{}File {} in Set {} already exists'
                op_stats['noop'].append(msg.format('', f.id, self.pk))
                logger.info(msg.format(logsig, f.id, self.pk))

            except ObjectDoesNotExist:
                # Creation routine
                item = Item()
                item.set = self
                item.ct = ContentType.objects.get(pk=f.polymorphic_ctype_id)
                item.filer_file = f
                item.save()

                # SetItemSort
                set_item_sort = SetItemSort()
                set_item_sort.item = item
                set_item_sort.set = self
                set_item_sort.sort = SetItemSort.objects.filter(set=self).count()
                set_item_sort.save()

                msg = '{}File {} saved for Set {}'
                op_stats['added'].append(msg.format('', f.id, self.pk))
                logger.info(msg.format(logsig, f.id, self.pk))

        self.save_item_sort()
        self.is_processed = True
        self.save()

        fset_processed.send(sender=self.__class__, fset=self)

        return op_stats

    #                                                            _______________
    #                                                            Sorting Methods
    def get_items_sorted(self):
        """
        Returns a list of items in current sorting order.
        """
        return [item.item
                for item in SetItemSort.objects.filter(set=self)
                                               .order_by('sort')]

    def get_items_sorted_pks_serialized(self):
        """
        Returns a serialized string with sorted itempks for use in GET queries.
        """
        items = self.get_items_sorted()
        ret = []
        for item in items:
            ret.append('itempk[]={}'.format(item.pk))

        return "&".join(ret)

    def get_set_type(self):
        """
        Returns the set type that this filerset belongs to.
        """
        return self.category.first().get_root()

    def get_set_type_slug(self):
        """
        Returns the slug of the set type that this filerset belongs to.
        """
        return self.category.first().get_root().slug

    def save_item_sort(self, custom=None):
        """
        Traverses all items on the set and saves their sort position.
        """

        sort_by = self.ordering

        if sort_by == 'custom' and custom is None:
            # When the user wants custom sorting and the set is initially saved
            # with custom as its ordering option then create the initial sort
            # positions in exactly the ordering that is currently set.
            sort_by = ''

        elif sort_by == 'custom':
            items = list()
            objects = Item.objects.in_bulk(custom)
            sorted_objects = [objects[id] for id in custom]
            for idx, item in enumerate(sorted_objects):

                try:
                    sort_obj = SetItemSort.objects.get(set=self, item=item)
                except SetItemSort.DoesNotExist:
                    sort_obj = SetItemSort()

                sort_obj.set = self
                sort_obj.item = item
                sort_obj.sort = idx

                # Delaying save() to avoid unique constraint exceptions.
                items.append(sort_obj)

        else:
            items = list()
            for idx, item in enumerate(
                    Item.objects.filter(set=self).order_by(sort_by)):

                try:
                    sort_obj = SetItemSort.objects.get(set=self, item=item)
                except SetItemSort.DoesNotExist:
                    sort_obj = SetItemSort()

                sort_obj.set = self
                sort_obj.item = item
                sort_obj.sort = idx

                # delaying save() to avoid unique constraint exceptions
                items.append(sort_obj)

        try:
            for item in items:
                item.save()
        except:
            pass

    def save(self, *args, **kwargs):
        super(Set, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{}'.format(self.title)


# ______________________________________________________________________________
#                                                                    Model: Item
class Item(TimeStampedModel):
    """
    The item model holds items that are contained within a Set.
    """

    class Meta:
        verbose_name = _('item')
        verbose_name_plural = _('items')
        ordering = ('item_sort__sort',)

    set = models.ForeignKey(
        'Set',
        verbose_name=_('Belongs to set'),
        related_name='filer_set',
        null=False,
        default=None,
        blank=None)

    # TODO:   Name the content type field as suggested in the django docs
    ct = models.ForeignKey(
        ContentType,
        verbose_name=_('content type'),
        related_name='contenttype',
        null=False,
        default=None,
        blank=False)

    is_cover = models.BooleanField(
        _('cover item?'),
        null=False,
        blank=True,
        default=False)

    filer_file = FilerFileField(
        related_name='filer_file_obj',
        verbose_name=_('Filer file'),
        null=True,
        default=None,
        blank=True)

    title = models.CharField(
        _('title'),
        help_text=_('Note that django-filersets provides you with various '
                    'ways to author title and description for items. Please '
                    'see the help for more information and examples.'),
        max_length=150,
        blank=True,
        default=None,
        null=True)

    description = models.TextField(
        _('description'),
        blank=True,
        default=None,
        null=True)

    is_locked = models.BooleanField(
        _('locked?'),
        help_text=_('Reprocessing a set searches for and deletes files that '
                    'are not/no longer contained within the root folder. Check '
                    'locked if you wish to keep this file as part of the '
                    'set even though it is reported as an orphan.'),
        blank=False,
        default=False,
        null=False)

    #                                                                        ___
    #                                                             get_item_thumb
    def get_item_thumb(self):
        """
        Return a thumbnail representation of the current item.
        """
        if self.filer_file.polymorphic_ctype.name == 'image':
            admin_link = self.filer_file.get_admin_url_path()
            options = {'size': (100, 100), 'crop': True}
            thumb_url = get_thumbnailer(
                self.filer_file.file).get_thumbnail(options).url
            output = '<img class="fs_filepk" src="{}" data-filepk="{}">'
            output = output.format(thumb_url, self.filer_file.id)
            output = '<a href="{}">{}</a>'.format(admin_link, output)
        else:
            output = '{}'.format(ugettext('Edit'))

        return output

    get_item_thumb.allow_tags = True
    get_item_thumb.short_description = 'Thumb'

    #                                                                        ___
    #                                                      get_original_filename
    def get_original_filename(self):
        """
        Return the original filename of the item.
        """
        return self.filer_file.original_filename

    get_original_filename.short_description = 'filename'
    get_original_filename.allow_tags = True

    #                                                                        ___
    #                                                          get_sort_position
    def get_sort_position(self):
        """
        Return 0-based sort position of the item.
        """
        return self.item_sort.sort

    get_sort_position.short_description = 'Pos'

    #                                                                        ___
    #                                                                is_timeline
    def is_timeline(self):
        """
        Check is_timeline flag on the file and return True or False.
        """
        is_timeline = False
        try:
            is_timeline = self.filer_file.filemodelext_file.all()[0].is_timeline
        except IndexError:
            pass
        return is_timeline

    #                                                                        ___
    #                                                            get_is_timeline
    def get_is_timeline(self):
        """
        Render green check or red x according to is_timeline flag.
        """
        yesno = 'check-circle' if self.is_timeline() else 'times-circle'
        output = '<i class="fs_is-timeline-indicator fa fa-{}"></i>'
        return output.format(yesno)

    get_is_timeline.allow_tags = True
    get_is_timeline.short_description = _('Tl.?')

    #                                                                        ___
    #                                                                       save
    def save(self, *args, **kwargs):
        if not self.ct_id:
            self.ct_id = ContentType.objects.get(
                pk=self.filer_file.polymorphic_ctype_id).id

        super(Item, self).save(*args, **kwargs)

    #                                                                        ___
    #                                                                    unicode
    def __unicode__(self):
        return u'{}'.format(self.filer_file.original_filename)
        # return u'Set: {}'.format(self.set.title)


# ______________________________________________________________________________
#                                                             Model: SetItemSort
class SetItemSort(models.Model):
    """
    Stores the sort position for each item in a particular set.
    """

    class Meta:
        verbose_name = _('item sort in sets')
        verbose_name_plural = _('item sort in sets')
        unique_together = ('item', 'set', 'sort',)
        ordering = ('sort', 'item', 'set')

    item = models.OneToOneField(
        Item,
        verbose_name=_('item'),
        related_name='item_sort',
        blank=False,
        null=False,
        default=None)

    set = models.ForeignKey(
        Set,
        verbose_name=_('set'),
        related_name='set_sort',
        blank=False,
        null=False,
        default=None)

    sort = models.PositiveIntegerField(
        _('sort'),
        blank=False,
        null=True,
        default=None)

    def __unicode__(self):
        msg = u'Item {} on position {} in set {}'
        return msg.format(self.item.id, self.sort, self.set.id)


# ______________________________________________________________________________
#                                                                Model: Category
class Category(MP_Node):
    """

    """
    # TODO Docstring.
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    objects = CategoryManager()

    created = models.DateTimeField(
        _('created'),
        auto_now_add=True)

    last_modified = models.DateTimeField(
        _('updated'),
        auto_now=True)

    is_active = models.BooleanField(
        _('is active?'),
        null=False,
        default=False,
        blank=True)

    name = models.CharField(
        _('category name'),
        max_length=140,
        blank=False,
        default=None)

    slug = AutoSlugField(
        _('slug'),
        always_update=True,
        max_length=80,
        blank=True,
        default=None,
        populate_from='name')

    slug_composed = models.CharField(
        _('composed slug'),
        unique=True,
        max_length=150,
        blank=True,
        default=None,
        null=True)

    description = models.TextField(
        _('description'),
        blank=True,
        default=None,
        null=True)

    parent = models.ForeignKey(
        'self',
        verbose_name=_('parent'),
        related_name='cat_parent',
        blank=True,
        null=True,
        default=None)

    def number_of_sets(self):
        """
        Returns the number of sets contained in current category
        """
        return Set.objects.filter(category=self, status='published').count()

    def get_level_compensation(self, compensate_to=None):
        """
        Returns the offset to the root level as int
        """
        # TODO  Implement compensate_to functionality
        return self.get_depth() - 1

    def save(self, *args, **kwargs):
        """
        Overriding save to provide a category slug.
        """
        super(Category, self).save(*args, **kwargs)

        # Providing a composed slug keeps the cost of lookups for category urls
        # low during runtime, since it only has to check against one string.
        current_token = [self.slug]
        ancestor_tokens = [res.slug for res in self.get_ancestors()]
        composed_list = ancestor_tokens + current_token

        self.slug_composed = '{}/'.format('/'.join(composed_list))

        super(Category, self).save(*args, **kwargs)

        for child in self.get_children():
            child.save(force_update=True)


    @classmethod
    def on_category_pre_delete(cls, sender, instance, using, **kwargs):
        # Uses pre_delete to check if user deletes a root category, which
        # equals deleting a settype. If so prepares an attribute that can
        # be used on ``post_delete`` to remove the settype. (otherwise
        # we end up in an infinite loop).
        if instance.is_root():
            instance.delete_settype = instance.settype_categories.first()

    @classmethod
    def on_category_post_delete(cls, sender, instance, using, **kwargs):
        # See comment above on method on_category_pre_delete.
        if hasattr(instance, 'delete_settype'):
            instance.delete_settype.delete()

    def __unicode__(self):
        return u'{}'.format(self.name)

pre_delete.connect(Category.on_category_pre_delete, sender=Category)
post_delete.connect(Category.on_category_post_delete, sender=Category)


# ______________________________________________________________________________
#                                                                 Model: Settype
class Settype(models.Model):
    """
    Enables users to configure different types of sets, like galleries,
    downloads, etc.

    With set types you can configure categories that belong to certain
    logical entities of filersets. For example, if you use filersets for the two
    areas image galleries and downloads then you do not want to show sets
    belonging to the downloads in a list view of the image galleries.

    Currently we assume that those two areas are presented through different
    django namespaces:
    https://docs.djangoproject.com/en/1.6/topics/http/urls/#url-namespaces
    """
    class Meta:
        verbose_name = _('set type')
        verbose_name_plural = _('set types')

    created = models.DateTimeField(
        _('created'),
        auto_now_add=True)

    last_modified = models.DateTimeField(
        _('updated'),
        auto_now=True)

    label = models.CharField(
        _('label'),
        help_text=_('The label is shown as internal description in widgets.'),
        max_length=30,
        blank=False,
        default=None,
        null=False)

    #: Additionally to defining the slug this value is used to build the
    #: instance namespace of this set type. See http://goo.gl/oIw0g1 for
    #: documentation on Django url namespaces.
    slug = AutoSlugField(
        _('slug'),
        always_update=True,
        max_length=80,
        blank=True,
        default=None,
        populate_from='label')

    base_folder = FilerFolderField(
        verbose_name=_('base folder'),
        help_text=_('All media for this set type should be uploaded to '
                    'child directories of this folder.'),
        blank=True,
        null=True,
        default=None)

    has_mediastream = models.BooleanField(
        _('provide stream'),
        help_text=_('Check this setting if you want to organize items '
                    'within this set type\'s base folder on a centralized '
                    'list page'),
        blank=False,
        null=False,
        default=False)

    memo = models.TextField(
        _('internal memo'),
        help_text=_('You could use this field to lave some information for '
                    'yourself or co-workers.'),
        blank=True,
        default=None,
        null=True)

    category = TreeManyToManyField(
        Category,
        verbose_name=_('categories'),
        related_name='settype_categories',
        help_text=_('Pick the category/ies you wish to include in list '
                    'displays of filersets associated with this set type.'),
        blank=True,
        default=None,
        null=True)

    #: Available template options can be configured in the project settings.
    #: This field holds a reference to the dictionary key or 'default'.
    template_conf = models.CharField(
        _('templates'),
        max_length=60,
        blank=True,
        null=False,
        default='default')

    def get_root_category(self):
        """
        Returns Category instance of connected root category.
        """
        return self.category.first()

    def save(self, *args, **kwargs):
        """
        Creates new Category instance on category root level and sets
        relation to the set.
        """
        update = True if self.pk else False

        super(Settype, self).save(*args, **kwargs)

        if update:
            category = self.category.all().first()
            category.name = '{}'.format(self.label)
            category.save()
        else:
            category = Category()
            category.name = '{}'.format(self.label)
            category.is_active = True
            Category.add_root(instance=category)

        self.category.clear()
        self.category.add(category)

    @classmethod
    def on_settype_delete(cls, sender, instance, using, **kwargs):
        """
        Deletes the root category and its descendants when a settype is deleted.
        """
        try:
            Category.delete(instance.category.all().first())
        except TypeError:
            if not instance.category.all().first():
                pass
            else:
                raise

    def __unicode__(self):
        return u'{}'.format(self.label)

pre_delete.connect(Settype.on_settype_delete, sender=Settype)


# ______________________________________________________________________________
#                                                            Model: FilemodelExt
class FilemodelExt(models.Model):
    """
    """
    # TODO Docstring.
    class Meta:
        verbose_name = _('file model extension')
        verbose_name_plural = _('file model extensions')

    filer_file = FilerFileField(
        related_name='filemodelext_file',
        verbose_name=_('Filer file'),
        null=False,
        default=None,
        blank=False,
        unique=True,
        primary_key=True)

    is_timeline = models.BooleanField(
        _('tl?'),
        help_text=_('This field indicates whether the file is displayed on '
                    'a timeline view.'),
        blank=True,
        default=False,
        null=False)

    category = models.ManyToManyField(
        'Category',
        verbose_name=_('Category'),
        related_name='filemodelext_category',
        help_text=_('Assign the file to as many categories as you like'),
        blank=True,
        default=None,
        null=True)

    tags = TaggableManager(blank=True)

    def get_tags_display(self):
        """
        Provides assigned tags in compatible format for DRF serializer.
        """
        return self.tags.values_list('name', flat=True)

    def __unicode__(self):
        return u'{}'.format(self.filer_file)


# ______________________________________________________________________________
#                                                               Signal Listeners
@receiver(post_save, sender=Image)
def filersets_post_save_file(sender, **kwargs):
    instance = kwargs.get('instance')

    # The post_save() signal causes troubles when the instance is saved from
    # a fixture. We use the raw flag to check if this is the case.
    if kwargs.get('raw', True):
        return

    #                                                                        ___
    #                                                               FilemodelExt
    try:
        FilemodelExt.objects.get(filer_file=instance)
    except FilemodelExt.DoesNotExist:
        filemodelext = FilemodelExt()
        filemodelext.filer_file = instance
        filemodelext.save()

    #                                                                        ___
    #                                                                 autoupdate
    if not instance.folder:
        return

    folders = instance.folder.get_ancestors(include_self=True)
    fsets = Set.objects.filter(folder__in=folders)

    for fset in fsets:
        if fset.is_autoupdate:
            fset.create_or_update_set()