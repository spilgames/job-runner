var JobView = Backbone.View.extend({
    template: _.template($('#job-template').html()),
    jobModalTemplate: _.template($('#job-modal-template').html()),

    el: $('#jobs'),
    events: {
        'click .details': 'showDetails'
    },

    // initialization of the view
    initialize: function(options) {
        _.bindAll(this, 'renderItem', 'showDetails', 'scheduleJob', 'initialFetch');
        this.activeProject = null;

        this.groupCollection = options.groupCollection;
        this.workerCollection = new WorkerCollection();
        this.jobTemplateCollection = new JobTemplateCollection();
        this.jobCollection = new JobCollection();
        this.jobCollection.bind('add', this.renderItem);

        var self = this;

        options.router.on('route:showJobs', function(project_id) {
            $('#job_runner section').addClass('hide');
            $('#jobs').removeClass('hide');

            self.activeProject = options.projectCollection.get(project_id);
            self.initialFetch();
        });
    },

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
            job_url: job.url()
        })).modal();

        $('.schedule-job').hide();
        _(this.groupCollection.models).each(function(group) {
            if (jobTemplate.attributes.auth_groups.indexOf(group.attributes.resource_uri) >= 0) {
                $('.schedule-job').show();
            }
        });

        $('.schedule-job').click(this.scheduleJob);
    },

    scheduleJob: function(e) {
        if (confirm('Are you sure you want to schedule this job?')) {
            var runCollection = new RunCollection();

            var run = runCollection.create({
                job: $(e.target).data('job_url'),
                schedule_dts: moment.utc().format('YYYY-MM-DD HH:mm:ss')
            }, {
                success: function() {
                    alert('The job has been scheduled.');
                },
                error: function() {
                    alert('The scheduling failed, make sure you have permission to schedule this job.');
                }
            });
        }
    }
});
