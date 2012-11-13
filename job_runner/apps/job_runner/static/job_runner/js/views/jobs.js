var JobView = Backbone.View.extend({
    template: _.template($('#job-template').html()),
    jobModalTemplate: _.template($('#job-modal-template').html()),

    el: $('#jobs'),
    events: {
        'click .details': 'showDetails'
    },

    // initialization of the view
    initialize: function(options) {
        var self = this;

        _.bindAll(this, 'renderItem', 'showDetails', 'scheduleJob');

        options.router.on('route:showJobs', function() {
            $('#job_runner section').addClass('hide');
            $('#jobs').removeClass('hide');
        });
        
        this.groupCollection = options.groupCollection;
        this.workerCollection = options.workerCollection;
        this.jobTemplateCollection = options.jobTemplateCollection;
        this.jobCollection = options.jobCollection;

        _(this.jobCollection.models).each(function(job) {
            self.renderItem(job);
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
