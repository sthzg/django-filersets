# -*- coding:utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Python
import sys
# ______________________________________________________________________________
#                                                                         Django
from django.core.management.base import BaseCommand
# ______________________________________________________________________________
#                                                                        Package
from filersets.models import Set


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

        op_stats = Set.objects.create_or_update_set()

        self.stdout.write('No change:\n{}'.format(
            '\n'.join([str(s) for s in op_stats['noop']])))

        self.stdout.write('Updated:\n{}'.format(
            '\n'.join([str(s) for s in op_stats['updated']])))

        self.stdout.write('Added:\n{}'.format(
            '\n'.join([str(s) for s in op_stats['added']])))

        sys.exit(0)
