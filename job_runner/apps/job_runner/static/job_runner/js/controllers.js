/*
    Controller for runs.
*/
var RunsCtrl = function($scope, $routeParams, Project, Run, Job, globalState) {
    $scope.global_state = globalState;
    globalState.data.page = 'runs';
    globalState.setProjectId($routeParams.project);
    
    $scope.runFilter = function(state) {
        return function(run) {
            return (run.get_state() == state);
        };
    };

    $scope.runs = globalState.getRuns();

};


/*
    Controller for jobs.
*/
var JobListCtrl = function($scope, $routeParams, Project, Job, JobTemplate, Worker, Run, Group, globalState, dtformat) {
    globalState.data.page = 'jobs';
    globalState.setProjectId($routeParams.project);
    $scope.global_state = globalState;
    $scope.jobs = globalState.getAllJobs();
    $scope.job_templates = globalState.getAllJobTemplates();

    // function for displaying job details
    $scope.showDetails = function() {
        globalState.data.jobTab = 'details';
    };

    // function for displaying recent runs of a job
    $scope.showRecentRuns = function() {
        globalState.data.jobTab = 'runs';

        // get recent runs and build the chart
        $scope.recent_runs = Run.all({job: $routeParams.job, state: 'completed', limit: 100}, function() {
            var chartData = [['Run', 'Duration (seconds)']];

            angular.forEach($scope.recent_runs, function(run) {
                chartData.push([dtformat.formatDateTime(run.start_dts), run.get_duration_sec()]);
            });

            chartData = google.visualization.arrayToDataTable(chartData);
            var chart = new google.visualization.AreaChart(document.getElementById('run-performance-graph'));
            chart.draw(chartData, {
                'axisTitlesPosition': 'none',
                'legend': {'position': 'none'},
                'hAxis': {'direction': -1, 'textPosition': 'none', 'gridlines': {'count': 0}},
                'vAxis': {'gridlines': {'count': 3}}
            });

        });
    };

    // show job details
    if ($routeParams.job) {
        $scope.job = Job.get({id: $routeParams.job});
        if (globalState.data.jobTab == 'runs') {
            // make sure that we update the recent runs
            $scope.showRecentRuns();
        }
    }

    // show run details
    if ($routeParams.run) {
        $scope.run = Run.get({id: $routeParams.run}, function() {
            // is there a better way?
            $('#modal').modal().on('hide', function() { history.go(-1); });
        });
    }

};


/*
    Controller which redirects to the first project.
*/
var RedirectToFirstProjectCtrl = function($location, Project) {
    var projects = Project.all({}, function() {
        if (projects.length > 0) {
            $location.path('/project/'+ projects[0].id +'/runs/');
        }
    });
};


/*
    Controller for selecting projects.
*/
var ProjectCtrl = function($scope, $routeParams, Project, globalState) {
    $scope.project = Project.get({id: $routeParams.project});
    $scope.projects = Project.all();
    $scope.global_state = globalState;
};


/*
    Controller for job actions.
*/
var JobActionCtrl = function($scope, $routeParams, $route, Job, Group, Run) {
    // set $scope.auth_permissions to true if the user has auth permissions
    // for the given jobId.
    var getPermissionsForJob = function(jobId) {
        $scope.job = Job.get({id: jobId}, function() {
            var jobTemplate = $scope.job.get_job_template(function() {
                var groups = Group.all({}, function() {
                    angular.forEach(groups, function(group) {
                        if(jobTemplate.auth_groups.indexOf(group.resource_uri) >= 0) {
                            $scope.auth_permissions = true;
                        }
                    });
                });
            });
        });


    };

    // function for scheduling a job
    $scope.scheduleNow = function(withChildren) {
        if (confirm('Are you sure you want to schedule this job?')) {
            var newRun = new Run({
                job: $scope.job.resource_uri,
                is_manual: true,
                schedule_children: withChildren,
                schedule_dts: moment().format('YYYY-MM-DD HH:mm:ss')
            });
            newRun.$create(function() {
                $scope.scheduled_run = newRun;
            });
        }
    };

    // function for setting enqueue_is_enabled attribute on job model
    $scope.toggleEnqueue = function(toValue) {
        if (toValue === true) {
            if (confirm('Are you sure you want to enable the enqueueing of this job?')) {
                $scope.job.enqueue_is_enabled = toValue;
                $scope.job.$save(function(){
                    globalState.jobs = null;
                    $route.reload();
                });
            }
        } else if (toValue === false) {
            if (confirm('Are you sure you want to suspend the enqueueing of this job? If suspended, the job will not be added to the worker queue. This will not affect already running jobs.')) {
                $scope.job.enqueue_is_enabled = toValue;
                $scope.job.$save(function() {
                    globalState.jobs = null;
                    $route.reload();
                });
            }
        }
    };

    if ($routeParams.job !== undefined) {
        getPermissionsForJob($routeParams.job);
    }
};
