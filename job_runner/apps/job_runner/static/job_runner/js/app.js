angular.module('jobrunner', ['jobrunner.filters', 'jobrunner.services', 'project', 'job', 'jobTemplate', 'worker', 'run', 'group', 'killRequest']).config(function($routeProvider, $locationProvider) {
    // this will make it possible to use deeplinks without "#"
    $locationProvider.html5Mode(true);

    // setup URL routes
    $routeProvider.
        when('/', {controller: RedirectToFirstProjectCtrl, templateUrl: '/static/job_runner/templates/runs.html'}).
        when('/project/:project/runs/', {controller: RunsCtrl, templateUrl: '/static/job_runner/templates/runs.html'}).
        when('/project/:project/runs/:run/', {controller: RunsCtrl, templateUrl: '/static/job_runner/templates/runs.html'}).
        when('/project/:project/jobs/', {controller: JobListCtrl, templateUrl: '/static/job_runner/templates/jobs.html'}).
        when('/project/:project/jobs/:job/', {controller: JobListCtrl, templateUrl: '/static/job_runner/templates/jobs.html'}).
        when('/project/:project/jobs/:job/runs/:run/', {controller: JobListCtrl, templateUrl: '/static/job_runner/templates/jobs.html'});
}).run(function(globalState, Run) {
    // handle run update
    var handleRunUpdate = function(run, data) {
        var pushRun = true;
        var toPop = [];

        // update scheduled runs, if our run completed
        if (data.event == 'returned') {
            Run.all({state: 'scheduled', project_id: globalState.data.projectId}, function(scheduled) {
                angular.forEach(scheduled, function(run) {
                    var inList = false;
                    angular.forEach(globalState.data.runs, function(r) {
                        if (r.resource_uri == run.resource_uri) {
                            inList = true;
                        }
                    });
                    if (inList === false) {
                        globalState.data.runs.push(run);
                    }
                });
            });
        }

        // update the run, if we already have it in cache
        angular.forEach(globalState.data.runs, function(value, index) {
            if (value.id == run.id) {
                pushRun = false;
                globalState.data.runs[index] = run;
            }

            // remove old completed runs
            if (value.id != run.id && value.job == run.job && (run.get_state() == 'completed' || run.get_state() == 'completed_with_error') && (value.get_state() == 'completed' || value.get_state() == 'completed_with_error')) {
                toPop.push(value);
            }
        });

        // cleanup old items
        angular.forEach(toPop, function(value) {
            var index = globalState.data.runs.indexOf(value);
            globalState.data.runs.splice(index, 1);
        });

        if (pushRun) {
            globalState.data.runs.push(run);
        }
    };


    // handle incoming events from the WebSocket server
    var handleEvent = function(data) {
        // if we don't have a list of runs, it means the user is currently
        // at an other page and doesn't have any runs cached
        if (globalState.runs === null) {
            return;
        }

        // ignore events other than "run"
        if (data.kind != 'run') {
            return;
        }

        Run.get({id: data.run_id}, function(run) {
            run.get_job(function(job) {
                job.get_job_template(function(template) {
                    template.get_worker(function(worker) {
                        worker.get_project(function(project) {
                            if (project.id == globalState.data.projectId) {
                                handleRunUpdate(run, data);
                            }
                        });
                    });
                });
            });

        });
    };

    // setup WebSocket connection in the background
    var connectWebSocket = function () {
        var socket = new WebSocket(ws_server);

        socket.onopen = function() {
            globalState.data.wsConnected = true;
        };

        socket.onclose = function() {
            globalState.data.wsConnected = false;
            setTimeout(connectWebSocket, 1000);
        };

        socket.onmessage = function(e) {
            console.log(e.data);
            handleEvent(JSON.parse(e.data));
        };
    };

    connectWebSocket();
});
