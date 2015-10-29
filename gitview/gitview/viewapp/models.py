# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

from utils import get_repo_name_from_url


# FIXME: reuse django.contrib.auth.User
class Developer(models.Model):
    # TODO: to remove this field. no necessary
    kerb_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=100)
    patches_amount = models.IntegerField(blank=True, null=True)
    total_lines = models.IntegerField(blank=True, null=True)
    total_lines_inserted = models.IntegerField(blank=True, null=True)
    total_lines_deleted = models.IntegerField(blank=True, null=True)
    latest_update = models.DateTimeField(blank=True, null=True)
    email = models.EmailField(db_index=True)
    projects = models.ManyToManyField('Project', related_name='developers')

    def __unicode__(self):
        return self.full_name

    class Meta:
        unique_together = ('email', 'full_name')

    @property
    def total_lines(self):
        pass

    @property
    def total_lines_inserted(self):
        pass

    @property
    def total_lines_deleted(self):
        pass

    @property
    def latest_commit(self):
        pass

    @property
    def projects_amount(self):
        return self.projects.count()


HELPTEXT_SHOULD_NOT_EDIT = _('This should not be edited in WebUI.')


class CodeHost(models.Model):
    name = models.CharField(max_length=255, null=True)
    commit_url = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    code_host = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=200, blank=True, default='',
                            help_text=_('Can be empty. It will be replaced ' \
                                        'with the project name retreived ' \
                                        'from remote repository URL.'))
    description = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(unique=True,
                          help_text=_('Valid Git repository URL'))
    code_host = models.ForeignKey(CodeHost, null=True)

    # Status for internal usage only
    being_syncing = models.BooleanField(default=False, blank=True,
                                        help_text=HELPTEXT_SHOULD_NOT_EDIT)
    last_synced_on = models.DateTimeField(blank=True, null=True, db_index=True,
                                          help_text=HELPTEXT_SHOULD_NOT_EDIT)

    def __unicode__(self):
        return self.name if self.name else self.url

    @property
    def is_synced_ever(self):
        return self.last_synced_on is None

    def save(self, *args, **kwargs):
        if len(self.name) == 0:
            self.name = get_repo_name_from_url(self.url)
        return super(Project, self).save(*args, **kwargs)


class DeveloperBranch(models.Model):
    developer = models.ForeignKey(Developer)
    branch = models.ForeignKey('Branch')

    def __unicode__(self):
        return u'{0} on branch {1}'.format(self.developer.full_name,
                                           self.branch.name)

    class Meta:
        unique_together = ('branch', 'developer')


class Branch(models.Model):
    """to support Branch"""
    name = models.CharField(max_length=100, db_index=True)
    start_date = models.DateTimeField(blank=True, null=True)
    latest_update = models.DateTimeField(blank=True, null=True)
    latest_commit = models.CharField(max_length=15, blank=True, null=True)
    total_patches = models.IntegerField(blank=True, null=True)
    total_lines = models.IntegerField(blank=True, null=True)
    total_lines_inserted = models.IntegerField(blank=True, null=True)
    total_lines_deleted = models.IntegerField(blank=True, null=True)
    developers = models.ManyToManyField(Developer, blank=True,
                                        through=DeveloperBranch,
                                        related_name='developer_branches')
    project = models.ForeignKey(Project, related_name='branches')

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('project', 'name')


class Patch(models.Model):
    commit_id = models.CharField(max_length=50)
    submit_date = models.DateTimeField(db_index=True)
    classification = models.CharField(max_length=4)
    total_files = models.IntegerField()
    lines_inserted = models.IntegerField()
    lines_deleted = models.IntegerField()
    total_lines = models.IntegerField()
    project = models.ForeignKey(Project, related_name='patches')
    branch = models.ForeignKey(Branch, related_name='patches')
    developer = models.ForeignKey(Developer, related_name='patches')

    def __unicode__(self):
        return u'{0} {1} {2}'.format(self.project.name,
                                     self.branch.name,
                                     self.commit_id)


class Commit(models.Model):
    commit_hash = models.CharField(max_length=50, db_index=True)
    submit_date = models.DateTimeField(db_index=True)
    summary = models.CharField(max_length=200, blank=True, default='')
    classification = models.CharField(max_length=10, blank=True, null=True)
    total_files = models.PositiveIntegerField(blank=True, default=0)
    lines_inserted = models.PositiveIntegerField(blank=True, default=0)
    lines_deleted = models.PositiveIntegerField(blank=True, default=0)
    project = models.ForeignKey(Project, related_name='commits')
    branch = models.ForeignKey(Branch, related_name='commits')
    developer = models.ForeignKey(Developer, related_name='commits')
    class Meta:
        unique_together = ('project', 'branch', 'commit_hash')

    def __unicode__(self):
        return self.commit_hash

    @property
    def abbreviated_commit_hash(self):
        return self.commit_hash[0:7]

    @property
    def files_changed(self):
        return self.total_files

    @property
    def total_lines(self):
        return self.lines_inserted - self.lines_deleted

    @property
    def commit_url(self):
        return self.project.code_host.commit_url % {'project_name':self.project.name,'commit_hash':self.commit_hash}

class Tag(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    submit_date = models.DateTimeField()
    project = models.ForeignKey(Project, related_name='tags')
    branches = models.ManyToManyField(Branch, related_name='tags')

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('project', 'name')


class ViewappLog(models.Model):
    """viewapp_error_log"""
    time_stamp = models.DateTimeField()
    error_comment = models.CharField(max_length=300)

    def __unicode__(self):
        return self.error_comment
