# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from autoslug import AutoSlugField
from django.db import models
from django.db.models.signals import pre_delete
from django.utils.translation import ugettext_lazy as _
from filer.fields.folder import FilerFolderField
from filersets.fields import TreeManyToManyField
from filersets.models import Category


class Settype(models.Model):
    """Enables users to configure different types of sets.

    With set types users can configure categories that belong to certain
    logical entities of filersets. For example, if you use filersets for
    image galleries and downloads then you do not want to show sets
    belonging to one of them in the list view of the other.
    """
    class Meta:
        app_label = 'filersets'
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

    #: When creating a new set type, a category on root level is automatically
    #: created and referenced in ``category``.
    category = TreeManyToManyField(
        Category,
        verbose_name=_('categories'),
        related_name='settype_categories',
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
        """Returns Category instance of connected root category."""
        return self.category.first()

    def get_root_category_slug(self, default=None):
        """Returns slug of root category or ``default``."""
        try:
            return self.get_root_category().slug
        except AttributeError:
            return default

    def save(self, *args, **kwargs):
        """Creates new category on category root level and sets relation."""
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
        """Deletes the root category and its descendants."""
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