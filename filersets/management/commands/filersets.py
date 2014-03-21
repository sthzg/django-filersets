# -*- coding:utf-8 -*-
from __future__ import absolute_import
import sys
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from filer.models import File
from filersets.models import Set, Item

class Command(BaseCommand):
    args = ''
    help = 'Build filersets data'
    can_import_settings = True

    def handle(self, *args, **options):
        """
        The management command checks all filer sets and creates the items
        if they don't exist already. The current idea is to give site admins
        various ways to to this step.

        1. invoking the manage.py command from the cl during development
        2. invoking it from a cronjob that periodically checks for new sets
        3. invoking it through buttons in the interface
        4. invoking it as a celery task for systems that have celery enabled

        TODO    organize the command with subcommands much like in Django CMS
        TODO    create a subcommand that takes set_id(s) to create on purpose
        TODO    create a way to alternatively handle this logic in a celery task
        """

        for filerset in Set.objects.all():

            folder_ids = [folder.id for folder in filerset.set_root.all()]

            for f in File.objects.filter(folder_id__in=folder_ids):

                # Check if there is an item already
                try:
                    Item.objects.get(set=filerset.pk, filer_file__id=f.id)
                    msg = '{} in set id {} already exists'
                    self.stdout.write(msg.format(f.id, filerset.pk))

                except ObjectDoesNotExist:
                    item = Item()
                    item.set = filerset
                    item.ct = ContentType.objects.get(pk=f.polymorphic_ctype_id)
                    item.filer_file = f
                    item.order = 1
                    item.save()

                    msg = '{} saved for set id {}'
                    self.stdout.write(msg.format(f.id, filerset.pk))

        sys.exit(0)
