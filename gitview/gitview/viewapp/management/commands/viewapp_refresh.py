# -*- coding: utf-8 -*-

import re

from logging import getLogger

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

from viewapp import projectanalyze
from viewapp.models import Project


logger = getLogger("commands_logger")


class Command(BaseCommand):
    args = '<project1 project2 ...>'
    help = 'Synchronize projects from corresponding remote Git repository.'

    option_list = BaseCommand.option_list + (
        make_option('-a', '--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help="synchronize all projects"),
        make_option('-n', '--new',
                    action='store_true',
                    dest='newly_added',
                    default=False,
                    help="synchronize newly added projects"),
        make_option('-f', '--force',
                    action='store_true',
                    dest='force_sync',
                    default=False,
                    help='when some projects you specified do not exist, '
                         'force to synchronize the existing ones instead '
                         'of termination.',))

    def handle(self, *args, **options):
        opt_all = options.get('all')
        opt_newly_add = options.get('newly_added')
        if opt_all and opt_newly_add:
            raise CommandError(
                '--all and --new should not be specified at same time.')

        if opt_all:
            projects = Project.objects.only('name', 'url')
        elif opt_newly_add:
            projects = Project.objects.filter(
                last_synced_on=None).only('name', 'url')
        elif args:
            projects = Project.objects.filter(
                name__in=args).only('name', 'url')
            names = set(item.name for item in projects)
            diff = set(args) - names
            if diff and not options.get('force_sync'):
                raise CommandError(
                    '{0} project(s) do not exist.'.format(' '.join(diff)))
        else:
            raise CommandError(':O surprised! This should not happen.')

        projectanalyze.run(projects)
