# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Developer.work_type'
        db.delete_column(u'viewapp_developer', 'work_type')


    def backwards(self, orm):
        # Adding field 'Developer.work_type'
        db.add_column(u'viewapp_developer', 'work_type',
                      self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True),
                      keep_default=False)


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
            'total_files': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'})
        },
        u'viewapp.developer': {
            'Meta': {'unique_together': "(('email', 'full_name'),)", 'object_name': 'Developer'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'db_index': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kerb_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'latest_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'patches_amount': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'projects': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'developers'", 'symmetrical': 'False', 'to': u"orm['viewapp.Project']"})
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