# -*- coding: utf-8 -*-

import re
import os
import shutil

from StringIO import StringIO
from datetime import datetime
from shlex import split as shlex_split
from subprocess import Popen, PIPE


__all__ = (
    'GitContributor',
    'GitLog',
    'GitRepo',
    'GitTag',
    'build_remote_branch_name',
    'git',
)


path_exists = os.path.exists
path_join = os.path.join

CODING_UTF8 = 'utf-8'
REMOTE_BRANCH_NAME_RE = re.compile(r'^((refs/)?remotes/)(\w+)/(.+$)$')


class InvalidTagError(Exception):
    pass


def build_remote_branch_name(branch_name, remote_name=None):
    _remote_name = 'origin' if remote_name is None else remote_name
    return 'remotes/{0}/{1}'.format(_remote_name, branch_name)


def trans_non_codecs_char(c):
    if not c.isalnum() and c != '.' and c != '-' and c != ' ':
        return '?'
    else:
        return c


def codecs_clean(s):
    from itertools import imap
    return ''.join(imap(trans_non_codecs_char, s))


def sbuffer_iterator(s):
    buffer = StringIO(s)
    try:
        for line in buffer:
            yield line
    finally:
        buffer.close()


def clean_remote_branch_name(remote_branch_name):
    omatch = REMOTE_BRANCH_NAME_RE.match(remote_branch_name)
    if omatch:
        return omatch.group(4)
    else:
        return remote_branch_name


def time_str_to_datetime(when):
    """Convert git date time to datetime object

    This method is for compatibility from git version 1.7.1 to 2.1.x
    """
    if when.isdigit():
        return datetime.fromtimestamp(float(when))
    else:
        format = '%a %b %d %H:%M:%S %Y'
        return datetime.strptime(when, format)


def git(command, shell=False, fail_immediately=True):
    '''Run git command'''
    proc = Popen(command, shell=shell, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()

    if fail_immediately and proc.returncode != 0:
        raise RuntimeError(stderr)

    return (proc,
            stdout.decode(CODING_UTF8, 'replace'),
            stderr.decode(CODING_UTF8, 'replace'))


# Match: 1 file changed, 210 insertions(+), 137 deletions(-)
CHANGES_STAT_RE = re.compile(r'(?P<files_changed>\d+) files? changed(, (?P<lines_inserted>\d+) insertions?\(\+\))?(, (?P<lines_deleted>\d+) deletions?\(-\))?')

COMMIT_INFO_RE = re.compile(r'(?P<commit_hash>[0-9a-zA-Z]+),(?P<timestamp>\d+),(?P<author_name>.+),(?P<author_email>.*)')


class GitContributor(object):
    full_name = u''
    email = u''


class GitLog(object):
    '''Represent a git log entry

    Contain log entry from output of `git-log` with custom options
    '''
    commit_hash = u''
    summary = u''
    files_changed = 0
    lines_inserted = 0
    lines_deleted = 0
    total_lines = 0
    submit_date = None
    author_name = u''
    author_email = u''

    @property
    def abbreviated_commit_hash(self):
        return self.commit_hash[0:7]

    @classmethod
    def parse(cls, output):
        '''Parse lines to create an object of GitLog

        parse accepts format:%H,%at,%aN,%aE%n%s feed to git-log, output may be

        080da0013b2b51525bf29ab617c65eeb18209c37,1420292629,FN LN,email
        Fix searching for keyworks with special chars
         1 file changed, 1 insertion(+), 1 deletion(-)

        But, sometimes, some commit may not have stat line.
        '''
        assert isinstance(output, (tuple, list)), \
            'output should be a string containing lines representing a ' \
            'log entry'

        log = cls()

        for line in output:
            omatch = COMMIT_INFO_RE.match(line)
            if omatch:
                log.commit_hash = omatch.group('commit_hash')
                timestamp = omatch.group('timestamp')
                log.submit_date = datetime.fromtimestamp(float(timestamp))
                log.author_name = omatch.group('author_name')
                log.author_email = omatch.group('author_email')
                continue

            omatch = CHANGES_STAT_RE.match(line)
            if omatch:
                n = omatch.group('files_changed')
                log.files_changed = 0 if n is None else int(n)
                n = omatch.group('lines_inserted')
                log.lines_inserted = 0 if n is None else int(n)
                n = omatch.group('lines_deleted')
                log.lines_deleted = 0 if n is None else int(n)
                continue

            log.summary = line

        return log


class GitTag(object):
    '''Represent a git tag

    Contain tag information from output of `git-tag -v`
    '''

    TAGGER_LINE_RE = re.compile(r'(.+) (<.+@.+>) (\d+|[ a-zA-Z0-9:]+) ([-+]\d{4})')

    commit_hash = None
    name = u''
    author_name = u''
    author_email = u''
    created_on = None
    tz = None

    def __init__(self):
        self.branch_names = []

    @classmethod
    def parse(cls, output):
        '''Parse lines to create an object of GitTag

        Lines start with object, tag, and tagger that are output from
        git-cat-file.
        '''
        tag = cls()
        fromtimestamp = datetime.fromtimestamp
        strptime = datetime.strptime

        three_lines_info_complete = 0
        for line in sbuffer_iterator(output):
            _line = line.strip()
            # In the output from git-cat-file for a tag, a blank line is the
            # separator between header section and the message and GPG section.
            # Currently, there is no need to handle an annotated tag's message
            # and GPG information, so I just ignore this blank line.
            if not _line:
                continue
            label, value = line.strip().split(' ', 1)
            if label == 'object':
                cls.commit_hash = value
                three_lines_info_complete += 1
            elif label == 'tag':
                cls.name = value
                three_lines_info_complete += 1
            elif label == 'tagger':
                omatch = cls.TAGGER_LINE_RE.match(value)
                if omatch is not None:
                    cls.author_name = omatch.group(1)
                    cls.author_email = omatch.group(2).strip('<>')
                    cls.created_on = time_str_to_datetime(omatch.group(3))
                    cls.tz = omatch.group(4)
                    three_lines_info_complete += 1
                else:
                    # FIXME: What should we do when data is invalid some time in the future
                    pass

            if three_lines_info_complete == 3:
                # We just only need object, tag and tagger lines. When all of
                # them are handled, it'll be okay to stop the iteration.
                break
        if three_lines_info_complete == 3:
            return tag
        else:
            raise InvalidTagError('invalid Tag')


    def add_branch_name(self, name):
        assert isinstance(name, basestring) and len(name) > 0
        self.branch_names.append(name)


class GitRepo(object):
    '''Represent a Git repository'''

    BRANCH_LINE_RE = re.compile(r'^remotes/origin/(.+)$')

    def __init__(self, repo_dir):
        self.repo_dir = repo_dir
        self.git_dir = path_join(repo_dir, '.git')

    def delete(self):
        '''Will delete cloned repository permanently'''
        shutil.rmtree(self.repo_dir)

    @property
    def cloned(self):
        return path_exists(self.git_dir)

    def remote_branch_names(self):
        '''Get branch names from output of git-remote show'''
        git_cmd = 'git --git-dir={0} branch -a'.format(self.git_dir)
        proc, stdout, stderr = git(shlex_split(git_cmd))

        ore = self.BRANCH_LINE_RE
        for line in sbuffer_iterator(stdout):
            branch_name = line.strip()
            omatch = ore.match(branch_name)
            if omatch is not None:
                # ignore such line 'remotes/origin/HEAD -> origin/master'
                if not omatch.group(1).startswith('HEAD ->'):
                    yield branch_name

    def local_branch_names(self):
        git_cmd = 'git --git-dir={0} branch'.format(self.git_dir)
        proc, stdout, stderr = git(shlex_split(git_cmd))
        for line in sbuffer_iterator(stdout):
            yield line.strip('* \r\n')

    def remote_tag_names(self):
        git_cmd = shlex_split('git --git-dir={0} tag'.format(self.git_dir))
        proc, stdout, stderr = git(git_cmd)
        for tag in sbuffer_iterator(stdout):
            yield tag.strip()

    def tags(self, tag_names):
        '''Get tags details from repository

        To know how to parse, to see the output of following command

        To get which branches a commit belongs to.
        git --git-dir=/path/to/repo/.git branch --contains commit_hash

        :return: sequence of GitTag
        '''
        git_cat_file = 'git --git-dir={0} cat-file -p `git --git-dir={0} rev-parse {1}`'
        git_branch = 'git --git-dir={0} branch --contains {1}'

        for tag_name in tag_names:
            git_cmd = git_cat_file.format(self.git_dir, tag_name)
            proc, stdout, stderr = git(git_cmd, shell=True)

            try:
                tag = GitTag.parse(stdout)
            except InvalidTagError as error:
                error.data = tag_name
                yield error
            else:
                git_cmd = git_branch.format(self.git_dir, tag.commit_hash)
                proc, stdout, stderr = git(shlex_split(git_cmd))
                for line in sbuffer_iterator(stdout):
                    tag.add_branch_name(line.strip('* \r\n'))

                yield tag

    def clone(self, repo_url, quiet=True):
        '''Clone remote repository to local working directory'''
        if os.path.exists(self.repo_dir):
            raise OSError('Repo {0} already exists.'.format(self.repo_dir))

        git_cmd = 'git clone {0} {1} {2}'.format('-q' if quiet else '',
                                                 repo_url,
                                                 self.repo_dir)
        git(shlex_split(git_cmd))

    def pull(self, quiet=True):
        '''git pull'''
        git_cmd = 'git --git-dir={0} pull {1}'.format(
            self.git_dir, '-q' if quiet else '')
        git(shlex_split(git_cmd))

    def create_local_branches(self):
        '''Create local branches tracking corresponding remote branches'''
        remote_branch_names = self.remote_branch_names()
        git_cmd = ['git', '--git-dir={0}'.format(self.git_dir), 'branch',
                   '--track', '$branch_name', '$remote_branch_name']
        for name in remote_branch_names:
            git_cmd[-2] = clean_remote_branch_name(name)
            git_cmd[-1] = name
            # False: we ignore the failure of git-branch, because some branch
            # has been created already.
            git(git_cmd, fail_immediately=False)

    def logs(self, rev_range=None, branch_name=None, no_merges=True):
        '''Retreive logs from specific branch

        You can specify a specific branch to retreive logs against it, or from
        current branch by omitting the branch_name argument.

        IMPORTANT: currently, no_merges is only a placeholder.

        Logs are retreived by using this command,

        git --git-dir=/path/to/repo/.git logs \
            --pretty="format:%H,%at,%aN,%aE%n%s" --no-merges \
            rev1...rev2 [branch_name]
        '''
        git_cmd = 'git --git-dir={0} log ' \
                  '--pretty="format:%n%H,%at,%aN,%aE%n%s" ' \
                  '--shortstat {1} {2} {3}'
        git_cmd = git_cmd.format(self.git_dir,
        						 # FIXME: to support no_merges argument
                                 '--no-merges',
                                 rev_range if rev_range else 'HEAD',
                                 branch_name if branch_name else '')
        proc, stdout, stderr = git(shlex_split(git_cmd))

        log_lines = []
        buffer = StringIO(stdout)
        # If you want to understand this while-loop, issue git-log above is a
        # good idea.
        while True:
            line = buffer.readline()
            if not line:
                if log_lines:
                    yield GitLog.parse(log_lines)
                break
            s = line.strip()
            if s == u'':
                if log_lines:
                    yield GitLog.parse(log_lines)
                    # Prepare for holding lines of next log
                    del log_lines[:]
                # Here, skip any blank lines before each set of log lines
            else:
                log_lines.append(s)
        buffer.close()

    def get_contributors(self, branch_names=None):
        '''Get contributors from branches

        You may choose from which branch to get contributors. Thanks to Git! No
        restriction of branch name to limit to a local branch or a remote
        branch. Just give the right branch name. Git knows what it is.
        '''
        if branch_names is None:
            _branch_names = u''
        else:
            assert isinstance(branch_names, (tuple, list, basestring)) or \
                hasattr(branch_names, '__iter__')
            _branch_names = branch_names
            if isinstance(branch_names, basestring):
                _branch_names = (branch_names,)

        git_cmd = 'git --git-dir={0} log --pretty=format:"%an,%ae" {1} | sort | uniq'
        git_cmd = git_cmd.format(self.git_dir, ' '.join(_branch_names))
        proc, stdout, stderr = git(git_cmd, shell=True)

        for line in sbuffer_iterator(stdout):
            person = GitContributor()
            # why change from split to rsplit? There are many unpredictable
            # input for user.name from contributors in various open source
            # projects community. NEVER expect regular ones there. In this
            # case, comma is used to be the separator between user.name and
            # user.email, and unfortunately, someone's user.name also contains
            # comma. So, find separator from right side is safer because it's
            # not possible an email address could contain comma characters.
            person.full_name, person.email = line.strip().rsplit(',', 1)
            yield person

    def get_all_contributors(self, from_local=True, from_remote=True):
        '''Get all contributors at once

        You may choose from local branches, remote branches or even both.
        '''
        from itertools import chain
        branch_names = chain(self.local_branch_names() if from_local else (),
                             self.remote_branch_names() if from_remote else ())
        return self.get_contributors(branch_names)
