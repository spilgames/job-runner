var jobrunnerServices = angular.module('jobrunner.services', ['project', 'job', 'jobTemplate', 'run']);

/*
    Formatters for date/time objects.
*/
jobrunnerServices.value('dtformat', {
    // format the delta between two datetime-stamps.
    formatDuration: function(startDts, endDts) {
        if (startDts !== null && endDts !== null) {
            var start = moment(startDts);
            var end = moment(endDts);
            var duration = moment.duration(end.diff(start));

            return duration.days() + 'd, ' + duration.hours() + 'h, ' + duration.minutes() + 'min, ' + duration.seconds() + 'sec ';
        }
    },

    // get the duration in seconds between two datetime-stamps.
    getDurationInSec: function(startDts, endDts) {
        if (startDts !== null && endDts !== null) {
            var start = moment(startDts);
            var end = moment(endDts);
            var duration = moment.duration(end.diff(start));

            var output = duration.seconds();
            output = output + duration.days() * 24 * 60 * 60;
            output = output + duration.hours() * 60 * 60;
            output = output + duration.minutes() * 60;

            return output;
        }
    },

    // format datetime-stamp.
    formatDateTime: function(dateTimeString) {
        if (dateTimeString !== null) {
            return moment(dateTimeString).format('YYYY-MM-DD HH:mm:ss');
        }
    }

});

/*
    Global cache object.
*/
jobrunnerServices.factory('globalCache', function($cacheFactory) {
    var globalCache = $cacheFactory('globalCache');
    return globalCache;
});


/*
    Global state.
*/
jobrunnerServices.factory('globalState', function(Project, Job, JobTemplate, Run, Worker, globalCache) {
    return {
        data : {
            projectId: null,
            page: null,
            jobTab: 'details',
            jobFilter: {},
            runs: null,
            wsConnected: false
        },

        // initialize the globalState for the given project, after initializing
        // the given callback will be executed.
        initialize: function(projectId, callback) {
            var self = this;

            if (!this.data.projectId || this.data.projectId != projectId) {
                this.data.projectId = projectId;

                // reset all data
                globalCache.removeAll();

                this.data.project = null;
                this.data.jobs = null;
                this.data.jobTemplates = null;
                this.data.runs = null;

                // cache all jobs
                Job.all({project_id: this.data.projectId}, function(jobs) {
                    globalCache.put('job.all', jobs);
                    angular.forEach(jobs, function(job) {
                        globalCache.put('job.' + job.id, job);
                    });

                    // cache all job-templates
                    JobTemplate.all({project_id: self.data.projectId}, function(jobTemplates) {
                        globalCache.put('jobTemplate.all', jobTemplates);
                        angular.forEach(jobTemplates, function(template) {
                            globalCache.put('jobTemplate.' + template.id, template);
                        });

                        // cache all workers
                        Worker.all({project_id: self.data.projectId}, function(workers) {
                            globalCache.put('worker.all', workers);
                            angular.forEach(workers, function(worker) {
                                globalCache.put('worker.' + worker.id, worker);
                            });
                            callback();
                        });
                    });
                });
            } else {
                callback();
            }
        },

        // get the current project object.
        getProject: function() {
            var self = this;
            var project = globalCache.get('project.' + self.data.projectId);
            if (!project) {
                project = Project.get({id: self.data.projectId}, function(project) {
                    globalCache.put('project.' + self.data.projectId);
                });
            }
            return project;
        },

        // get all jobs.
        getAllJobs: function(success) {
            var jobs = globalCache.get('job.all');
            if (!jobs) {
                jobs = Job.all({project_id: this.data.projectId}, function(jobs) {
                    globalCache.put('job.all', jobs);
                    success(jobs);
                });
            } else if (success) {
                success(jobs);
            }
            return jobs;
        },

        // get all job-templates.
        getAllJobTemplates: function() {
            return globalCache.get('jobTemplate.all');
        },

        // get all runs to display at the dashboard.
        getRuns: function() {
            if (this.data.runs) {
                return this.data.runs;
            } else {
                this.data.runs = [];
                var self = this;

                // get all scheduled
                Run.all({state: 'scheduled', project_id: this.data.projectId}, function(scheduled) {
                    angular.forEach(scheduled, function(run) {
                        self.data.runs.push(run);
                    });
                });

                // get all enqueued
                Run.all({state: 'in_queue', project_id: this.data.projectId}, function(inQueue) {
                    angular.forEach(inQueue, function(run) {
                        self.data.runs.push(run);
                    });
                });

                // get all started
                Run.all({state: 'started', project_id: this.data.projectId}, function(started) {
                    angular.forEach(started, function(run) {
                        self.data.runs.push(run);
                    });
                });

                // get for each job the last complated run
                // TODO: make it possible to retrieve this in one call from the
                //       API.
                Job.all({project_id: this.data.projectId}, function(jobs) {
                    angular.forEach(jobs, function(job) {
                        var runs = Run.query({job: job.id, limit: 1, state: 'completed'}, function() {
                            angular.forEach(runs, function(run) {
                                self.data.runs.push(run);
                            });
                        });
                    });
                });

                return this.data.runs;
            }
        }
    };
});
