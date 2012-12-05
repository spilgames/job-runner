# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Job', fields ['reschedule_type']
        db.create_index('job_runner_job', ['reschedule_type'])

        # Adding index on 'Job', fields ['reschedule_interval_type']
        db.create_index('job_runner_job', ['reschedule_interval_type'])

        # Adding index on 'Run', fields ['return_success']
        db.create_index('job_runner_run', ['return_success'])

        # Adding index on 'Run', fields ['return_dts']
        db.create_index('job_runner_run', ['return_dts'])

        # Adding index on 'Run', fields ['enqueue_dts']
        db.create_index('job_runner_run', ['enqueue_dts'])


    def backwards(self, orm):
        # Removing index on 'Run', fields ['enqueue_dts']
        db.delete_index('job_runner_run', ['enqueue_dts'])

        # Removing index on 'Run', fields ['return_dts']
        db.delete_index('job_runner_run', ['return_dts'])

        # Removing index on 'Run', fields ['return_success']
        db.delete_index('job_runner_run', ['return_success'])

        # Removing index on 'Job', fields ['reschedule_interval_type']
        db.delete_index('job_runner_job', ['reschedule_interval_type'])

        # Removing index on 'Job', fields ['reschedule_type']
        db.delete_index('job_runner_job', ['reschedule_type'])


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'job_runner.job': {
            'Meta': {'ordering': "('title',)", 'unique_together': "(('title', 'job_template'),)", 'object_name': 'Job'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.JobTemplate']"}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['job_runner.Job']"}),
            'reschedule_interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'reschedule_interval_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'blank': 'True'}),
            'reschedule_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '18', 'blank': 'True'}),
            'script_content': ('django.db.models.fields.TextField', [], {}),
            'script_content_partial': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'job_runner.jobtemplate': {
            'Meta': {'object_name': 'JobTemplate'},
            'auth_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Worker']"})
        },
        'job_runner.project': {
            'Meta': {'object_name': 'Project'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'job_runner.rescheduleexclude': {
            'Meta': {'object_name': 'RescheduleExclude'},
            'end_time': ('django.db.models.fields.TimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Job']"}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.TimeField', [], {})
        },
        'job_runner.run': {
            'Meta': {'ordering': "('-return_dts', '-start_dts', '-enqueue_dts', 'schedule_dts')", 'object_name': 'Run'},
            'enqueue_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_manual': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Job']"}),
            'return_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'return_log': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'return_success': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'schedule_children': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'schedule_dts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'start_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'})
        },
        'job_runner.worker': {
            'Meta': {'object_name': 'Worker'},
            'api_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Project']"}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['job_runner']