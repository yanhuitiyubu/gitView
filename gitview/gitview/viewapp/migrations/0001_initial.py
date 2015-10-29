# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Developer'
        db.create_table(u'viewapp_developer', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('kerb_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('patches_amount', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('projects_amount', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('latest_update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('work_type', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, db_index=True)),
        ))
        db.send_create_signal(u'viewapp', ['Developer'])

        # Adding unique constraint on 'Developer', fields ['email', 'full_name']
        db.create_unique(u'viewapp_developer', ['email', 'full_name'])

        # Adding M2M table for field projects on 'Developer'
        m2m_table_name = db.shorten_name(u'viewapp_developer_projects')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('developer', models.ForeignKey(orm[u'viewapp.developer'], null=False)),
            ('project', models.ForeignKey(orm[u'viewapp.project'], null=False))
        ))
        db.create_unique(m2m_table_name, ['developer_id', 'project_id'])

        # Adding model 'Project'
        db.create_table(u'viewapp_project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(unique=True, max_length=200)),
            ('being_syncing', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_synced_on', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'viewapp', ['Project'])

        # Adding model 'DeveloperBranch'
        db.create_table(u'viewapp_developerbranch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('developer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['viewapp.Developer'])),
            ('branch', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['viewapp.Branch'])),
        ))
        db.send_create_signal(u'viewapp', ['DeveloperBranch'])

        # Adding unique constraint on 'DeveloperBranch', fields ['branch', 'developer']
        db.create_unique(u'viewapp_developerbranch', ['branch_id', 'developer_id'])

        # Adding model 'Branch'
        db.create_table(u'viewapp_branch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('latest_update', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('latest_commit', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('total_patches', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('total_lines', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('total_lines_inserted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('total_lines_deleted', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='branches', to=orm['viewapp.Project'])),
        ))
        db.send_create_signal(u'viewapp', ['Branch'])

        # Adding unique constraint on 'Branch', fields ['project', 'name']
        db.create_unique(u'viewapp_branch', ['project_id', 'name'])

        # Adding model 'Patch'
        db.create_table(u'viewapp_patch', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('commit_id', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('submit_date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('classification', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('total_files', self.gf('django.db.models.fields.IntegerField')()),
            ('lines_inserted', self.gf('django.db.models.fields.IntegerField')()),
            ('lines_deleted', self.gf('django.db.models.fields.IntegerField')()),
            ('total_lines', self.gf('django.db.models.fields.IntegerField')()),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patches', to=orm['viewapp.Project'])),
            ('branch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patches', to=orm['viewapp.Branch'])),
            ('developer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patches', to=orm['viewapp.Developer'])),
        ))
        db.send_create_signal(u'viewapp', ['Patch'])

        # Adding model 'Commit'
        db.create_table(u'viewapp_commit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('commit_hash', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('submit_date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True)),
            ('classification', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('total_files', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('lines_inserted', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('lines_deleted', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('total_lines', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='commits', to=orm['viewapp.Project'])),
            ('branch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='commits', to=orm['viewapp.Branch'])),
            ('developer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='commits', to=orm['viewapp.Developer'])),
        ))
        db.send_create_signal(u'viewapp', ['Commit'])

        # Adding unique constraint on 'Commit', fields ['project', 'branch', 'commit_hash']
        db.create_unique(u'viewapp_commit', ['project_id', 'branch_id', 'commit_hash'])

        # Adding model 'Tag'
        db.create_table(u'viewapp_tag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('submit_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tags', to=orm['viewapp.Project'])),
        ))
        db.send_create_signal(u'viewapp', ['Tag'])

        # Adding unique constraint on 'Tag', fields ['project', 'name']
        db.create_unique(u'viewapp_tag', ['project_id', 'name'])

        # Adding M2M table for field branches on 'Tag'
        m2m_table_name = db.shorten_name(u'viewapp_tag_branches')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tag', models.ForeignKey(orm[u'viewapp.tag'], null=False)),
            ('branch', models.ForeignKey(orm[u'viewapp.branch'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tag_id', 'branch_id'])

        # Adding model 'ViewappLog'
        db.create_table(u'viewapp_viewapplog', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('time_stamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('error_comment', self.gf('django.db.models.fields.CharField')(max_length=300)),
        ))
        db.send_create_signal(u'viewapp', ['ViewappLog'])


    def backwards(self, orm):
        # Removing unique constraint on 'Tag', fields ['project', 'name']
        db.delete_unique(u'viewapp_tag', ['project_id', 'name'])

        # Removing unique constraint on 'Commit', fields ['project', 'branch', 'commit_hash']
        db.delete_unique(u'viewapp_commit', ['project_id', 'branch_id', 'commit_hash'])

        # Removing unique constraint on 'Branch', fields ['project', 'name']
        db.delete_unique(u'viewapp_branch', ['project_id', 'name'])

        # Removing unique constraint on 'DeveloperBranch', fields ['branch', 'developer']
        db.delete_unique(u'viewapp_developerbranch', ['branch_id', 'developer_id'])

        # Removing unique constraint on 'Developer', fields ['email', 'full_name']
        db.delete_unique(u'viewapp_developer', ['email', 'full_name'])

        # Deleting model 'Developer'
        db.delete_table(u'viewapp_developer')

        # Removing M2M table for field projects on 'Developer'
        db.delete_table(db.shorten_name(u'viewapp_developer_projects'))

        # Deleting model 'Project'
        db.delete_table(u'viewapp_project')

        # Deleting model 'DeveloperBranch'
        db.delete_table(u'viewapp_developerbranch')

        # Deleting model 'Branch'
        db.delete_table(u'viewapp_branch')

        # Deleting model 'Patch'
        db.delete_table(u'viewapp_patch')

        # Deleting model 'Commit'
        db.delete_table(u'viewapp_commit')

        # Deleting model 'Tag'
        db.delete_table(u'viewapp_tag')

        # Removing M2M table for field branches on 'Tag'
        db.delete_table(db.shorten_name(u'viewapp_tag_branches'))

        # Deleting model 'ViewappLog'
        db.delete_table(u'viewapp_viewapplog')


    models = {
        u'viewapp.branch': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Branch'},
            'developers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'developer_branches'", 'blank': 'True', 'through': u"orm['viewapp.DeveloperBranch']", 'to': u"orm['viewapp.Developer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latest_commit': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'latest_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'branches'", 'to': u"orm['viewapp.Project']"}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'total_lines': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_lines_deleted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_lines_inserted': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_patches': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'viewapp.commit': {
            'Meta': {'unique_together': "(('project', 'branch', 'commit_hash'),)", 'object_name': 'Commit'},
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commits'", 'to': u"orm['viewapp.Branch']"}),
            'classification': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'commit_hash': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'developer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commits'", 'to': u"orm['viewapp.Developer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lines_deleted': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'lines_inserted': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commits'", 'to': u"orm['viewapp.Project']"}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'total_files': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'total_lines': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        u'viewapp.developer': {
            'Meta': {'unique_together': "(('email', 'full_name'),)", 'object_name': 'Developer'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'db_index': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kerb_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'latest_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'patches_amount': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'developers'", 'symmetrical': 'False', 'to': u"orm['viewapp.Project']"}),
            'projects_amount': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'work_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        u'viewapp.developerbranch': {
            'Meta': {'unique_together': "(('branch', 'developer'),)", 'object_name': 'DeveloperBranch'},
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['viewapp.Branch']"}),
            'developer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['viewapp.Developer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'viewapp.patch': {
            'Meta': {'object_name': 'Patch'},
            'branch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patches'", 'to': u"orm['viewapp.Branch']"}),
            'classification': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'commit_id': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'developer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patches'", 'to': u"orm['viewapp.Developer']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lines_deleted': ('django.db.models.fields.IntegerField', [], {}),
            'lines_inserted': ('django.db.models.fields.IntegerField', [], {}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patches'", 'to': u"orm['viewapp.Project']"}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'total_files': ('django.db.models.fields.IntegerField', [], {}),
            'total_lines': ('django.db.models.fields.IntegerField', [], {})
        },
        u'viewapp.project': {
            'Meta': {'object_name': 'Project'},
            'being_syncing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_synced_on': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'viewapp.tag': {
            'Meta': {'unique_together': "(('project', 'name'),)", 'object_name': 'Tag'},
            'branches': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'tags'", 'symmetrical': 'False', 'to': u"orm['viewapp.Branch']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': u"orm['viewapp.Project']"}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'viewapp.viewapplog': {
            'Meta': {'object_name': 'ViewappLog'},
            'error_comment': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'time_stamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['viewapp']