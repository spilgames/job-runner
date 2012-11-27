var JobView = Backbone.View.extend({
    template: _.template($('#job-template').html()),
    jobDetailsTemplate: _.template($('#job-details-template').html()),
    jobDetailsRunRowTemplate: _.template($('#job-details-run-row-template').html()),

    el: $('#jobs'),

    // initialization of the view
    initialize: function(options) {
        _.bindAll(this, 'renderItem', 'changeItem', 'showJob', 'sortJobs', 'showRuns', 'scheduleJob', 'initialFetch', 'toggleJobIsEnabled', 'initializeView');
        this.activeProject = null;
        this.initialized = false;
        this.selectedJobId = null;

        this.groupCollection = options.groupCollection;
        this.workerCollection = new WorkerCollection();
        this.jobTemplateCollection = new JobTemplateCollection();
        this.jobCollection = new JobCollection();
        this.jobCollection.bind('add', this.renderItem);
        this.jobCollection.bind('change', this.changeItem);


        var self = this;

        // router callback
        options.router.on('route:showJobs', function(projectId) {
            self.initializeView(options, projectId);
        });

        options.router.on('route:showJob', function(projectId, jobId) {
            self.selectedJobId = jobId;
            self.initializeView(options, projectId);
            self.showJob(jobId);
        });

        options.router.on('route:showRunInJobView', function(projectId, jobId, runId) {
            self.selectedJobId = jobId;
            self.initializeView(options, projectId);
            self.showJob(jobId);
            options.modalView.showRun(runId);
        });
    },

    // initialize the view for the given project_id
    initializeView: function(options, project_id) {
        var self = this;

        $('#job_runner section').addClass('hide');
        $('#jobs').removeClass('hide');

        if (!this.initialized) {
            self.activeProject = options.projectCollection.get(project_id);
            self.workerCollection.reset();
            self.jobTemplateCollection.reset();
            self.jobCollection.reset();
            $('.jobs div.span2', self.el).remove();
            self.initialFetch();
            self.initialized = true;
        }
    },

    // fetch data (based on active project)
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
                            }
                        });
                    }
                });
            }
        });
    },

    // render a job
    renderItem: function(job) {
        var jobTemplate = this.jobTemplateCollection.where({'resource_uri': job.attributes.job_template})[0];
        var worker = this.workerCollection.where({'resource_uri': jobTemplate.attributes.worker})[0];

        $('#jobs .jobs').append(this.template({
            id: job.id,
            title: job.attributes.title,
            hostname: worker.attributes.title,
            enqueue_is_enabled: job.attributes.enqueue_is_enabled
        }));
        this.sortJobs();

        if (this.selectedJobId == job.id) {
            $('#job-' + job.id + ' > div').addClass('selected');
        }

        $('#job-'+ job.id).show();
    },

    // update a job
    changeItem: function(job) {
        var self = this;
        $('#job-' + job.id, self.el).remove();
        self.renderItem(job);
    },

    // sort jobs
    sortJobs: function() {
        $('.jobs > div', this.el).sort(function(a, b) {
            return $('div h5', $(a)).text() > $('div h5', $(b)).text() ? 1 : -1;
        }).appendTo('#jobs .jobs');
    },

    // show job details
    showJob: function(jobId) {
        var self = this;

        $('.jobs > div > div', this.el).removeClass('selected');
        $('#job-' + jobId + ' > div').addClass('selected');

        // do nothing if the job is already displayed
        if ($('#job-details').data('job_id') == jobId) {
            return;
        }

        var job = new Job({'resource_uri': '/api/v1/job/' + jobId + '/'});
        job.fetch({success: function() {
            var jobTemplate = new JobTemplate({'resource_uri': job.attributes.job_template});
            jobTemplate.fetch({success: function() {

                $('#job-details').html(self.jobDetailsTemplate({
                    title: job.attributes.title,
                    enqueue_is_enabled: job.attributes.enqueue_is_enabled,
                    script_content: _.escape(job.attributes.script_content),
                    children: job.attributes.children,
                    job_url: job.url(),
                    id: job.id
                }));

                $('#job-details').data('job_id', jobId);

                if (job.attributes.enqueue_is_enabled === true) {
                    $('.toggle-enable-job').addClass('btn-danger');
                    $('.toggle-enable-job span').html('Suspend enqueue');
                } else {
                    $('.toggle-enable-job').addClass('btn-success');
                    $('.toggle-enable-job span').html('Enable enqueue');
                }
         
                $('.schedule-job').hide();
                $('.toggle-enable-job').hide();

                _(self.groupCollection.models).each(function(group) {
                    if (jobTemplate.attributes.auth_groups.indexOf(group.attributes.resource_uri) >= 0) {
                        $('.schedule-job').show();
                        $('.toggle-enable-job').show();
                    }
                });

                $('.schedule-job').click(self.scheduleJob);
                $('.toggle-enable-job').click(self.toggleJobIsEnabled);
                $('.show-runs').click(self.showRuns);

            }});
        }});
    },

    // show the historic runs
    showRuns: function(e) {
        var fetched = $(e.target).data('fetched');
        var self = this;

        if (!fetched) {
            var runCollection = new RunCollection();

            runCollection.fetch({
                data: {
                    state: 'completed',
                    job: $(e.target).data('job_id'),
                    limit: 100
                },
                success: function() {
                    var chartData = [['Run', 'Duration (seconds)']];

                    _(runCollection.models).each(function(run) {
                        chartData.push([formatDateTime(run.attributes.start_dts), getDurationInSec(run.attributes.start_dts, run.attributes.return_dts)]);

                        $('#tab2 tbody').append(self.jobDetailsRunRowTemplate({
                            job_id: $(e.target).data('job_id'),
                            id: run.id,
                            return_success: run.attributes.return_success,
                            start_dts: formatDateTime(run.attributes.start_dts),
                            duration: formatDuration(run.attributes.start_dts, run.attributes.return_dts)
                        }));
                    });

                    chartData = google.visualization.arrayToDataTable(chartData);

                    var chart = new google.visualization.AreaChart(document.getElementById('run-performance-graph'));
                    chart.draw(chartData, {
                        'axisTitlesPosition': 'none',
                        'legend': {'position': 'none'},
                        'hAxis': {'direction': -1, 'textPosition': 'none', 'gridlines': {'count': 0}},
                        'vAxis': {'gridlines': {'count': 3}}
                    });

                }
            });
            $(e.target).data('fetched', true);
        }
    },

    // callback for toggeling the enqueue_is_enabled attribute of a job
    toggleJobIsEnabled: function(e) {
        var jobId = $(e.target.parentNode).data('job_id');

        // firefox
        if (jobId === undefined) {
            jobId = $(e.target).data('job_id');
        }

        var job = this.jobCollection.get(jobId);

        if (job.attributes.enqueue_is_enabled === true) {
            if (confirm('Are you sure you want to suspend the enqueueing of this job? If suspended, the job will not be added to the worker queue. This will not affect already running jobs.')) {
                job.save({enqueue_is_enabled: false}, {success: function() {
                    job.fetch();
                    $('.toggle-enable-job').removeClass('btn-danger');
                    $('.toggle-enable-job').addClass('btn-success');
                    $('.toggle-enable-job span').html('Enable enqueue');
                }});
            }
        } else {
            if (confirm('Are you sure you want to enable the enqueueing of this job?')) {
                job.save({enqueue_is_enabled: true}, {success: function() {
                    job.fetch();
                    $('.toggle-enable-job').removeClass('btn-success');
                    $('.toggle-enable-job').addClass('btn-danger');
                    $('.toggle-enable-job span').html('Suspend enqueue');
                }});
            }
        }
    },

    // callback for scheduling a job
    scheduleJob: function(e) {
        var jobUrl = $(e.target.parentNode).data('job_url');
        var scheduleChildren = $(e.target.parentNode).data('schedule_children');

        // firefox
        if (jobUrl === undefined) {
            jobUrl = $(e.target).data('job_url');
            scheduleChildren = $(e.target).data('schedule_children');
        }

        if (confirm('Are you sure you want to schedule this job?')) {
            var runCollection = new RunCollection();
            var run = runCollection.create({
                job: jobUrl,
                is_manual: true,
                schedule_children: scheduleChildren,
                schedule_dts: moment().format('YYYY-MM-DD HH:mm:ss')
            }, {
                success: function() {
                    $('.schedule-job i').removeClass('icon-play').addClass('icon-ok');
                    $('.schedule-job span').html('Job scheduled');
                    $('.schedule-job-group button').attr('disabled', 'disabled');
                }
            });
        }
    }
});
