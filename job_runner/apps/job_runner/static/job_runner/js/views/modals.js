var ModalView = Backbone.View.extend({
    // templates
    runModalTemplate: _.template($('#run-modal-template').html()),

    el: $('#modal'),

    // constructor
    initialize: function(options) {
        _.bindAll(this, 'showRun');
    },

    // show run details
    showRun: function(runId) {
        var self = this;

        var run = new Run({'resource_uri': '/api/v1/run/' + runId + '/'});
        run.fetch({success: function() {
            var job = new Job({'resource_uri': run.attributes.job});
            job.fetch({success: function() {
                var suspended = job.attributes.enqueue_is_enabled === false && run.attributes.is_manual === false;

                $('#modal').html(self.runModalTemplate({
                    job_id: job.id,
                    title: job.attributes.title,
                    state: run.humanReadableState(),
                    schedule_dts: formatDateTime(run.attributes.schedule_dts),
                    enqueue_dts: formatDateTime(run.attributes.enqueue_dts),
                    start_dts: formatDateTime(run.attributes.start_dts),
                    return_dts: formatDateTime(run.attributes.return_dts),
                    run_duration: formatDuration(run.attributes.start_dts, run.attributes.return_dts),
                    script_content: _.escape(job.attributes.script_content),
                    return_log: _.escape(run.attributes.return_log),
                    suspended: suspended
                })).modal().on('hide', function() { history.back(); });

            }});
        }});
    }

});
