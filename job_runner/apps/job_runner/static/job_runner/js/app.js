var globalState = null;

angular.module('jobrunner', ['project', 'job', 'jobTemplate', 'worker']).config(function($routeProvider, $locationProvider) {
    globalState = {
        project: null,
        page: null,
        jobs: null,
        job_templates: null,
        job_filter: {
            reschedule_interval_type: ''
        }
    };

    $locationProvider.html5Mode(true);

    $routeProvider.
        when('/project/:project/runs/', {controller: RunsCtrl, templateUrl: '/static/job_runner/templates/runs.html'}).
        when('/project/:project/jobs/', {controller: JobListCtrl, templateUrl: '/static/job_runner/templates/job_list.html'}).
        when('/project/:project/jobs/:job/', {controller: JobListCtrl, templateUrl: '/static/job_runner/templates/job_list.html'});

});


/*
    Controller for runs.
*/
var RunsCtrl = function($scope, $location, $routeParams, Project) {
    globalState.page = 'runs';
    globalState.project = Project.get({id: $routeParams['project']});
};


/*
    Controller for jobs.
*/
var JobListCtrl = function($scope, $location, $routeParams, Project, Job, JobTemplate, Worker) {
    globalState.page = 'jobs';
    $scope.global_state = globalState;

    // do some caching of objects
    if (globalState.project && globalState.jobs && globalState.job_templates && globalState.project.id == $routeParams.project) {
        $scope.jobs = globalState.jobs;
        $scope.job_templates = globalState.job_templates;
    } else {
        globalState.project = Project.get({id: $routeParams['project']}, function() {
            globalState.jobs = Job.all({project_id: globalState.project.id});
            globalState.job_templates = JobTemplate.all({project_id: globalState.project.id});
            globalState.workers = Worker.all({project_id: globalState.project.id});
            $scope.jobs = globalState.jobs;
            $scope.job_templates = globalState.job_templates;
        });
    }

    // show job details
    if ($routeParams.job) {
        $scope.job = Job.get({id: $routeParams.job});
    }

};


/*
    Controller for selecting projects.
*/
var ProjectCtrl = function($scope, Project) {
    $scope.projects = Project.all();
    $scope.global_state = globalState;
};
