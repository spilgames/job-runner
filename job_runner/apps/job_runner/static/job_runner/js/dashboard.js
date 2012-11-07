(function ($) {
    /*
        Tastypie classes.
    */
    var TastypieModel = Backbone.Model.extend({
        base_url: function() {
            var temp_url = Backbone.Model.prototype.url.call(this);
            return (temp_url.charAt(temp_url.length - 1) == '/' ? temp_url : temp_url + '/');
        },

        url: function() {
            if (this.attributes.resource_uri !== undefined) {
                return this.attributes.resource_uri;
            } else {
                return this.base_url();
            }
        }
    });

    var TastypieCollection = Backbone.Collection.extend({
        parse: function(response) {
            this.recent_meta = response.meta || {};
            return response.objects || response;
        },

        fetch_all: function(options) {
            var self = this;

            if (options === undefined) {
                this.reset();
                options = {'add': true};
            } else {
                options.add = true;
            }

            var success_callback = null;

            if (options.success !== undefined) {
                success_callback = options.success;
            } else {
                success_callback = function() {};
            }

            options.success = function() {
                if (self.recent_meta.next !== null) {
                    if (options.data === undefined) {
                        options.data = {};
                    }

                    options.data.offset = self.recent_meta.offset + self.recent_meta.limit;
                    self.fetch_all(options);
                } else {
                    success_callback();
                }
            };

            self.fetch(options);
        }
    });


    /*
        Models
    */
    var Run = TastypieModel.extend({
        // return the state of the run
        state: function() {
            if (this.attributes.enqueue_dts === null) {
                return 'scheduled';
            } else if (this.attributes.enqueue_dts !== null && this.attributes.start_dts === null) {
                return 'in_queue';
            } else if (this.attributes.start_dts !== null && this.attributes.return_dts === null) {
                return 'started';
            } else if (this.attributes.return_dts !== null && this.attributes.return_success === true) {
                return 'completed';
            } else if (this.attributes.return_dts !== null && this.attributes.return_success === false) {
                return 'completed_with_error';
            }
        },

        // return the human readable state
        humanReadableState: function() {
            return {
                'scheduled': 'Scheduled',
                'in_queue': 'In queue',
                'started': 'Started',
                'completed': 'Completed',
                'completed_with_error': 'Completed with error'
            }[this.state()];
        }
    });

    var Job = TastypieModel.extend();
    var Server = TastypieModel.extend();


    /*
        Collections
    */
    var RunCollection = TastypieCollection.extend({
        model: Run,
        url: '/api/job_runner/v1/run/'
    });

    var JobCollection = TastypieCollection.extend({
        model: Job,
        url: '/api/job_runner/v1/job/'
    });

    var ServerCollection = TastypieCollection.extend({
        model: Server,
        url: '/api/job_runner/v1/server/'
    });


    /*
        Views
    */
    var RunView = Backbone.View.extend({
        template: _.template("<div style='display: none;' class='job-run job-<%= state %>' id='run-<%= id %>' data-id='<%= id %>' data-job_id='<%= job_id %>' data-timestamp='<%= timestamp %>'><h5><a href='#' class='details'><%= title %></a></h5><ul><li><i class='icon-tag'></i> <%= server %></li><li><i class='icon-time'></i> <%= timestamp %></li></ul></div>"),
        el: $('#job_runner'),
        events: {
            'click .details': 'showDetails'
        },

        // initialize the view
        initialize: function(options) {
            _.bindAll(this, 'render', 'renderItem', 'changeItem', 'initialFetch', 'sortItems', 'showDetails');
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

            var modal = $('#run_modal');
            $('#run_modal_title').html(job.attributes.title);
            $('.state', modal).html(run.humanReadableState());
            $('.schedule_dts', modal).html(this.formatDateTime(run.attributes.schedule_dts));
            $('.enqueue_dts', modal).html(this.formatDateTime(run.attributes.enqueue_dts));
            $('.start_dts', modal).html(this.formatDateTime(run.attributes.start_dts));
            $('.return_dts', modal).html(this.formatDateTime(run.attributes.return_dts));
            $('.run_duration', modal).html(this.formatDuration(run.attributes.start_dts, run.attributes.return_dts));
            $('.script_content', modal).html(job.attributes.script_content_rendered);
            $('.return_log', modal).html(run.attributes.return_log);

            $('#run_modal').modal();
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
                run = new Run({'resource_uri': '/api/job_runner/v1/run/' + event.run_id + '/'});
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

    var JobsView = Backbone.View.extend({

        // initialization of the view
        initialize: function(options) {
            options.router.on('route:showJobs', function() {
                $('#job_runner section').addClass('hide');
                $('#jobs').removeClass('hide');
            });
            
        }
    });


    /*
        Application router
    */
    var AppRouter = Backbone.Router.extend({
        routes: {
            '': 'showDashboard',
            'jobs/': 'showJobs'
        },

        initialize: function() {
            $('.js-link').click(function(e){
                e.preventDefault();
                Backbone.history.navigate($(this).attr("href"),true);
            });
        },

        showDashboard: function(e) {

            $('ul.nav li').removeClass('active');
            $('ul.nav li.dashboard').addClass('active');
        },

        showJobs: function() {
            $('ul.nav li').removeClass('active');
            $('ul.nav li.jobs').addClass('active');
        }
    });


    var appRouter = new AppRouter();
    var runView = new RunView({router: appRouter});
    var jobsView = new JobsView({router: appRouter});
    Backbone.history.start({pushState: true});

})(jQuery);
