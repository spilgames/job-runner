var JobView = Backbone.View.extend({
    template: _.template($('#job-template').html()),
    jobModalTemplate: _.template($('#job-modal-template').html()),

    el: $('#jobs'),
    events: {
        'click .details': 'showDetails'
    },

    // initialization of the view
    initialize: function(options) {
        _.bindAll(this, 'renderItem', 'showDetails', 'scheduleJob', 'initialFetch', 'toggleJobIsEnabled');
        this.activeProject = null;

        this.groupCollection = options.groupCollection;
        this.workerCollection = new WorkerCollection();
        this.jobTemplateCollection = new JobTemplateCollection();
        this.jobCollection = new JobCollection();
        this.jobCollection.bind('add', this.renderItem);

        var self = this;

        // router callback
        options.router.on('route:showJobs', function(project_id) {
            $('#job_runner section').addClass('hide');
            $('#jobs').removeClass('hide');

            self.activeProject = options.projectCollection.get(project_id);
            self.workerCollection.reset();
            self.jobTemplateCollection.reset();
            self.jobCollection.reset();
            $('.jobs div.span2', self.el).remove();
            self.initialFetch();
        });
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
            hostname: worker.attributes.title
        }));
        $('#job-'+ job.id).slideDown("slow");

    },

    // show job details
    showDetails: function(e) {
        e.preventDefault();

        var JobId = $(e.target.parentNode.parentNode).data('id');
        var job = this.jobCollection.get(JobId);
        var jobTemplate = this.jobTemplateCollection.where({'resource_uri': job.attributes.job_template})[0];

        $('#modal').html(this.jobModalTemplate({
            title: job.attributes.title,
            script_content: job.attributes.script_content,
            job_url: job.url(),
            id: job.id
        })).modal();

        if (job.attributes.is_enabled === true) {
            $('.toggle-enable-job').addClass('btn-danger');
            $('.toggle-enable-job span').html('Disable');
        } else {
            $('.toggle-enable-job').addClass('btn-success');
            $('.toggle-enable-job span').html('Enable');
        }
 
        $('.schedule-job').hide();
        $('.toggle-enable-job').hide();

        _(this.groupCollection.models).each(function(group) {
            if (jobTemplate.attributes.auth_groups.indexOf(group.attributes.resource_uri) >= 0) {
                $('.schedule-job').show();
                $('.toggle-enable-job').show();
            }
        });

        $('.schedule-job').click(this.scheduleJob);
        $('.toggle-enable-job').click(this.toggleJobIsEnabled);
    },

    // callback for toggeling the is_enabled attribute of a job
    toggleJobIsEnabled: function(e) {
        var jobId = $(e.target.parentNode).data('job_id');
        var job = this.jobCollection.get(jobId);

        if (job.attributes.is_enabled === true) {
            if (confirm('Are you sure you want to disable this job?')) {
                job.attributes.is_enabled = false;
                job.save({}, {success: function() {
                    $('.toggle-enable-job').removeClass('btn-danger');
                    $('.toggle-enable-job').addClass('btn-success');
                    $('.toggle-enable-job span').html('Enable');
                }});
            }
        } else {
            if (confirm('Are you suse you want to enable this job?')) {
                job.attributes.is_enabled = true;
                job.save({}, {success: function() {
                    $('.toggle-enable-job').removeClass('btn-success');
                    $('.toggle-enable-job').addClass('btn-danger');
                    $('.toggle-enable-job span').html('Disable');
                }});
            }
        }
    },

    // callback for scheduling a job
    scheduleJob: function(e) {
        if (confirm('Are you sure you want to schedule this job?')) {
            var runCollection = new RunCollection();

            var run = runCollection.create({
                job: $(e.target.parentNode).data('job_url'),
                schedule_dts: moment.utc().format('YYYY-MM-DD HH:mm:ss')
            }, {
                success: function() {
                    $('.schedule-job i').removeClass('icon-play').addClass('icon-ok');
                    $('.schedule-job span').html('Job scheduled');
                    $('.schedule-job').attr('disabled', 'disabled');
                },
                error: function() {
                    alert('The scheduling failed, make sure you have permission to schedule this job.');
                }
            });
        }
    }
});
