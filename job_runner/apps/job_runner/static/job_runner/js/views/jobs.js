var JobsView = Backbone.View.extend({
    template: _.template($('#job-template').html()),
    jobModalTemplate: _.template($('#job-modal-template').html()),

    el: $('#jobs'),
    events: {
        'click .details': 'showDetails'
    },

    // initialization of the view
    initialize: function(options) {
        var self = this;

        _.bindAll(this, 'renderItem', 'showDetails');

        options.router.on('route:showJobs', function() {
            $('#job_runner section').addClass('hide');
            $('#jobs').removeClass('hide');
        });
        
        this.job_collection = new JobCollection();
        this.server_collection = new ServerCollection();
        this.job_collection.bind('add', this.renderItem);

        this.server_collection.fetch_all({success: function() {
            self.job_collection.fetch_all();
        }});

    },

    // render a job
    renderItem: function(item) {
        var server = this.server_collection.where({'resource_uri': item.attributes.server})[0];

        $('#jobs .jobs').append(this.template({
            id: item.id,
            title: item.attributes.title,
            hostname: server.attributes.hostname
        }));

    },

    // show job details
    showDetails: function(e) {
        e.preventDefault();

        var JobId = $(e.target.parentNode.parentNode).data('id');
        var job = this.job_collection.get(JobId);

        $('#modal').html(this.jobModalTemplate({
            title: job.attributes.title,
            script_content: job.attributes.script_content_rendered
        })).modal();
    }
});
