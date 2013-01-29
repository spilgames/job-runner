/*
    Get all objects from a paginated resource.
*/
angular.module('getAll', []).factory('getAll', function() {
    var forEach = angular.forEach;
    var extend = angular.extend;

    var getAll = function(output_list, model, offset, params, success, error) {
        var items = model.get(extend({}, params, {offset: offset}, success, error), function() {
            forEach(items.objects, function(item) {
                output_list.push(new model(item));
            });

            if (items.meta.next !== null) {
                getAll(output_list, model, items.meta.offset + items.meta.limit, params, success, error);
            }
        });
    };

    return getAll;
});


/*
    Project model.
*/
angular.module('project', ['ngResource', 'getAll']).factory('Project', function($resource, getAll) {
    var Project = $resource('/api/v1/project/:id/', {'id': '@id'});

    Project.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Project, 0, params, success, error);
        return output_list;
    };

    return Project;
});


/*
    Worker model.
*/
angular.module('worker', ['ngResource', 'project']).factory('Worker', function($resource, Project) {
    var Worker = $resource('/api/v1/worker/:id/', {'id': '@id'});

    Worker.prototype.get_project = function() {
        if (!this._project && this.project) {
            this._project = Project.get({'id': this.project.split('/').splice(-2, 1)[0]});
        }
        return this._project;
    };

    return Worker;
});


/*
    Job template model.
*/
angular.module('jobTemplate', ['ngResource', 'worker']).factory('JobTemplate', function($resource, Worker) {
    var JobTemplate = $resource('/api/v1/job_template/:id/', {'id': '@id'});

    JobTemplate.prototype.get_worker = function() {
        if (!this._worker && this.worker) {
            this._worker = Worker.get({'id': this.worker.split('/').splice(-2, 1)[0]});
        }
        return this._worker;
    };

    return JobTemplate;
});


/*
    Job model.
*/
angular.module('job', ['ngResource', 'getAll', 'jobTemplate']).factory('Job', function($resource, getAll, JobTemplate) {
    var Job = $resource('/api/v1/job/:id/', {'id': '@id'});

    Job.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Job, 0, params, success);
        return output_list;
    };

    Job.prototype.get_job_template = function() {
        if (!this._job_template && this.job_template) {
            this._job_template = JobTemplate.get({'id': this.job_template.split('/').splice(-2, 1)[0]});
        }
        return this._job_template;
    };

    return Job;
});
