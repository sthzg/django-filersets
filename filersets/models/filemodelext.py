# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _
from filer.fields.file import FilerFileField

try:
    from taggit_autosuggest_select2.managers import TaggableManager
except ImportError:
    from taggit.managers import TaggableManager


class FilemodelExt(models.Model):
    """Deprecated: Functionality will be part of separate filerstream app."""
    class Meta:
        app_label = 'filersets'
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
        """Provides assigned tags in compatible format for DRF serializer."""
        return self.tags.values_list('name', flat=True)

    def __unicode__(self):
        return u'{}'.format(self.filer_file)