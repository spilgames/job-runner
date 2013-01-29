var globalState = null;

angular.module('jobrunner', ['project', 'job']).config(function($routeProvider, $locationProvider) {
    globalState = {
        project: null,
        page: null
    };

    $locationProvider.html5Mode(true);

    $routeProvider.
        when('/project/:project/runs/', {controller: RunsCtrl, templateUrl: '/static/job_runner/templates/runs.html'}).
        when('/project/:project/jobs/', {controller: JobListCtrl, templateUrl: '/static/job_runner/templates/job_list.html'});

});

var RunsCtrl = function($scope, $location, $routeParams, Project) {
    globalState.project = Project.get({id: $routeParams['project']});
    globalState.page = 'runs';
};

var JobListCtrl = function($scope, $location, $routeParams, Project, Job) {
    globalState.page = 'jobs';
    $scope.global_state = globalState;

    globalState.project = Project.get({id: $routeParams['project']}, function() {
        $scope.jobs = Job.all({project_id: globalState.project.id});
    });

};

var ProjectCtrl = function($scope, Project) {
    $scope.projects = Project.all();
    $scope.global_state = globalState;
};
