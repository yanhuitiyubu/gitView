# -*- coding: utf-8 -*-

import os
import re
import datetime
import subprocess

from viewapp.models import Project
from viewapp.models import Tag
from viewapp.models import Branch

from django.conf import settings
from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from logging import getLogger

logger = getLogger('commands_logger')


class Command(BaseCommand):
    "refresh the tag of projects"
    option_list = BaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='refresh tags of all projects'),)

    def handle(self, *args, **options):
        project_list = []
        try:
            if options['all']:
                project_list = Project.objects.all()
            elif args:
                project_list = Project.objects.filter(name__in=args)
            self.__refresh(project_list)
        except Exception, error:
            logger.error(error)

    def __refresh(self, project_list):
        logger.info('Refreshing tag')
        for project in project_list:
            try:
                logger.info('Refreshing project: ' + project.name)
                project_name = re.split('/|\.', project.url)[-2]
                project_dir = os.path.join(settings.PROJECT_DIR, project_name)
                os.chdir(project_dir)
                git_tag_cmd = ['git', 'log', '--tags', '--decorate=full',
                               '--pretty=format:%h %d %at']
                grep_cmd = ['grep', 'refs/tags']
                git_proc = subprocess.Popen(git_tag_cmd,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
                grep_proc = subprocess.Popen(grep_cmd,
                                             stdin=git_proc.stdout,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
                git_proc.stdout.close()
                stdout, stderr = grep_proc.communicate()
                for tag_line in stdout.split('\n'):
                    self.__tagLineAna(project, tag_line)
            except Exception, error:
                logger.error(error)

    def __tagLineAna(self, project, tag_line):
        try:
            line_match = re.split(r'\s+|\(|\)|,', tag_line)
            for ref in line_match[1:-1]:
                sign = re.match(r'refs/tags/(.+)', ref)
                if not sign:
                    continue
                git_contains_cmd = ['git', 'branch',
                                    '--contains', line_match[0]]
                proc = subprocess.Popen(git_contains_cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                stdout, stderr = proc.communicate()
                date_format = \
                    datetime.datetime.fromtimestamp(float(line_match[-1]))
                try:
                    tag = Tag.objects.get(name=sign.group(1), project=project)
                except ObjectDoesNotExist:
                    tag = Tag(name=sign.group(1), submit_date=date_format,
                              project=project)
                    tag.save()
                for branch_line in stdout.split('\n'):
                    branch_name = branch_line.strip(' *')
                    if branch_name:
                        try:
                            branch = Branch.objects.get(name=branch_name,
                                                        project=project)
                        except ObjectDoesNotExist:
                            branch = Branch(name=branch_name, project=project)
                            branch.save()
                        if branch not in tag.branches.all():
                            tag.branches.add(branch)
                tag.save()
        except Exception, error:
            logger.error(error)
