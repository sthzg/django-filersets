# -*- coding:utf-8 -*-
# ______________________________________________________________________________
#                                                                         Future
from __future__ import absolute_import
# ______________________________________________________________________________
#                                                                         Python
import sys
# ______________________________________________________________________________
#                                                                         Django
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
# ______________________________________________________________________________
#                                                                        Package
from filersets.models import Set


class Command(BaseCommand):
    args = '<set_id>'
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

        if len(args) is not int(1):
            self.stderr.write('Please provide one set_id as argument')
            return
        elif not isinstance(int(args[0]), int):
            self.stderr.write('Argument must be an integer')

        set_id = int(args[0])
        try:
            fset = Set.objects.get(pk=set_id)
        except ObjectDoesNotExist:
            self.stderr.write('No set with this set_id')
            exit(1)

        op_stats = fset.create_or_update_set()

        self.stdout.write('No change:\n{}'.format(
            '\n'.join([str(s) for s in op_stats['noop']])))

        self.stdout.write('Updated:\n{}'.format(
            '\n'.join([str(s) for s in op_stats['updated']])))

        self.stdout.write('Added:\n{}'.format(
            '\n'.join([str(s) for s in op_stats['added']])))

        sys.exit(0)
