var RunView = Backbone.View.extend({
    template: _.template($('#run-template').html()),
    runModalTemplate: _.template($('#run-modal-template').html()),

    el: $('#dashboard'),
    events: {
        'click .details': 'showDetails'
    },
    
    // initialization
    initialize: function(options) {
        _.bindAll(this, 'renderRun', 'changeRun', 'initialFetch', 'initialFetchRuns', 'sortRuns', 'handleEvent');
        this.activeProject = null;

        this.workerCollection = new WorkerCollection();
        this.jobTemplateCollection = new JobTemplateCollection();
        this.jobCollection = new JobCollection();

        this.runCollection = new RunCollection();
        this.runCollection.bind('add', this.renderRun);
        this.runCollection.bind('change', this.changeRun);

        var self = this;

        // router callback
        options.router.on('route:showDashboard', function(project_id) {
            $('#job_runner section').addClass('hide');
            $('#dashboard').removeClass('hide');
            self.activeProject = options.projectCollection.get(project_id);

            self.workerCollection.reset();
            self.jobTemplateCollection.reset();
            self.jobCollection.reset();
            self.runCollection.reset();

            $('.job-run', self.el).remove();

            self.initialFetch();

            var socket = new WebSocket(ws_server);
            socket.onerror = function(e) {
                alert('A WebSocket error occured while connecting to ' + ws_server);
            };
            socket.onmessage = function(e) {
                console.log(e.data);
                self.handleEvent(JSON.parse(e.data));
            };

        });
    },

    // fetch initial data (based on active project)
    initialFetch: function() {
        var self = this;

        this.workerCollection.fetch_all({
            data: {
                'project__id': self.activeProject.id
            },
            success: function() {
                self.jobTemplateCollection.fetch_all({
                    data: {
                        'worker__project__id': self.activeProject.id
                    },
                    success: function() {
                        self.jobCollection.fetch_all({
                            data: {
                                'job_template__worker__project__id': self.activeProject.id
                            },
                            success: function() {
                                self.initialFetchRuns();
                            }
                        });
                    }
                });
            }
        });
    },

    // fetch initial set of runs (based on active project)
    initialFetchRuns: function() {
        var self = this;

        this.runCollection.fetch_all({
            add: true,
            data: {
                'state': 'scheduled',
                'job__job_template__worker__project__id': self.activeProject.id
            }
        });

        this.runCollection.fetch_all({
            add: true,
            data: {
                'state': 'in_queue',
                'job__job_template__worker__project__id': self.activeProject.id
            }
        });

        this.runCollection.fetch_all({
            add: true,
            data: {
                'state': 'started',
                'job__job_template__worker__project__id': self.activeProject.id
            }
        });

        _(this.jobCollection.models).each(function(job) {
            self.runCollection.fetch({
                add: true,
                data: {
                    'job': job.id,
                    'limit': 1,
                    'state': 'completed'
                }
            });
        });

    },

    // render a run object
    renderRun: function(run) {
        var self = this;
        var job = this.jobCollection.where({'resource_uri': run.attributes.job})[0];
        var jobTemplate = this.jobTemplateCollection.where({'resource_uri': job.attributes.job_template})[0];
        var worker = this.workerCollection.where({'resource_uri': jobTemplate.attributes.worker})[0];

        if (run.state() == 'scheduled') {
            $('#scheduled-runs', self.el).append(self.template({
                id: run.id,
                job_id: job.id,
                state: 'scheduled',
                title: job.attributes.title,
                server: worker.attributes.title,
                timestamp: self.formatDateTime(run.attributes.schedule_dts)
            }));
            this.sortRuns('#scheduled-runs');

        } else if (run.state() == 'in_queue') {
            $('#enqueued-runs', self.el).append(self.template({
                id: run.id,
                job_id: job.id,
                state: 'in-queue',
                title: job.attributes.title,
                server: worker.attributes.title,
                timestamp: self.formatDateTime(run.attributes.enqueue_dts)
            }));
            this.sortRuns('#enqueued-runs');

        } else if (run.state() == 'started') {
            $('#started-runs', self.el).append(self.template({
                id: run.id,
                job_id: job.id,
                state: 'started',
                title: job.attributes.title,
                server: worker.attributes.title,
                timestamp: self.formatDateTime(run.attributes.start_dts)
            }));
            this.sortRuns('#started-runs');

        } else if (run.state() == 'completed') {
            var old = $('#completed-with-error-runs div, #completed-runs div').filter(function() {
                return $(this).data('job_id') == job.id;
            });
            old.fadeOut('slow', function() { old.remove(); });
            $('#completed-runs', self.el).append(self.template({
                id: run.id,
                job_id: job.id,
                state: 'completed',
                title: job.attributes.title,
                server: worker.attributes.title,
                timestamp: self.formatDateTime(run.attributes.return_dts)
            }));
            this.sortRuns('#completed-runs');

        } else if (run.state() == 'completed_with_error') {
            var old = $('#completed-with-error-runs div, #completed-runs div').filter(function() {
                return $(this).data('job_id') == job.id;
            });
            old.fadeOut('slow', function() { old.remove(); });
            $('#completed-with-error-runs', self.el).append(self.template({
                id: run.id,
                job_id: job.id,
                state: 'completed-with-error',
                title: job.attributes.title,
                server: worker.attributes.title,
                timestamp: self.formatDateTime(run.attributes.return_dts)
            }));
            this.sortRuns('#completed-with-error-runs');
        }

        $('#run-'+ run.id).slideDown("slow");

    },

    // callback used when an item has been changed
    changeRun: function(run) {
        var self = this;
        $('#run-' + run.id, self.el).fadeOut('fast', function() {
            $(this).remove();
            self.renderRun(run);
        });
    },

    // sort runs
    sortRuns: function(column_id) {
        $(column_id +' div').sort(function(a, b) {
            return $(a).data('timestamp') < $(b).data('timestamp') ? 1 : -1;
        }).appendTo(column_id);
    },

    // handle websocket event
    handleEvent: function(event) {
        var self = this;
        var run = this.runCollection.get(event.run_id);
        if (run !== undefined) {
            run.fetch();
        } else {
            run = new Run({'resource_uri': '/api/v1/run/' + event.run_id + '/'});
            run.fetch({success: function() {

                var job = self.jobCollection.where({'resource_uri': run.attributes.job})[0];
                if (job === undefined) {
                    job = new Job({'resource_uri': run.attributes.job});
                    job.fetch({success: function() {
                        // make sure that job is within the current active project
                        var jobTemplate = self.jobTemplateCollection.where({resource_uri: job.attributes.job_template})[0];
                        var worker = self.workerCollection.where({resource_uri: jobTemplate.attributes.worker})[0];
                        if (worker.attributes.project == self.activeProject.attributes.resource_uri) {
                            self.jobCollection.add(job);
                            self.runCollection.add(run);
                        }
                    }});
                } else {
                    // when the job is already in the collection, we assume it
                    // was previously checked and is in the current project
                    self.runCollection.add(run);
                }

            }});
        }

        if (event.event == "returned") {
            var scheduled = self.jobCollection.where({'enqueue_dts': null});
            this.jobCollection.remove(scheduled);
            this.runCollection.fetch({
                add: true,
                data: {
                    'state': 'scheduled',
                    'job__job_template__worker__project__id': self.activeProject.id
                }
            });
        }

    },

    // show run details
    showDetails: function(e) {
        e.preventDefault();

        var runId = $(e.target.parentNode.parentNode).data('id');
        var run = this.runCollection.get(runId);
        var job = this.jobCollection.where({'resource_uri': run.attributes.job})[0];

        $('#modal').html(this.runModalTemplate({
            title: job.attributes.title,
            state: run.humanReadableState(),
            schedule_dts: this.formatDateTime(run.attributes.schedule_dts),
            enqueue_dts: this.formatDateTime(run.attributes.enqueue_dts),
            start_dts: this.formatDateTime(run.attributes.start_dts),
            return_dts: this.formatDateTime(run.attributes.return_dts),
            run_duration: this.formatDuration(run.attributes.start_dts, run.attributes.return_dts),
            script_content: job.attributes.script_content,
            return_log: run.attributes.return_log
        })).modal();

    },

    // helper for formatting datetime
    formatDateTime: function(dateString) {
        if (dateString !== null) {
            return moment(dateString).format('YY-MM-DD HH:mm:ss');
        } else {
            return '';
        }
    },

    // helper for formatting the duration
    formatDuration: function(startDTS, endDTS) {
        if (startDTS !== null && endDTS !== null) {
            var start = moment(startDTS);
            var end = moment(endDTS);
            var duration = moment.duration(end.diff(start));

            return duration.days() + ' days, ' + duration.hours() + ' hours, ' + duration.minutes() + ' minutes, ' + duration.seconds() + ' seconds';
        }
    }

});
