var globalState = null;

angular.module('jobrunner', ['project', 'job']).config(function($routeProvider, $locationProvider) {
    globalState = {
        project: null,
        page: null,
        jobs: null,
        job_filter: {}
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
var JobListCtrl = function($scope, $location, $routeParams, Project, Job) {
    globalState.page = 'jobs';
    $scope.global_state = globalState;

    // do some caching of objects
    if (globalState.project && globalState.jobs && globalState.project.id == $routeParams.project) {
        $scope.jobs = globalState.jobs;
    } else {
        globalState.project = Project.get({id: $routeParams['project']}, function() {
            globalState.jobs = Job.all({project_id: globalState.project.id});
            $scope.jobs = globalState.jobs;
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
