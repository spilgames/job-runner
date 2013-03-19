# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        """
        This will migrate the old project->worker->job-template->job structure
        to the new structure of worker pools.
        """
        for worker in orm['job_runner.Worker'].objects.all():
            # create a worker-pool for every worker
            worker_pool = orm['job_runner.WorkerPool'].objects.create(
                title=worker.title,
                enqueue_is_enabled=worker.enqueue_is_enabled,
                notification_addresses=worker.notification_addresses,
            )
            # add the worker to the pool
            worker_pool.workers.add(worker)
            worker_pool.save()

            project = worker.project
            # add the worker-pool to the project
            project.worker_pools.add(worker_pool)
            project.save()

            job_templates = orm['job_runner.JobTemplate'].objects.filter(
                worker=worker)

            # loop over ever job-template for the worker
            for job_template in job_templates:
                # link the job-template to the project
                job_template.project = project
                job_template.save()

                for auth_group in job_template.auth_groups.all():
                    project.auth_groups.add(auth_group)
                project.save()

                for job in job_template.job_set.all():
                    # link the worker-pool to the job
                    job.worker_pool = worker_pool
                    job.save()

    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")

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
            'Meta': {'ordering': "('job_template__worker__project__title', 'job_template__worker__title', 'job_template__title', 'title')", 'unique_together': "(('title', 'job_template'),)", 'object_name': 'Job'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'disable_enqueue_after_fails': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'fail_times': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.JobTemplate']"}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['job_runner.Job']"}),
            'reschedule_interval': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'reschedule_interval_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'blank': 'True'}),
            'reschedule_type': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '18', 'blank': 'True'}),
            'script_content': ('django.db.models.fields.TextField', [], {}),
            'script_content_partial': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'worker_pool': ('smart_selects.db_fields.ChainedForeignKey', [], {'to': "orm['job_runner.WorkerPool']"})
        },
        'job_runner.jobtemplate': {
            'Meta': {'ordering': "('worker__project__title', 'worker__title', 'title')", 'object_name': 'JobTemplate'},
            'auth_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Project']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Worker']"})
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
            'start_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'})
        },
        'job_runner.runlog': {
            'Meta': {'ordering': "('-run',)", 'object_name': 'RunLog'},
            'content': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'run': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'run_log'", 'unique': 'True', 'to': "orm['job_runner.Run']"})
        },
        'job_runner.worker': {
            'Meta': {'ordering': "('project__title', 'title')", 'object_name': 'Worker'},
            'api_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ping_response_dts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['job_runner.Project']"}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'job_runner.workerpool': {
            'Meta': {'object_name': 'WorkerPool'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'enqueue_is_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_addresses': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'workers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['job_runner.Worker']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['job_runner']
    symmetrical = True
