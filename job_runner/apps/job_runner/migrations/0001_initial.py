# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Project'
        db.create_table('job_runner_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('notification_addresses', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('job_runner', ['Project'])

        # Adding M2M table for field groups on 'Project'
        db.create_table('job_runner_project_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('project', models.ForeignKey(orm['job_runner.project'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('job_runner_project_groups', ['project_id', 'group_id'])

        # Adding model 'Worker'
        db.create_table('job_runner_worker', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('api_key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['job_runner.Project'])),
            ('notification_addresses', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('job_runner', ['Worker'])

        # Adding model 'JobTemplate'
        db.create_table('job_runner_jobtemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('worker', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['job_runner.Worker'])),
            ('notification_addresses', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('job_runner', ['JobTemplate'])

        # Adding M2M table for field auth_groups on 'JobTemplate'
        db.create_table('job_runner_jobtemplate_auth_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('jobtemplate', models.ForeignKey(orm['job_runner.jobtemplate'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('job_runner_jobtemplate_auth_groups', ['jobtemplate_id', 'group_id'])

        # Adding model 'Job'
        db.create_table('job_runner_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['job_runner.Job'])),
            ('job_template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['job_runner.JobTemplate'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('script_content_partial', self.gf('django.db.models.fields.TextField')()),
            ('script_content', self.gf('django.db.models.fields.TextField')()),
            ('reschedule_interval', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('reschedule_interval_type', self.gf('django.db.models.fields.CharField')(max_length=6, blank=True)),
            ('reschedule_type', self.gf('django.db.models.fields.CharField')(max_length=18, blank=True)),
            ('notification_addresses', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('job_runner', ['Job'])

        # Adding model 'RescheduleExclude'
        db.create_table('job_runner_rescheduleexclude', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['job_runner.Job'])),
            ('start_time', self.gf('django.db.models.fields.TimeField')()),
            ('end_time', self.gf('django.db.models.fields.TimeField')()),
        ))
        db.send_create_signal('job_runner', ['RescheduleExclude'])

        # Adding model 'Run'
        db.create_table('job_runner_run', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('job', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['job_runner.Job'])),
            ('schedule_dts', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('enqueue_dts', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('start_dts', self.gf('django.db.models.fields.DateTimeField')(null=True, db_index=True)),
            ('return_dts', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('return_success', self.gf('django.db.models.fields.NullBooleanField')(default=None, null=True, blank=True)),
            ('return_log', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
        ))
        db.send_create_signal('job_runner', ['Run'])


    def backwards(self, orm):
        # Deleting model 'Project'
        db.delete_table('job_runner_project')

        # Removing M2M table for field groups on 'Project'
        db.delete_table('job_runner_project_groups')

        # Deleting model 'Worker'
        db.delete_table('job_runner_worker')

        # Deleting model 'JobTemplate'
        db.delete_table('job_runner_jobtemplate')

        # Removing M2M table for field auth_groups on 'JobTemplate'
        db.delete_table('job_runner_jobtemplate_auth_groups')

        # Deleting model 'Job'
        db.delete_table('job_runner_job')

        # Deleting model 'RescheduleExclude'
        db.delete_table('job_runner_rescheduleexclude')

        # Deleting model 'Run'
        db.delete_table('job_runner_run')


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
            'Meta': {'object_name': 'Job'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.JobTemplate']"}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['job_runner.Job']"}),
            'reschedule_interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'reschedule_interval_type': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'reschedule_type': ('django.db.models.fields.CharField', [], {'max_length': '18', 'blank': 'True'}),
            'script_content': ('django.db.models.fields.TextField', [], {}),
            'script_content_partial': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'job_runner.jobtemplate': {
            'Meta': {'object_name': 'JobTemplate'},
            'auth_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Worker']"})
        },
        'job_runner.project': {
            'Meta': {'object_name': 'Project'},
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
            'start_time': ('django.db.models.fields.TimeField', [], {})
        },
        'job_runner.run': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'Run'},
            'enqueue_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Job']"}),
            'return_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'return_log': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'return_success': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'schedule_dts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'start_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'})
        },
        'job_runner.worker': {
            'Meta': {'object_name': 'Worker'},
            'api_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Project']"}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['job_runner']