# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext
from easy_thumbnails.files import get_thumbnailer
from filer.fields.file import FilerFileField
from model_utils.models import TimeStampedModel


class Item(TimeStampedModel):
    """Holds items that are contained within a Set."""
    class Meta:
        app_label = 'filersets'
        verbose_name = _('item')
        verbose_name_plural = _('items')
        ordering = ('item_sort__sort',)

    set = models.ForeignKey(
        'Set',
        verbose_name=_('Belongs to set'),
        related_name='filer_set',
        null=False,
        default=None,
        blank=None
    )

    # TODO: Name the content type field as suggested in the django docs
    ct = models.ForeignKey(
        ContentType,
        verbose_name=_('content type'),
        related_name='contenttype',
        null=False,
        default=None,
        blank=False
    )

    is_cover = models.BooleanField(
        _('cover item?'),
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

    is_locked = models.BooleanField(
        _('locked?'),
        help_text=_('Reprocessing a set searches for and deletes files that '
                    'are not/no longer contained within the root folder. Check '
                    'locked if you wish to keep this file as part of the '
                    'set even though it is reported as an orphan.'),
        blank=False,
        default=False,
        null=False
    )

    def get_item_thumb(self):
        """Returns a thumbnail representation of the current item."""
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

    def get_original_filename(self):
        """Returns the original filename of the item."""
        return self.filer_file.original_filename

    get_original_filename.short_description = 'filename'
    get_original_filename.allow_tags = True

    def get_sort_position(self):
        """Returns 0-based sort position of the item."""
        return self.item_sort.sort

    get_sort_position.short_description = 'Pos'

    def get_next(self, circle=True):
        """ Return next item in set or None.

        :param circle: whether to return the last item if current is the first
        :type circle: bool
        """
        pos = self.get_sort_position()
        sorted_items = self.set.get_items_sorted()

        try:
            return self.set.get_items_sorted()[pos + 1]
        except IndexError:
            return sorted_items[0] if circle else None

    def get_previous(self, circle=True):
        """ Return next item in set or None.

        :param circle: whether to return the last item if current is the first
        :type circle: bool
        """
        pos = self.get_sort_position()
        sorted_items = self.set.get_items_sorted()

        if circle:
            return sorted_items[pos - 1]
        else:
            return None if pos == int(0) else sorted_items[pos - 1]

    def is_timeline(self):
        """Check is_timeline flag on the file and return True or False."""
        is_timeline = False
        try:
            is_timeline = self.filer_file.filemodelext_file.all()[0].is_timeline
        except IndexError:
            pass
        return is_timeline

    def get_is_timeline(self):
        """Renders green check or red x according to is_timeline flag."""
        yesno = 'check-circle' if self.is_timeline() else 'times-circle'
        output = '<i class="fs_is-timeline-indicator fa fa-{}"></i>'
        return output.format(yesno)

    get_is_timeline.allow_tags = True
    get_is_timeline.short_description = _('Tl.?')

    def save(self, *args, **kwargs):
        if not self.ct_id:
            self.ct_id = ContentType.objects.get(
                pk=self.filer_file.polymorphic_ctype_id).id

        super(Item, self).save(*args, **kwargs)

    @classmethod
    def on_item_post_delete(cls, sender, instance, using, **kwargs):
        """Deletes the associated file from filer."""
        try:
            instance.filer_file.delete()
        except ObjectDoesNotExist:
            pass

    def __unicode__(self):
        return u'{}'.format(self.filer_file.original_filename)
        # return u'Set: {}'.format(self.set.title)

post_delete.connect(Item.on_item_post_delete, sender=Item)