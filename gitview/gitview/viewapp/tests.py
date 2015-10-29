# -*- coding: utf-8 -*-

import os
import unittest

from itertools import imap

from utils import git
from viewapp.models import Branch
from viewapp.models import Commit
from viewapp.models import Developer
from viewapp.models import DeveloperBranch
from viewapp.models import Project
from viewapp.models import Tag
from viewapp.projectanalyze import get_project_name
from viewapp.projectanalyze import ProjectGitSyncTask


class TestHelperMethods(unittest.TestCase):

    def test_get_project_name(self):
        url = 'https://github.com/user/python-repo.git'
        ret = get_project_name(url)
        self.assertEqual(ret, 'python-repo')

        url = 'https://github.com/user/python-repo'
        ret = get_project_name(url)
        self.assertEqual(ret, 'python-repo')

        url = 'github.com/user/python-repo'
        ret = get_project_name(url)
        self.assertEqual(ret, 'python-repo')

        url = ''
        ret = get_project_name(url)
        self.assertEqual(ret, url)


test_repo_dir = os.path.join(os.path.dirname(__file__), '..',
                             'utils/tests/repos/repo1')
test_repo_uri = 'file://{0}'.format(test_repo_dir)


class TestProjectAnalyze(unittest.TestCase):
    '''Test project analyze'''

    def setUp(self):
        self.project = Project.objects.create(name='test_project',
                                              url=test_repo_uri,
                                              description='test project')

        self.dev1 = Developer.objects.create(kerb_name='dev1',
                                             full_name='developer 1',
                                             email='dev1@example.com')
        self.dev2 = Developer.objects.create(kerb_name='dev2',
                                             full_name='developer 2',
                                             email='dev2@example.com')

        self.dev1.projects.add(self.project)
        self.dev2.projects.add(self.project)

        self.branch1 = Branch.objects.create(name='test_branch1',
                                             project=self.project)
        self.branch2 = Branch.objects.create(name='test_branch2',
                                             project=self.project)

        self.rel_branch_dev1 = DeveloperBranch.objects.create(
            branch=self.branch1, developer=self.dev1)
        self.rel_branch_dev2 = DeveloperBranch.objects.create(
            branch=self.branch2, developer=self.dev1)
        self.rel_branch_dev3 = DeveloperBranch.objects.create(
            branch=self.branch2, developer=self.dev2)

        self.task = ProjectGitSyncTask(self.project)
        self.task._clone_or_pull()

    def tearDown(self):
        self.rel_branch_dev1.delete()
        self.rel_branch_dev2.delete()
        self.rel_branch_dev3.delete()

        self.branch1.delete()
        self.branch2.delete()

        self.dev1.projects.remove(self.project)
        self.dev2.projects.remove(self.project)
        self.dev1.delete()
        self.dev2.delete()

        self.project.delete()

        self.task.git_repo.delete()

    def test_new_branches_to_sync(self):
        new_ones = list(self.task._new_branches_to_sync())
        self.assert_(len(new_ones) > 0)

        existings = [self.branch1.name, self.branch2.name]
        for branch_name in new_ones:
            self.assert_(branch_name not in existings)

    def test_run(self):
        self.task.run()

        # Verify branch
        names = imap(git.clean_remote_branch_name,
                     self.task.git_repo.remote_branch_names())
        for name in names:
            ret = Branch.objects.filter(name=name).exists()
            self.assert_(ret)

        # Verify tag
        tag_names = self.task.git_repo.remote_tag_names()
        for name in tag_names:
            ret = Tag.objects.filter(name=name).exists()
            self.assert_(ret)

        # Verify developer
        filter_developer = Developer.objects.filter
        filter_branch = Branch.objects.filter
        filter_dev_branch = DeveloperBranch.objects.filter

        branch_names = imap(git.clean_remote_branch_name,
                            self.task.git_repo.remote_branch_names())
        for name in branch_names:
            contributors = self.task.git_repo.get_contributors(name)
            for contributor in contributors:
                developers = filter_developer(full_name=contributor.full_name,
                                              email=contributor.email)
                self.assert_(developers.exists())

                branches = filter_branch(name=name, project=self.project)
                self.assert_(branches.exists())

                ret = filter_dev_branch(developer=developers[0],
                                        branch=branches[0]).exists()
                self.assert_(ret)

        # Verify commit
        branch_names = imap(git.clean_remote_branch_name,
                            self.task.git_repo.remote_branch_names())
        for name in branch_names:
            ret = Commit.objects.filter(project=self.project,
                                        branch__name=name).exists()
            self.assert_(ret)
