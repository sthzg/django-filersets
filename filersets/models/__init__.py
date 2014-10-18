# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.db.models.signals import post_save
from django.dispatch import receiver
from filer.models import Image
from .category import Category
from .filemodelext import FilemodelExt
from .item import Item
from .set import Set
from .setitemsort import SetItemSort
from .settype import Settype


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