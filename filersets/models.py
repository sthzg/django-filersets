# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from django.contrib.contenttypes.models import ContentType
from filer.models import Folder
from mptt.fields import TreeManyToManyField, TreeForeignKey
from mptt.models import MPTTModel
from autoslug import AutoSlugField
from filer.fields.file import FilerFileField


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


    date = models.DateField(
        _('Set date'),
        blank=True,
        default=None,
    )

    title = models.CharField(
        _('Set title'),
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
