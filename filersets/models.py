# -*- coding: utf-8 -*-
from __future__ import absolute_import
import inspect
import logging
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from django.contrib.contenttypes.models import ContentType
from mptt.fields import TreeManyToManyField, TreeForeignKey
from mptt.models import MPTTModel
from filer.models import Folder
from autoslug import AutoSlugField
from filer.models import File
from filer.fields.file import FilerFileField

logger = logging.getLogger(__name__)

class SetManager(models.Manager):
    def create_or_update_set(self, set_id=None):
        """ Creates or updates filersets

        If ``set_id``is not given, all sets are created/updated. You can pass
        either no value for ``set_id``, a single IDs or a list of IDs.

        :param set_id: Single ID as int, multiple IDs as list or None (= All)
        """

        logsig = str(inspect.stack()[0][3]) + '() '
        
        # Param handling for set_id, because it can take None, int and list
        if not set_id:
            filter_query = {}

        elif isinstance(set_id, int):
            filter_query = {'pk': set_id}

        elif isinstance(set_id, list):
            filter_query = {'pk__in': set_id}

        else:
            # TODO Raise exception
            return

        op_stats = dict({'added': list(), 'updated': list(), 'noop': list()})
        for filerset in Set.objects.filter(**filter_query):

            folder_ids = [folder.id for folder in filerset.set_root.all()]

            for f in File.objects.filter(folder_id__in=folder_ids):

                # Check if there is an item already
                try:
                    # Update routine
                    # TODO  Find orphanes and act
                    Item.objects.get(set=filerset.pk, filer_file__id=f.id)

                    msg = '{}File {} in Set {} already exists'
                    op_stats['noop'].append(msg.format('', f.id, filerset.id))
                    logger.info(msg.format(logsig, f.id, set_id))

                except ObjectDoesNotExist:
                    # Creation routine
                    item = Item()
                    item.set = filerset
                    item.ct = ContentType.objects.get(pk=f.polymorphic_ctype_id)
                    item.filer_file = f
                    item.order = 1
                    item.save()

                    msg = '{}File {} saved for Set {}'
                    op_stats['added'].append(msg.format('', f.id, filerset.id))
                    logger.info(msg.format(logsig, f.id, set_id))

            filerset.is_processed = True
            filerset.save()

        return op_stats


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

    date = models.DateField(
        _('Date'),
        blank=True,
        default=None,
    )

    title = models.CharField(
        _('Title'),
        max_length=60,
        blank=False,
        default=None
    )

    slug = AutoSlugField(
        _('Slug'),
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

    set_root = TreeManyToManyField(
        Folder,
        verbose_name=_('Set folders'),
        help_text=_('Choose the directories you wish to have integrated into '
                    'the current set.')
    )

    # Sets are not directly available for displaying when they are saved. First
    # a task needs to process all the items and after success sets flag to True
    is_processed = models.BooleanField(
        _('Is processed?'),
        null=False,
        blank=True,
        default=False
    )

    def __unicode__(self):
        return self.title


class Item(MPTTModel):
    """
    The item model holds items that are contained within a Set.

    TODO: Mark the combination of ``set`` and ``filer_file`` as unique
    """

    set = models.ForeignKey(
        'Set',
        verbose_name=_('Belongs to set'),
        related_name='filer_set',
        null=False,
        default=None,
        blank=None
    )

    # TODO:   Name the content type field as suggestedin the django docs
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

    filer_file = FilerFileField(
        related_name='filer_file_obj',
        verbose_name=_('Filer file'),
        null=True,
        default=None,
        blank=True
    )

    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children'
    )

    order = models.PositiveIntegerField(_('Order'))

    class MPTTMeta:
        order_inseration_by = ['order']

    def save(self, *args, **kwargs):
        super(Item, self).save(*args, **kwargs)
        Item.objects.rebuild()

    def __unicode__(self):
        return 'Set: {}'.format(self.set.title)
