var appModule = angular.module('jobrunner', ['jobrunner.filters', 'jobrunner.services', 'project', 'job', 'jobTemplate', 'worker', 'workerPool', 'run', 'group', 'killRequest', 'ngCookies', 'LocalStorageModule']);

appModule.config(function($routeProvider, $locationProvider) {
    // this will make it possible to use deeplinks without "#"
    $locationProvider.html5Mode(true);

    // setup URL routes
    $routeProvider.
        when('/', {controller: RedirectToProjectCtrl, templateUrl: '/static/job_runner/templates/runs.html'}).
        when('/no-projects/', {controller: NoProjectsCtrl, templateUrl: '/static/job_runner/templates/no_projects.html'}).
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

        // update scheduled runs, if our run was enqueued or returned
        if (data.event == 'enqueued' || data.event == 'returned') {
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
            if (value.id != run.id && value.job == run.job && value.schedule_id != run.schedule_id && (run.get_state() == 'completed' || run.get_state() == 'completed_with_error') && (value.get_state() == 'completed' || value.get_state() == 'completed_with_error')) {
                toPop.push(value);
            }

            // cleanup scheduled run on all workers runs
            if (value.schedule_id == run.schedule_id && value.worker === null && run.worker !== null) {
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

        // get an instance of the run and make sure it belongs to one of the
        // jobs we are aware of (so we can assume it is within the selected
        // project).
        Run.get({id: data.run_id}, function(run) {
            globalState.getAllJobs(function(jobs) {
                angular.forEach(jobs, function(job) {
                    if (job.resource_uri == run.job) {
                        handleRunUpdate(run, data);
                    }
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
