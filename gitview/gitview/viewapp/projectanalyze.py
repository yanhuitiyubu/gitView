# -*- coding: utf-8 -*-

import os
import sys

from datetime import datetime
from logging import getLogger

from django.conf import settings
from django.db import transaction

from utils import git
from utils import key_generator
from viewapp.models import Branch
from viewapp.models import Commit
from viewapp.models import Developer
from viewapp.models import DeveloperBranch
from viewapp.models import Project
from viewapp.models import Tag


path_exists = os.path.exists
path_join = os.path.join


logger = getLogger("commands_logger")


COMMIT_SUMMARY_MAX_LENGTH = 200


def get_project_name(git_repo_url):
    return git_repo_url.split('/')[-1].replace('.git', '')


class ProjectGitSyncTask(object):
    '''Task to synchronize a project's git into database'''

    def __init__(self, project):
        assert isinstance(project, Project)
        self.project = project
        self.project_dir = path_join(settings.PROJECT_DIR, project.name)
        self.git_repo = git.GitRepo(self.project_dir)

        #self._prepare_global_data()

    def _prepare_global_data(self):
        '''Prepare global data  used while syncing against a project'''
        qs = Developer.objects.filter(
            projects=self.project).values('full_name', 'email')
        # Text containing contributor's name and email from terminal is encoded
        # in UTF-8 by default. So, you must have already realized why full_name
        # and email retrieved from database must be encoded in UTF-8 too. :)
        self._existing_contributors = set(
            (key_generator(d['full_name'].encode('utf-8'),
                           d['email'].encode('utf-8'))
             for d in qs.iterator()))

    def _clone_or_pull(self):
        '''Clone or pull project according to existence'''
        if self.git_repo.cloned:
            logger.info('Pull {0} from {1}'.format(self.project.name,
                                                   self.project.url))
            self.git_repo.pull()
        else:
            logger.info('Clone {0} from {1}'.format(self.project.name,
                                                    self.project.url))
            self.git_repo.clone(self.project.url)

    def _new_branches_to_sync(self):
        '''Get new branches that need to synchronize'''
        qs = Branch.objects.filter(project=self.project).values('name',
                                                                'project')
        existing_branches = set((
            '{0},{1}'.format(branch['project'], branch['name'])
            for branch in qs.iterator()))
        # Before checking if there is any new branch appearing in remote
        # repository, we need to strip the remote spec information from
        # remote branch name.
        branches_in_repo = set((
            '{0},{1}'.format(self.project.pk,
                             git.clean_remote_branch_name(name))
            for name in self.git_repo.remote_branch_names()))

        new_branches = branches_in_repo - existing_branches
        return (branch.split(',')[1] for branch in new_branches)

    def _branches_to_sync(self):
        '''Get the branches that need to synchronize'''
        qs = Branch.objects.filter(project=self.project).values('name','project')
        branches_in_repo = set((
            '{0},{1}'.format(self.project.pk,
                             git.clean_remote_branch_name(name))
            for name in self.git_repo.remote_branch_names()))
        return (branch.split(',')[1] for branch in branches_in_repo)

    def _build_developer_branch_rel(self, branch):
        '''Build the relationship between developer and branch

        DeveloperBranch is the core relationship between developer and branch,
        and also a core concept to GitView to query and generate report.

        Developers will created for you if they does not exist in GitView
        already.
        '''
        branch_name = branch.name
        remote_branch_name = git.build_remote_branch_name(branch_name)
        contributors = self.git_repo.get_contributors(remote_branch_name)

        qs = DeveloperBranch.objects.filter(
            branch__project=self.project).values('developer__full_name',
                                                 'branch__name')
        existing_rels = set((key_generator(rel['developer__full_name'],
                                           rel['branch__name'])
                             for rel in qs.iterator()))

        get_developer = Developer.objects.get
        create_developer = Developer.objects.create
        create_rel = DeveloperBranch.objects.create
        add_developer_to_project = self.project.developers.add

        for contributor in contributors:
            new_rel_key = key_generator(contributor.full_name, branch_name)
            if new_rel_key in existing_rels:
                continue

            try:
                developer = get_developer(full_name=contributor.full_name,
                                          email=contributor.email)
            except Developer.DoesNotExist:
                kerb_name = contributor.email.split('@')[0]
                developer = create_developer(kerb_name=kerb_name,
                                             email=contributor.email,
                                             full_name=contributor.full_name)

            add_developer_to_project(developer)

            # Finally, we have enough things, developer and branch, to
            # build the relationship. That's great!
            create_rel(developer=developer, branch=branch)

            # Remember this newly added relationship, next iterations would
            # check the existence of relationship between developer and branch
            existing_rels.add(new_rel_key)

    def _sync_branches(self):
        '''Synchronize branches and related data

        Related data contains developers and commits for now.
        '''
        new_names = list(self._new_branches_to_sync())
        names = list(self._branches_to_sync())

        if not names:
            logger.info('No new branches to synchronize')
            return

        if len(names) > 1:
            logger.info(
                'Synchronize branches {0}'.format(', '.join(names)))
        else:
            logger.info('Synchronize branch {0}'.format(names[0]))

        for branch_name in names:
            if branch_name in new_names:
                branch = Branch.objects.create(name=branch_name,
                                               project=self.project)
                self._build_developer_branch_rel(branch)
            self._sync_branch_commits(Branch.objects.get(name=branch_name,project=self.project))

    def _sync_tags(self):
        '''Add new tags'''
        # Useful for getting which branches a tag is related to.
        # Any good solution?
        self.git_repo.create_local_branches()
        logger.info('Local branches are created.')

        qs = Tag.objects.filter(project=self.project).values('name', 'project')
        existing_tags = set((key_generator(str(tag['project']), tag['name'])
                             for tag in qs.iterator()))
        remote_tags = set((key_generator(str(self.project.pk), name)
                           for name in self.git_repo.remote_tag_names()))

        new_tags = set(remote_tags) - set(existing_tags)

        if not new_tags:
            logger.info('No new tags to synchronize')
            return

        new_tags = (tag.split(',')[1] for tag in new_tags)

        create_tag = Tag.objects.create
        branch_manager = Branch.objects

        # Start to add new tags
        for tag in self.git_repo.tags(new_tags):
            if isinstance(tag, git.InvalidTagError):
                msg = 'Skip to synchronize invalid tag {0}'.format(tag.data)
                logger.warning(msg)
                continue
            else:
                logger.info('Synchronize tag {0}'.format(tag.name))

                model = create_tag(name=tag.name,
                                   submit_date=tag.created_on,
                                   project=self.project)
                for branch_name in tag.branch_names:
                    try:
                        branch = branch_manager.get(project=self.project,
                                                    name=branch_name)
                    except Branch.DoesNotExist:
                        branch = branch_manager.create(project=self.project,
                                                       name=branch_name)
                    model.branches.add(branch)

    def _sync_branch_commits(self, branch):
        '''Synchronize commits against remote branch

        :param branch: from which branch to synchronize commits
        :type branch: Branch
        '''
        # Determine rev range
        commits = Commit.objects.filter(project=self.project,
                                        branch=branch)
        commits = commits.only('commit_hash').order_by('-submit_date')[:1]

        if len(commits) == 0:
            rev_range = 'HEAD'
        else:
            rev_range = '{0}...HEAD'.format(commits[0].commit_hash)

        logger.info(
            'Commits within {0} on branch {1} will be synchronized'.format(
                rev_range, branch.name))

        # Get logs (commits) within the rev range
        logs = self.git_repo.logs(rev_range,
                                  git.build_remote_branch_name(branch.name))

        # Sync commits
        create_developer = Developer.objects.create
        filter_developer = Developer.objects.filter
        create_commit = Commit.objects.create

        qs = Commit.objects.filter(project=self.project,
                                   branch=branch).values_list('commit_hash',
                                                              flat=True)
        existings = set(qs.iterator())

        for log in logs:
            if log.commit_hash in existings:
                continue

            logger.debug('Synchronize commit {0}'.format(log.commit_hash))

            # I know, I know, developers are already synchronized in a separate
            # step, but still add here if necessary as a supplementary.
            qs = filter_developer(email=log.author_email).only('pk')
            if len(qs) == 0:
                logger.debug('Add new developer {0}'.format(log.author_email))

                kerb_name = log.author_email.split('@')[0]
                developer = create_developer(kerb_name=kerb_name,
                                             email=log.author_email,
                                             full_name=log.author_name)
            else:
                developer = qs[0]

            # Shrink summary to length 100 character
            summary = log.summary
            summary_too_long = len(summary) > COMMIT_SUMMARY_MAX_LENGTH
            if summary_too_long:
                logger.warning(u'Summary "{0}" of commit {1} is too long to '
                               u'store in database. Truncate to 100 to fit '
                               u'the length of Commit.summary field.'.format(
                                   summary, log.abbreviated_commit_hash))
                summary = summary[0:100]

            create_commit(commit_hash=log.commit_hash,
                          submit_date=log.submit_date,
                          summary=summary,
                          classification='',
                          total_files=log.files_changed,
                          lines_inserted=log.lines_inserted,
                          lines_deleted=log.lines_deleted,
                          project=self.project,
                          branch=branch,
                          developer=developer)

    def run(self):
        '''Run this task

        Eventually, all following tasks should get run in this give order. If
        the order is changed, the result is unpredictable.
        '''
        self._clone_or_pull()
        logger.info('Begin to synchronize branches and related contributors '
                    'and commits')
        self._sync_branches()
        logger.info('Begin to synchronize tags')
        self._sync_tags()


def run(projects):
    projects_count = len(projects)

    if projects_count == 0:
        logger.info('No project to synchronize')
        return

    for i, project in enumerate(projects, start=1):
        logger.info('Synchronize project {0} ({1}/{2})'.format(
            project, i, projects_count))

        try:
            project.being_syncing = True
            project.save(update_fields=('being_syncing',))
        except Exception as err:
            logger.error('Failed to prepare the start of synchronization.')
            logger.error('This is unexpected thing. If failed to prepare '
                         'synchronization for an arbitrary project, the whole '
                         'task should terminate immediately.')
            sys.exit(1)

        try:
            with transaction.commit_on_success():
                ProjectGitSyncTask(project).run()

                project.last_synced_on = datetime.now()
                project.save(update_fields=('last_synced_on',))

            logger.info('Succeed to synchronize project {0}'.format(project))
        except KeyboardInterrupt:
            logger.info('Synchronization is terminated by user.')
            sys.exit(2)
        except Exception as err:
            logger.error(str(err).strip())
            logger.error('Failed to synchronize project {0}'.format(project))
            if settings.DEBUG:
                raise
        finally:
            project.being_syncing = False
            project.save(update_fields=('being_syncing',))
