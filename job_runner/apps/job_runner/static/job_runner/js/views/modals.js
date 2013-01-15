var ModalView = Backbone.View.extend({
    // templates
    runModalTemplate: _.template($('#run-modal-template').html()),

    el: $('#modal'),

    // constructor
    initialize: function(options) {
        _.bindAll(this, 'showRun');
        this.groupCollection = options.groupCollection;
    },

    // show run details
    showRun: function(runId, backUrl) {
        var self = this;

        var run = new Run({'resource_uri': '/api/v1/run/' + runId + '/'});
        run.fetch({success: function() {
            var runLog = new RunLog({'resource_uri': run.attributes.run_log});
            var job = new Job({'resource_uri': run.attributes.job});

            var modalCallback = function() {
                var suspended = job.attributes.enqueue_is_enabled === false && run.attributes.is_manual === false;
                var jobTemplate = new JobTemplate({'resource_uri': job.attributes.job_template});

                jobTemplate.fetch({success: function() {
                    $('#modal').html(self.runModalTemplate({
                        url: run.url(),
                        job_id: job.id,
                        title: job.attributes.title,
                        job_description: job.attributes.description,
                        state: run.humanReadableState(),
                        schedule_dts: formatDateTime(run.attributes.schedule_dts),
                        enqueue_dts: formatDateTime(run.attributes.enqueue_dts),
                        start_dts: formatDateTime(run.attributes.start_dts),
                        return_dts: formatDateTime(run.attributes.return_dts),
                        run_duration: formatDuration(run.attributes.start_dts, run.attributes.return_dts),
                        script_content: _.escape(job.attributes.script_content),
                        return_log: _.escape(runLog.attributes.content),
                        suspended: suspended
                    })).modal().on('hide', function() { appRouter.navigate(backUrl, {'trigger': true}); });

                    _(self.groupCollection.models).each(function(group) {
                        if (jobTemplate.attributes.auth_groups.indexOf(group.attributes.resource_uri) >= 0) {
                            $('#modal .kill-run').removeClass('hide');
                        }
                    });

                    $('#modal .kill-run').click(self.killRun);
                }});
            };

            job.fetch({success: function() {
                if (run.attributes.run_log) {
                    runLog.fetch({success: modalCallback});
                } else {
                    modalCallback();
                }
            }});
        }});
    },

    killRun: function(e) {
        var runUrl = $(e.target.parentNode).data('run_url');

        // firefox
        if (runUrl === undefined) {
            runUrl = $(e.target).data('run_url');
        }
        
        if (confirm('Are you sure you want to kill this run?')) {
            var killRequestCollection = new KillRequestCollection();
            killRequestCollection.create({
                run: runUrl
            }, {
                success: function() {
                    $('#modal .kill-run').addClass('disabled');
                    $('#modal .kill-run i').removeClass('icon-remove').addClass('icon-ok');
                    $('#modal .kill-run span').html('Kill-request has been sent');
                }
            });
        }
    }

});
