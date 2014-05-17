# -*- coding: utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Python
import inspect
import logging
# ______________________________________________________________________________
#                                                                         Django
from django.db import models
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from django.contrib.contenttypes.models import ContentType
# ______________________________________________________________________________
#                                                                        Contrib
from model_utils.choices import Choices
from autoslug import AutoSlugField
from filer.models import File
from filer.fields.file import FilerFileField
from filer.fields.folder import FilerFolderField
from treebeard.mp_tree import MP_Node, MP_NodeManager
# from taggit.managers import TaggableManager
from taggit_autosuggest_select2.managers import TaggableManager

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
        verbose_name = _('Filer Set')
        verbose_name_plural = _('Filer Sets')

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
        ('filer_file__modified_at', _('modfied date ascending')),
        ('-filer_file__modified_at', _('modified date descending')),
    )

    STATUS_OPTIONS = Choices(
        ('unpublished', _('unpublished')),
        ('published', _('published')),
    )

    status = models.CharField(
        _('Status'),
        choices=STATUS_OPTIONS,
        max_length=15,
        blank=True,
        default='unpublished',
        null=False
    )

    date = models.DateField(
        _('Date'),
        blank=True,
        default=None,
    )

    ordering = models.CharField(
        _('Ordering rule'),
        max_length=50,
        blank=True,
        choices=ORDERING_OPTIONS,
        default='filer_file__original_filename',
        null=True
    )

    title = models.CharField(
        _('Title'),
        max_length=60,
        blank=False,
        default=None
    )

    slug = AutoSlugField(
        _('Slug'),
        always_update=True,
        max_length=80,
        blank=True,
        default=None,
        populate_from='title'
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        default=None
    )

    folder = FilerFolderField(
        verbose_name=_('Set folders'),
        help_text=_('Choose the directory you wish to have integrated into '
                    'the current set.')
    )

    recursive = models.BooleanField(
        verbose_name=_('Include sub-folders?'),
        help_text=_('If checked, items from all subfolders will be included '
                    'into the set as well.'),
        blank=True,
        default=False,
        null=False
    )

    category = models.ManyToManyField(
        'Category',
        verbose_name=_('Category'),
        related_name='category_set',
        help_text=_('Assign the set to as many categories as you like'),
        blank=True,
        default=None,
        null=True
    )

    # Sets are not directly available for displaying when they are saved. First
    # a task needs to process all the items and after success sets flag to True
    is_processed = models.BooleanField(
        _('Is processed?'),
        null=False,
        blank=True,
        default=False
    )

    def create_or_update_set(self):
        """
        Creates or updates the items in this filerset.
        """
        logsig = str(inspect.stack()[0][3]) + '() '

        if self.recursive:
            folder_ids = self.folder.get_descendants(include_self=True)
            filter_query = {'folder_id__in': [f.id for f in folder_ids]}
        else:
            filter_query = {'folder_id': self.folder.id}

        op_stats = dict({'added': list(), 'updated': list(), 'noop': list()})
        for f in File.objects.filter(**filter_query):
            # Check if there is an item already
            try:
                # Update routine
                # TODO  Find orphanes and act
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

                msg = '{}File {} saved for Set {}'
                op_stats['added'].append(msg.format('', f.id, self.pk))
                logger.info(msg.format(logsig, f.id, self.pk))

        return op_stats

    def save(self, *args, **kwargs):
        super(Set, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{}'.format(self.title)

# ______________________________________________________________________________
#                                                                    Model: Item
class Item(TimeStampedModel):
    """ The item model holds items that are contained within a Set. """
    # TODO: Mark the combination of `set` and `filer_file` as unique

    set = models.ForeignKey(
        'Set',
        verbose_name=_('Belongs to set'),
        related_name='filer_set',
        null=False,
        default=None,
        blank=None
    )

    # TODO:   Name the content type field as suggested in the django docs
    ct = models.ForeignKey(
        ContentType,
        verbose_name=_('Content type'),
        related_name='contenttype',
        null=False,
        default=None,
        blank=False
    )

    is_cover = models.BooleanField(
        _('Cover item?'),
        null=False,
        blank=True,
        default=False
    )

    category = models.ManyToManyField(
        'Category',
        verbose_name=_('Category'),
        related_name='item_category',
        help_text=_('Assign the set to as many categories as you like'),
        blank=True,
        default=None,
        null=True
    )

    filer_file = FilerFileField(
        related_name='filer_file_obj',
        verbose_name=_('Filer file'),
        null=True,
        default=None,
        blank=True
    )

    title = models.CharField(
        _('title'),
        help_text=_('Note that django-filersets provides you with various '
                    'ways to author title and description for items. Please '
                    'see the help for more information and examples.'),
        max_length=150,
        blank=True,
        default=None,
        null=True
    )

    description = models.TextField(
        _('description'),
        blank=True,
        default=None,
        null=True
    )

    tags = TaggableManager(
        blank=True
    )

    is_timeline = models.BooleanField(
        _('on timeline?'),
        help_text=_('This field indicates whether the item is displayed on '
                    'a timeline view.'),
        blank=True,
        default=False,
        null=False
    )

    is_locked = models.BooleanField(
        _('locked'),
        help_text=_('Reprocessing a set searches for and deletes files that '
                    'are not/no longer contained within the root folder. Check '
                    'locked if you wish to keep this file as part of the '
                    'set even though it is reported as an orphan.'),
        blank=False,
        default=False,
        null=False
    )

    def save(self, *args, **kwargs):

        if not self.ct_id:
            self.ct_id = ContentType.objects.get(
                pk=self.filer_file.polymorphic_ctype_id).id

        super(Item, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{}'.format(self.filer_file.original_filename)
        # return u'Set: {}'.format(self.set.title)


# ______________________________________________________________________________
#                                                                Model: Category
class Category(MP_Node):

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    objects = CategoryManager()

    is_active = models.BooleanField(
        _('Is active?'),
        null=False,
        default=False,
        blank=True
    )

    name = models.CharField(
        _('Category name'),
        max_length=140,
        blank=False,
        default=None
    )

    slug = AutoSlugField(
        _('Slug'),
        always_update=True,
        max_length=80,
        blank=True,
        default=None,
        populate_from='name'
    )

    slug_composed = models.CharField(
        _('Composed slug'),
        unique=True,
        max_length=150,
        blank=True,
        default=None,
        null=True
    )

    description = models.TextField(
        _('Description'),
        blank=True,
        default=None,
        null=True
    )

    parent = models.ForeignKey(
        'self',
        verbose_name=_('parent'),
        related_name='cat_parent',
        blank=True,
        null=True,
        default=None
    )

    def number_of_sets(self):
        """ returns the number of sets contained in current category """
        return Set.objects.filter(category=self, status='published').count()

    def get_level_compensation(self, compensate_to=None):
        """ returns the offset to the root level as int """
        # TODO  Implement compensate_to functionality
        return self.get_depth() - 1

    def save(self, *args, **kwargs):

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

    def __unicode__(self):
        return u'{}'.format(self.name)


# ______________________________________________________________________________
#                                                              Model: Membership
class Affiliate(models.Model):
    """
    Configure categories that belong to certain logical entities of filersets

    With affiliates you can configure categories that belong to certain
    logical entities of filersets. For example, if you use filersets for the two
    areas image galleries and downloads then you do not want to show sets
    belonging to the downloads in a list view of the image galleries.

    Currently we assume that those two areas are presented through different
    django namespaces:
    https://docs.djangoproject.com/en/1.6/topics/http/urls/#url-namespaces
    """

    class Meta:
        verbose_name=_('affiliated categories')
        verbose_name_plural=_('affiliated categories')

    label = models.CharField(
        _('label'),
        help_text=_('The label is shown as internal description in widgets.'),
        max_length=30,
        blank=False,
        default=None,
        null=False
    )

    namespace = models.CharField(
        _('namespace'),
        help_text=_('Enter the namespace that will be associated with this '
                    'particular affiliate.'),
        max_length=30,
        blank=True,
        default=None,
        null=True
    )

    memo = models.TextField(
        _('internal memo'),
        help_text=_('You could use this field to lave some information for '
                    'yourself or co-workers.'),
        blank=True,
        default=None,
        null=True
    )

    category = models.ManyToManyField(
        Category,
        verbose_name=_('categories'),
        related_name='affiliate_categories',
        help_text=_('Pick the category/ies you wish to include in list '
                    'displays of filersets associated with this affiliate.'),
        blank=True,
        default=None,
        null=True
    )

    def __unicode__(self):
        return u'{}'.format(self.label)