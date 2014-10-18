# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.db import models
from django.utils.translation import ugettext_lazy as _


class SetItemSort(models.Model):
    """Stores the sort position for each item in a particular set."""
    class Meta:
        app_label = 'filersets'
        verbose_name = _('item sort in sets')
        verbose_name_plural = _('item sort in sets')
        unique_together = ('item', 'set', 'sort',)
        ordering = ('sort', 'item', 'set')

    item = models.OneToOneField(
        'Item',
        verbose_name=_('item'),
        related_name='item_sort',
        blank=False,
        null=False,
        default=None)

    set = models.ForeignKey(
        'Set',
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