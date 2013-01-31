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
var JobListCtrl = function($scope, $location, $routeParams, Project, Job, JobTemplate, Worker, Run) {
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

    // show job details
    if ($routeParams.job) {
        $scope.job = Job.get({id: $routeParams.job});
        $scope.recent_runs = Run.all({job: $routeParams.job, state: 'completed', limit: 100});
    }

};


/*
    Controller for selecting projects.
*/
var ProjectCtrl = function($scope, Project) {
    $scope.projects = Project.all();
    $scope.global_state = globalState;
};
