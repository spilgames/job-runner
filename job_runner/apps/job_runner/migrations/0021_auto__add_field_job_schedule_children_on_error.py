# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Job.schedule_children_on_error'
        db.add_column('job_runner_job', 'schedule_children_on_error',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Job.schedule_children_on_error'
        db.delete_column('job_runner_job', 'schedule_children_on_error')


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
            'Meta': {'ordering': "('job_template__project__title', 'job_template__title', 'title')", 'unique_together': "(('title', 'job_template'),)", 'object_name': 'Job'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'disable_enqueue_after_fails': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'fail_times': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.JobTemplate']"}),
            'last_completed_schedule_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['job_runner.Job']"}),
            'reschedule_interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'reschedule_interval_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'blank': 'True'}),
            'run_on_all_workers': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule_children_on_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'script_content': ('django.db.models.fields.TextField', [], {}),
            'script_content_partial': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'worker_pool': ('smart_selects.db_fields.ChainedForeignKey', [], {'to': "orm['job_runner.WorkerPool']"})
        },
        'job_runner.jobtemplate': {
            'Meta': {'ordering': "('project__title', 'title')", 'object_name': 'JobTemplate'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Project']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'job_runner.killrequest': {
            'Meta': {'object_name': 'KillRequest'},
            'enqueue_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'execute_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'run': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Run']"}),
            'schedule_dts': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'job_runner.project': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Project'},
            'auth_groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'auth_groups_set'", 'blank': 'True', 'to': "orm['auth.Group']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'worker_pools': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['job_runner.WorkerPool']", 'symmetrical': 'False'})
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
            'pid': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'return_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'return_success': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'schedule_children': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'schedule_dts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'schedule_id': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'db_index': 'True'}),
            'start_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Worker']", 'null': 'True', 'blank': 'True'})
        },
        'job_runner.runlog': {
            'Meta': {'ordering': "('-run',)", 'object_name': 'RunLog'},
            'content': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'run': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'run_log'", 'unique': 'True', 'to': "orm['job_runner.Run']"})
        },
        'job_runner.worker': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Worker'},
            'api_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ping_response_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'job_runner.workerpool': {
            'Meta': {'ordering': "('title',)", 'object_name': 'WorkerPool'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'workers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['job_runner.Worker']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['job_runner']