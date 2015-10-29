# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
import unittest

from datetime import datetime
from shlex import split as shlex_split

from utils import key_generator
from utils import get_repo_name_from_url
from utils import git


def test_get_repo_name_from_url():
    ret = get_repo_name_from_url('file:///tmp/project.git')
    assert ret == 'project'

    ret = get_repo_name_from_url('file:///tmp/python-gitview.git')
    assert ret == 'python-gitview'

    ret = get_repo_name_from_url('https://github.com/python-gitview.git')
    assert ret == 'python-gitview'

    ret = get_repo_name_from_url('https://github.com/python-gitview')
    assert ret == 'python-gitview'


def test_key_generator():
    ret = key_generator('hello', 'world')
    assert ret == 'hello,world'

    ret = key_generator('hello')
    assert ret == 'hello'

    ret = key_generator('Hi', 'hello', 'world', delimiter=', ')
    assert ret == 'Hi, hello, world'


def test_time_str_to_datetime():
    timestamp = '1397716290'
    dt = git.time_str_to_datetime(timestamp)
    assert dt == datetime.fromtimestamp(float(timestamp))

    format = '%a %b %d %H:%M:%S %Y'
    when = 'Fri Jan 25 01:21:30 2008'
    dt = git.time_str_to_datetime(when)
    assert dt == datetime.strptime(when, format)

    when = 'Fri Jan 25 20:21:30 2008'
    dt = git.time_str_to_datetime(when)
    assert dt == datetime.strptime(when, format)


class TestGitLog(unittest.TestCase):
    '''Test GitLog'''

    def setUp(self):
        self.git_log = ('0e2b29683642ed3c7fef5e0189000cb203e07aa6,1420474274,Chenxiong Qi,my@example.com',
                        'move dependencies to separate requirements file',
                        '3 files changed, 14 insertions(+), 4 deletions(-)')
        self.git_log1 = ('0e2b29683642ed3c7fef5e0189000cb203e07aa6,1420474274,Chenxiong Qi,my@example.com',
                         'move dependencies to separate requirements file',
                         '3 files changed, 14 insertions(+)')
        self.git_log2 = ('0e2b29683642ed3c7fef5e0189000cb203e07aa6,1420474274,Chenxiong Qi,my@example.com',
                         'move dependencies to separate requirements file',
                         '3 files changed, 4 deletions(-)')
        self.git_log3 = ('0e2b29683642ed3c7fef5e0189000cb203e07aa6,1420474274,Chenxiong Qi,my@example.com',
                         'move dependencies to separate requirements file',
                         '1 file changed, 1 deletion(-)')

    def test_parse(self):
        log = git.GitLog.parse(self.git_log)

        self.assertEqual(log.commit_hash,
                         '0e2b29683642ed3c7fef5e0189000cb203e07aa6')
        self.assertEqual(log.abbreviated_commit_hash, '0e2b296')
        self.assertEqual(log.submit_date, datetime.fromtimestamp(1420474274))
        self.assertEqual(log.author_name, 'Chenxiong Qi')
        self.assertEqual(log.author_email, 'my@example.com')
        self.assertEqual(log.summary,
                         'move dependencies to separate requirements file')
        self.assertEqual(log.files_changed, 3)
        self.assertEqual(log.lines_inserted, 14)
        self.assertEqual(log.lines_deleted, 4)

    def test_parse_partial_stat(self):
        log = git.GitLog.parse(self.git_log1)
        self.assertEqual(log.files_changed, 3)
        self.assertEqual(log.lines_inserted, 14)
        self.assertEqual(log.lines_deleted, 0)

        log = git.GitLog.parse(self.git_log2)
        self.assertEqual(log.files_changed, 3)
        self.assertEqual(log.lines_inserted, 0)
        self.assertEqual(log.lines_deleted, 4)

        log = git.GitLog.parse(self.git_log3)
        self.assertEqual(log.files_changed, 1)
        self.assertEqual(log.lines_inserted, 0)
        self.assertEqual(log.lines_deleted, 1)


class TestGitTag(unittest.TestCase):
    '''Test GitTag'''

    def setUp(self):
        self.git_tag_info = '''
object ee751244f0ee430d78df94d3d82fee78697c6d9a
type commit
tag v1.0
tagger Mike <mike@example.com> 1421299090 +0800

tag release 1.0
'''

    def test_parse(self):
        tag = git.GitTag.parse(self.git_tag_info)
        self.assertEqual(tag.commit_hash,
                         'ee751244f0ee430d78df94d3d82fee78697c6d9a')
        self.assertEqual(tag.name, 'v1.0')
        self.assertEqual(tag.author_name, 'Mike')
        self.assertEqual(tag.author_email, 'mike@example.com')
        self.assertEqual(tag.created_on, datetime.fromtimestamp(1421299090))
        self.assertEqual(tag.tz, '+0800')


class TestGitRepoClone(unittest.TestCase):
    '''Test GitRepo - clone a project'''

    def setUp(self):
        self.working_dir = '/tmp/gitview-test/'
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)
        os.mkdir(self.working_dir)
        self.repo_dir = os.path.join(self.working_dir, 'my-project')
        self.git_repo = git.GitRepo(self.repo_dir)
        self.project_repo_url = os.path.join(os.path.dirname(__file__),
                                             'repos', 'repo1')

    def test_clone(self):
        self.git_repo.clone(self.project_repo_url)

        git_cmd = 'git --git-dir={0}/.git status'.format(self.repo_dir)
        proc, stdout, stderr = git.git(shlex_split(git_cmd))
        self.assert_(proc.returncode == 0, stderr.strip())


class TestGitRepo(unittest.TestCase):
    '''Test GitRepo against a cloned repository'''

    def setUp(self):
        self.working_dir = '/tmp/gitview-test/my-project'
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)
        self.project_repo_url = os.path.join(os.path.dirname(__file__),
                                             'repos', 'repo1')
        self.git_repo = git.GitRepo(self.working_dir)
        self.git_repo.clone(self.project_repo_url)

        self.expected_branch_names = set(('master',
                                          'new-features',
                                          'release-1.0'))
        self.expected_remote_branch_names = set(
            ('remotes/origin/master',
             'remotes/origin/new-features',
             'remotes/origin/release-1.0'))
        self.expected_tag_names = set(('v1.0', 'v1.1'))

    def test_pull(self):
        try:
            self.git_repo.pull()
        except RuntimeError as err:
            self.fail(str(err))

    def test_local_branch_names(self):
        names = self.git_repo.local_branch_names()
        self.assertEqual(len(set(names) - set(('master',))), 0)

    def test_remote_branch_names(self):
        names = set(self.git_repo.remote_branch_names())
        self.assertEqual(len(names - self.expected_remote_branch_names), 0)

    def test_remote_tags_names(self):
        tag_names = self.git_repo.remote_tag_names()
        self.assertEqual(len(set(tag_names) - self.expected_tag_names), 0)

    def test_tags(self):
        tags_names = list(self.git_repo.remote_tag_names())
        tags = self.git_repo.tags(tags_names)
        test_tags_names = set(tag.name for tag in tags)
        self.assertEqual(len(test_tags_names - set(tags_names)), 0)

        for tag in tags:
            self.assert_(len(tag.branch_names) > 0)

    def test_create_local_branch(self):
        self.git_repo.create_local_branches()

        local_branch_names = list(self.git_repo.local_branch_names())
        self.assertEqual(len(local_branch_names),
                         len(list(self.git_repo.local_branch_names())),
                         'No local branch is created to track remote branch.')

        # To see whether all local branch is created to track corresponding
        # remote branch.
        remote_branch_names = self.git_repo.remote_branch_names()
        names = set(git.clean_remote_branch_name(name)
                    for name in remote_branch_names)
        not_created = names - set(local_branch_names)
        self.assert_(len(not_created) == 0,
                     '{0} not created.'.format(' '.join(not_created)))

    def test_logs(self):
        logs = list(self.git_repo.logs())
        self.assert_(len(logs) > 0)

        logs = list(self.git_repo.logs(rev_range='HEAD^^...HEAD'))
        commits_count_certainly = 2
        self.assertEqual(len(logs), commits_count_certainly)

        remote_branch_names = list(self.git_repo.remote_branch_names())
        commits_count_certainly = 1
        logs = list(self.git_repo.logs(branch_name=remote_branch_names[1]))
        self.assert_(len(logs) > 0)

    def test_get_contributors(self):
        contributors = list(self.git_repo.get_contributors())
        self.assert_(len(contributors) > 0)

        contributors = list(self.git_repo.get_contributors('master'))
        self.assert_(len(contributors) > 0)

        contributors = list(self.git_repo.get_contributors(('master',)))
        self.assert_(len(contributors) > 0)

    def test_get_all_contributors(self):
        ones_remote = list(
            self.git_repo.get_all_contributors(from_local=False))
        self.assert_(len(ones_remote) > 0)

        ones_local = list(
            self.git_repo.get_all_contributors(from_remote=False))
        self.assert_(len(ones_local) > 0)

        ones_from_all = list(self.git_repo.get_all_contributors())
        self.assert_(len(ones_from_all) > 0)

        ones_from_where = list(
            self.git_repo.get_all_contributors(from_local=False,
                                               from_remote=False))
        self.assert_(len(ones_from_where) > 0)

        self.assert_(len(ones_remote) >= len(ones_local))

        # No local branch created and commits pushed to it, so both of them
        # should be equivalent.
        self.assertEqual(len(ones_from_all), len(ones_remote))

        ones_from_current_branch = list(self.git_repo.get_contributors())
        self.assertEqual(len(ones_from_where), len(ones_from_current_branch))
