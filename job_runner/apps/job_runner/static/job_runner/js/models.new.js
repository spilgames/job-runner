/*
    Get all objects from a paginated resource.
*/
angular.module('getAll', []).factory('getAll', function() {
    var forEach = angular.forEach;
    var extend = angular.extend;

    var getAll = function(output_list, model, offset, params, success, error) {
        var items = model.get(extend({}, params, {offset: offset}), function() {
            forEach(items.objects, function(item) {
                output_list.push(new model(item));
            });

            if (items.meta.next !== null) {
                getAll(output_list, model, items.meta.offset + items.meta.limit, params, success, error);
            } else {
                if (success !== undefined) {
                    success();
                }
            }
        }, error);
    };

    return getAll;
});


/*
    Group model.
*/
angular.module('group', ['ngResource', 'getAll']).factory('Group', function($resource, getAll) {
    var Group = $resource(
        '/api/v1/group/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );

    // Return all group objects
    Group.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Group, 0, params, success, error);
        return output_list;
    };

    return Group;
});


/*
    Project model.
*/
angular.module('project', ['ngResource', 'getAll']).factory('Project', function($resource, getAll) {
    var Project = $resource(
        '/api/v1/project/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );

    // Return all projects
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
angular.module('worker', ['ngResource', 'getAll', 'project']).factory('Worker', function($resource, getAll, Project) {
    var Worker = $resource(
        '/api/v1/worker/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );

    // Return all workers
    Worker.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Worker, 0, params, success, error);
        return output_list;
    };

    // Return the related project
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
angular.module('jobTemplate', ['ngResource', 'getAll', 'worker']).factory('JobTemplate', function($resource, getAll, Worker) {
    var JobTemplate = $resource(
        '/api/v1/job_template/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );

    var relatedCache = {
        workers: {}
    };

    // Return all job-templates
    JobTemplate.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, JobTemplate, 0, params, success, error);
        return output_list;
    };

    // Return the related worker object
    JobTemplate.prototype.get_worker = function() {
        if (relatedCache.workers[this.worker] === undefined && this.worker) {
            relatedCache.workers[this.worker] = Worker.get({'id': this.worker.split('/').splice(-2, 1)[0]});
        }
        return relatedCache.workers[this.worker];
    };

    return JobTemplate;
});


/*
    Job model.
*/
angular.module('job', ['ngResource', 'getAll', 'jobTemplate', 'ngCookies']).factory('Job', function($resource, getAll, JobTemplate, $cookies, $http) {
    // Required by Django and Django-tastypie
    $http.defaults.headers.common['X-CSRFToken'] = $cookies.csrftoken;

    var relatedCache = {
        jobTemplates: {}
    };

    var Job = $resource(
        '/api/v1/job/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'},
            'save': {'method': 'PUT'}
        }
    );

    // Return all jobs
    Job.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Job, 0, params, success);
        return output_list;
    };

    // Return the related job-template
    Job.prototype.get_job_template = function(success) {
        if (relatedCache.jobTemplates[this.job_template] === undefined && this.job_template) {
            relatedCache.jobTemplates[this.job_template] = JobTemplate.get({'id': this.job_template.split('/').splice(-2, 1)[0]}, success);
        } else if (success) {
            success();
        }
        return relatedCache.jobTemplates[this.job_template];
    };

    // Return the parent of this job (if any)
    Job.prototype.get_parent = function() {
        if (!this._parent && this.parent) {
            this._parent = Job.get({id: this.parent.split('/').splice(-2, 1)[0]});
        }
        return this._parent;
    };

    // Return the children of this job (if any)
    Job.prototype.get_children = function() {
        if (!this._children && this.children) {
            var children = [];
            this._children = children;
            angular.forEach(this.children, function(child_uri) {
                children.push(Job.get({id: child_uri.split('/').splice(-2, 1)[0]}));
            });
        }
        return this._children;
    };

    return Job;
});


/*
    Run model.
*/
angular.module('run', ['ngResource', 'getAll', 'job', 'runLog', 'jobrunner.services', 'ngCookies']).factory('Run', function($resource, getAll, Job, RunLog, dtformat, $cookies, $http) {
    // Required by Django and Django-tastypie
    $http.defaults.headers.common['X-CSRFToken'] = $cookies.csrftoken;

    var relatedCache = {
        jobs: {},
        runLogs: {}
    };

    var Run = $resource(
        '/api/v1/run/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'},
            'create': {'method': 'POST'}
        }
    );

    // Return all runs
    Run.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Run, 0, params, success);
        return output_list;
    };

    Run.query = function(params, success, error) {
        var output_list = [];
        var items = Run.get(params, function() {
            angular.forEach(items.objects, function(item) {
                output_list.push(new Run(item));
            });
            success();
        }, error);

        return output_list;
    };

    // Return the related job
    Run.prototype.get_job = function() {
        if (relatedCache.jobs[this.job] === undefined && this.job) {
            relatedCache.jobs[this.job] = Job.get({id:  this.job.split('/').splice(-2, 1)[0]});
        }
        return relatedCache.jobs[this.job];
    };

    // Get run duration in seconds
    Run.prototype.get_duration_sec = function() {
        return dtformat.getDurationInSec(this.start_dts, this.return_dts);
    };

    // Get run duration as a formatted string
    Run.prototype.get_duration_string = function() {
        return dtformat.formatDuration(this.start_dts, this.return_dts);
    };

    // Return the state of the run
    Run.prototype.get_state = function() {
        if (this.enqueue_dts === null) {
            return 'scheduled';
        } else if (this.enqueue_dts !== null && this.start_dts === null) {
            return 'in_queue';
        } else if (this.start_dts !== null && this.return_dts === null) {
            return 'started';
        } else if (this.return_dts !== null && this.return_success === true) {
            return 'completed';
        } else if (this.return_dts !== null && this.return_success === false) {
            return 'completed_with_error';
        }
    };

    // Return the state of the run as a human-readable string
    Run.prototype.get_state_string = function() {
        return {
            'scheduled': 'Scheduled',
            'in_queue': 'In queue',
            'started': 'Started',
            'completed': 'Completed',
            'completed_with_error': 'Completed with error'
        }[this.get_state()];
    };

    // Return the related run-log object (if any)
    Run.prototype.get_run_log = function() {
        if (relatedCache.runLogs[this.run_log] === undefined && this.run_log) {
            relatedCache.runLogs[this.run_log] = RunLog.get({id: this.run_log.split('/').splice(-2, 1)[0]});
        }
        return relatedCache.runLogs[this.run_log];
    };

    return Run;
});


/*
    Run-log model.
*/
angular.module('runLog', ['ngResource', 'getAll']).factory('RunLog', function($resource, getAll) {
    var RunLog = $resource(
        '/api/v1/run_log/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );
    return RunLog;
});
