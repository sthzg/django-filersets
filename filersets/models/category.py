# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from autoslug import AutoSlugField
from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_delete, post_delete
from django.utils.translation import ugettext_lazy as _
from treebeard.mp_tree import MP_Node, MP_NodeManager
from .set import Set


class CategoryManager(MP_NodeManager):
    def get_categories_by_level(self, level_start=0, depth=0, skip_empty=False):
        """Retrieve a queryset with categories.

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


class Category(MP_Node):
    """Associates categories with set instances.

    Categories in root level behave in a special way. Every time a new
    ``Settype`` instance is created, a category in root level is automatically
    created and linked to this set type.

    Users are not allowed to ...

    a) create categories in root level
    b) move root level categories to child levels
    c) move child level categories to root level
    """
    class Meta:
        app_label = 'filersets'
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
        """Returns the number of sets contained in current category."""
        return Set.objects.filter(category=self, status='published').count()

    def get_level_compensation(self, compensate_to=None):
        """Returns the offset to the root level as int."""
        # TODO  Implement compensate_to functionality
        return self.get_depth() - 1

    def save(self, *args, **kwargs):
        """Overriding save to provide a category slug."""
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