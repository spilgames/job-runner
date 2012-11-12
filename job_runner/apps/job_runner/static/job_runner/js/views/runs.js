var RunView = Backbone.View.extend({
    template: _.template($('#run-template').html()),
    runModalTemplate: _.template($('#run-modal-template').html()),

    el: $('#dashboard'),
    events: {
        'click .details': 'showDetails'
    },

    // initialize the view
    initialize: function(options) {
        _.bindAll(this, 'renderItem', 'changeItem', 'initialFetch', 'sortItems', 'showDetails');
        var self = this;

        options.router.on('route:showDashboard', function() {
            $('#job_runner section').addClass('hide');
            $('#dashboard').removeClass('hide');
        });

        this.server_collection = new ServerCollection();
        this.job_collection = new JobCollection();
        this.run_collection = new RunCollection();

        this.run_collection.bind('add', this.renderItem);
        this.run_collection.bind('change', this.changeItem);

        this.server_collection.fetch_all({success: function() {
            self.job_collection.fetch_all({success: function() {
                self.initialFetch();
            }});
        }});

        var socket = new WebSocket(ws_server);
        socket.onerror = function(e) {
            alert('A WebSocket error occured while connecting to ' + item.attributes.hostname);
        };
        socket.onmessage = function(e) {
            console.log(e.data);
            self.handleEvent(JSON.parse(e.data));
        };
    },

    // fetch the initial data
    initialFetch: function() {
        var self = this;

        this.run_collection.fetch_all({
            add: true,
            data: {'state': 'scheduled'}
        });

        this.run_collection.fetch_all({
            add: true,
            data: {'state': 'in_queue'}
        });

        this.run_collection.fetch_all({
            add: true,
            data: {'state': 'started'}
        });

        _(this.job_collection.models).each(function(job) {
            self.run_collection.fetch({
                add: true,
                data: {
                    'job': job.id,
                    'limit': 1,
                    'state': 'completed'
                }
            });
        });
    },

    // callback for when an item has been updated
    changeItem: function(item) {
        var self = this;
        $('#run-' + item.id, self.el).fadeOut('fast', function() {
            $(this).remove();
            self.renderItem(item);
        });
    },

    // callback for showing details of a run
    showDetails: function(e) {
        e.preventDefault();

        var runId = $(e.target.parentNode.parentNode).data('id');
        var run = this.run_collection.get(runId);
        var job = this.job_collection.where({'resource_uri': run.attributes.job})[0];

        $('#modal').html(this.runModalTemplate({
            title: job.attributes.title,
            state: run.humanReadableState(),
            schedule_dts: this.formatDateTime(run.attributes.schedule_dts),
            enqueue_dts: this.formatDateTime(run.attributes.enqueue_dts),
            start_dts: this.formatDateTime(run.attributes.start_dts),
            return_dts: this.formatDateTime(run.attributes.return_dts),
            run_duration: this.formatDuration(run.attributes.start_dts, run.attributes.return_dts),
            script_content: job.attributes.script_content_rendered,
            return_log: run.attributes.return_log
        })).modal();
    },

    // render a run
    renderItem: function(item) {
        var self = this;
        var job = this.job_collection.where({'resource_uri': item.attributes.job})[0];
        var server = this.server_collection.where({'resource_uri': job.attributes.server})[0];

        if (item.state() == 'scheduled') {
            $('#scheduled-runs', self.el).append(self.template({
                id: item.id,
                job_id: job.id,
                state: 'scheduled',
                title: job.attributes.title,
                server: server.attributes.hostname,
                timestamp: self.formatDateTime(item.attributes.schedule_dts)
            }));
            this.sortItems('#scheduled-runs');
        } else if (item.state() == 'in_queue') {
            $('#enqueued-runs', self.el).append(self.template({
                id: item.id,
                job_id: job.id,
                state: 'in-queue',
                title: job.attributes.title,
                server: server.attributes.hostname,
                timestamp: self.formatDateTime(item.attributes.enqueue_dts)
            }));
            this.sortItems('#enqueued-runs');
        } else if (item.state() == 'started') {
            $('#started-runs', self.el).append(self.template({
                id: item.id,
                job_id: job.id,
                state: 'started',
                title: job.attributes.title,
                server: server.attributes.hostname,
                timestamp: self.formatDateTime(item.attributes.start_dts)
            }));
            this.sortItems('#started-runs');
        } else if (item.state() == 'completed') {
            var old = $('#completed-with-error-runs div, #completed-runs div').filter(function() {
                return $(this).data('job_id') == job.id;
            });
            old.fadeOut('slow', function() { old.remove(); });
            $('#completed-runs', self.el).append(self.template({
                id: item.id,
                job_id: job.id,
                state: 'completed',
                title: job.attributes.title,
                server: server.attributes.hostname,
                timestamp: self.formatDateTime(item.attributes.return_dts)
            }));
            this.sortItems('#completed-runs');
        } else if (item.state() == 'completed_with_error') {
            var old = $('#completed-with-error-runs div, #completed-runs div').filter(function() {
                return $(this).data('job_id') == job.id;
            });
            old.fadeOut('slow', function() { old.remove(); });
            $('#completed-with-error-runs', self.el).append(self.template({
                id: item.id,
                job_id: job.id,
                state: 'completed-with-error',
                title: job.attributes.title,
                server: server.attributes.hostname,
                timestamp: self.formatDateTime(item.attributes.return_dts)
            }));
            this.sortItems('#completed-with-error-runs');
        }

        $('#run-'+ item.id).slideDown("slow");
    },

    // sort items based on timestamp
    sortItems: function(column_id) {
        $(column_id +' div').sort(function(a, b) {
            return $(a).data('timestamp') < $(b).data('timestamp') ? 1 : -1;
        }).appendTo(column_id);
    },

    // handle websocket event
    handleEvent: function(event) {
        var self = this;
        var run = this.run_collection.get(event.run_id);
        if (run !== undefined) {
            run.fetch();
        } else {
            run = new Run({'resource_uri': '/api/v1/run/' + event.run_id + '/'});
            run.fetch({success: function() {
                self.run_collection.add(run);

                var job = self.job_collection.where({'resource_uri': run.attributes.job})[0];
                if (job === undefined) {
                    job = new Job({'resource_uri': run.attributes.job});
                    job.fetch({success: function() {
                        self.job_collection.add(job);
                    }});
                }
            }});
        }

        if (event.event == "returned") {
            var scheduled = self.job_collection.where({'enqueue_dts': null});
            self.job_collection.remove(scheduled);
            this.run_collection.fetch({
                add: true,
                data: {'state': 'scheduled'}
            });
        }
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
