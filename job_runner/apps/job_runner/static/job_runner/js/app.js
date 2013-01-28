var globalState = {
    project: null,
    page: null
};

angular.module('jobrunner', ['project']).config(function($routeProvider, $locationProvider) {
    $locationProvider.html5Mode(true);
    $routeProvider.
        when('/project/:project/runs/', {controller: RunsCtrl, templateUrl: '/static/job_runner/templates/runs.html'}).
        when('/project/:project/jobs/', {controller: JobsCtrl, templateUrl: '/static/job_runner/templates/jobs.html'});
});

var RunsCtrl = function($scope, $location, $routeParams, Project) {
    globalState.project = Project.get({id: $routeParams['project']});
    globalState.page = 'runs';
};

var JobsCtrl = function($scope, $location, $routeParams, Project) {
    globalState.project = Project.get({id: $routeParams['project']});
    globalState.page = 'jobs';
};

var ProjectCtrl = function($scope, Project) {
    $scope.projects = Project.all();
    $scope.global_state = globalState;
};
