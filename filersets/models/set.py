# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import inspect
import logging
from autoslug import AutoSlugField
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.utils.datetime_safe import datetime
from django.utils.translation import ugettext_lazy as _
from model_utils.choices import Choices
from filer.fields.folder import FilerFolderField
from filer.models import File
from filersets.fields import TreeManyToManyField
from filersets.signals import fset_processed
from .item import Item
from .setitemsort import SetItemSort
from .settype import Settype

try:
    from taggit_autosuggest_select2.managers import TaggableManager
except ImportError:
    from taggit.managers import TaggableManager


logger = logging.getLogger(__name__)


class SetManager(models.Manager):
    def create_or_update_all_sets(self):
        """Creates or updates all filersets."""
        # TODO  Write it

        logsig = str(inspect.stack()[0][3]) + '() '


class Set(TimeStampedModel):
    """A thin wrapper around one ore more django filer folders."""
    class Meta:
        app_label = 'filersets'
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
        help_text=_('If checked, items from all sub folders will be included '
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
        """Creates items and removes orphans in the current set.

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

    def get_items_sorted(self):
        """Returns a list of items in current sorting order."""
        return [item.item
                for item in SetItemSort.objects.filter(set=self)
                                               .order_by('sort')]

    def get_items_sorted_pks_serialized(self):
        """Returns a serialized string w/ sorted pks for use in GET queries."""
        items = self.get_items_sorted()
        ret = []
        for item in items:
            ret.append('itempk[]={}'.format(item.pk))

        return "&".join(ret)

    def get_set_type(self):
        """Returns the set type that this filerset belongs to."""
        return self.category.first().get_root()

    def get_set_type_slug(self):
        """Returns the slug of the set type that this filerset belongs to."""
        return self.category.first().get_root().slug

    def get_categories(self):
        """Returns a list of ``Category`` instances assigned to this set."""
        return self.category.filter(is_active=True).order_by('name')


    def save_item_sort(self, custom=None):
        """Traverses all items on the set and saves their sort position."""
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
        # Make sure we have a date if user clears value in DateTimeField.
        if not self.date:
            self.date = datetime.now()

        try:
            self.settype
        except Settype.DoesNotExist:
            self.settype = Settype.objects.all().first()

        super(Set, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{}'.format(self.title)