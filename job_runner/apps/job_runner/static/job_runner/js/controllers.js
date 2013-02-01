/*
    Controller for runs.
*/
var RunsCtrl = function($scope, $location, $routeParams, Project) {
    globalState.page = 'runs';
    globalState.project = Project.get({id: $routeParams.project});
};


/*
    Controller for jobs.
*/
var JobListCtrl = function($scope, $location, $routeParams, Project, Job, JobTemplate, Worker, Run, dtformat) {
    globalState.page = 'jobs';
    $scope.global_state = globalState;

    // do some caching of objects
    if (globalState.project && globalState.jobs && globalState.job_templates && globalState.project.id == $routeParams.project) {
        $scope.jobs = globalState.jobs;
        $scope.job_templates = globalState.job_templates;
    } else {
        globalState.project = Project.get({id: $routeParams.project}, function() {
            globalState.jobs = Job.all({project_id: globalState.project.id});
            globalState.job_templates = JobTemplate.all({project_id: globalState.project.id});
            globalState.workers = Worker.all({project_id: globalState.project.id});
            $scope.jobs = globalState.jobs;
            $scope.job_templates = globalState.job_templates;
        });
    }

    $scope.showDetails = function() {
        globalState.job_tab = 'details';
    };

    // function for displaying recent runs of a job
    $scope.showRecentRuns = function() {
        globalState.job_tab = 'runs';

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
        if (globalState.job_tab == 'runs') {
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
    Controller for selecting projects.
*/
var ProjectCtrl = function($scope, Project) {
    $scope.projects = Project.all();
    $scope.global_state = globalState;
};
