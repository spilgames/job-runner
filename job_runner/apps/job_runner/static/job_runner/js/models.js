/*
    Get all objects from a paginated resource.
*/
angular.module('getAll', []).factory('getAll', function() {
    var forEach = angular.forEach;
    var extend = angular.extend;

    var getAll = function(output_list, model, offset, params, success, error) {
        model.get(extend({}, params, {offset: offset}), function(items) {
            forEach(items.objects, function(item) {
                output_list.push(new model(item));
            });

            if (items.meta.next !== null) {
                getAll(output_list, model, items.meta.offset + items.meta.limit, params, success, error);
            } else {
                if (success !== undefined) {
                    success(output_list);
                }
            }
        }, error);
    };

    return getAll;
});


/*
    Decorator to cache get requests.
*/
angular.module('modelCache', []).factory('cachedGet', function() {
    var cachedGet = function(fn, cache, cacheKey) {
        return function(params, success, error) {
            var output = null;

            if (params.id) {
                output = cache.get(cacheKey + '.' + params.id);
            }
            if (!output) {
                output = fn(params, function(obj) {
                    if (params.id) {
                        cache.put(cacheKey + '.' + params.id, obj);
                    }
                    if(success) {
                        success(obj);
                    }
                }, error);
            } else if (success) {
                success(output);
            }
            return output;
        };
    };

    return cachedGet;
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
angular.module('project', ['ngResource', 'getAll', 'modelCache']).factory('Project', function($resource, getAll, globalCache, cachedGet) {
    var Project = $resource(
        '/api/v1/project/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );

    // Decorate get method to add caching.
    Project.get = cachedGet(Project.get, globalCache, 'project');

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
angular.module('worker', ['ngResource', 'getAll', 'project', 'modelCache']).factory('Worker', function($resource, getAll, Project, globalCache, cachedGet) {
    var Worker = $resource(
        '/api/v1/worker/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );

    // Decorate get method to add caching.
    Worker.get = cachedGet(Worker.get, globalCache, 'worker');

    // Return all workers
    Worker.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Worker, 0, params, success, error);
        return output_list;
    };

    // Return the related project
    Worker.prototype.get_project = function() {
        if (this.project) {
            return Project.get({'id': this.project.split('/').splice(-2, 1)[0]});
        }
    };

    return Worker;
});


/*
    Job template model.
*/
angular.module('jobTemplate', ['ngResource', 'getAll', 'worker', 'modelCache']).factory('JobTemplate', function($resource, getAll, Worker, globalCache, cachedGet) {
    var JobTemplate = $resource(
        '/api/v1/job_template/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );

    // Decorate get method to add caching.
    JobTemplate.get = cachedGet(JobTemplate.get, globalCache, 'jobTemplate');

    // Return all job-templates
    JobTemplate.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, JobTemplate, 0, params, success, error);
        return output_list;
    };

    // Return the related worker object
    JobTemplate.prototype.get_worker = function() {
        if (this.worker) {
            var workerId = this.worker.split('/').splice(-2, 1)[0];
            return Worker.get({'id': workerId});
        }
    };

    return JobTemplate;
});


/*
    Job model.
*/
angular.module('job', ['ngResource', 'getAll', 'jobTemplate', 'modelCache', 'ngCookies']).factory('Job', function($resource, getAll, JobTemplate, $cookies, $http, globalCache, cachedGet) {
    // Required by Django and Django-tastypie
    $http.defaults.headers.common['X-CSRFToken'] = $cookies.csrftoken;

    var Job = $resource(
        '/api/v1/job/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'},
            'save': {'method': 'PUT'}
        }
    );

    // Decorate get method to add caching.
    Job.get = cachedGet(Job.get, globalCache, 'job');

    // Return all jobs
    Job.all = function(params, success, error) {
        var output_list = [];
        getAll(output_list, Job, 0, params, success);
        return output_list;
    };

    // Return the related job-template
    Job.prototype.get_job_template = function() {
        if (this.job_template) {
            var templateId = this.job_template.split('/').splice(-2, 1)[0];
            return JobTemplate.get({'id': templateId});
        }
    };

    // Return the parent of this job (if any)
    Job.prototype.get_parent = function() {
        if (this.parent) {
            var parentId = this.parent.split('/').splice(-2, 1)[0];
            return Job.get({id: parentId});
        }
    };

    // Return the children of this job (if any)
    Job.prototype.get_children = function() {
        if (!this._children && this.children) {
            var children = [];
            this._children = children;
            angular.forEach(this.children, function(child_uri) {
                var childId = child_uri.split('/').splice(-2, 1)[0];
                children.push(Job.get({id: childId}));
            });
        }
        return this._children;
    };

    return Job;
});


/*
    Run model.
*/
angular.module('run', ['ngResource', 'getAll', 'job', 'runLog', 'jobrunner.services', 'ngCookies']).factory('Run', function($resource, getAll, Job, RunLog, dtformat, globalCache, $cookies, $http) {
    // Required by Django and Django-tastypie
    $http.defaults.headers.common['X-CSRFToken'] = $cookies.csrftoken;

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
        Run.get(params, function(items) {
            angular.forEach(items.objects, function(item) {
                output_list.push(new Run(item));
            });
            if (success) {
                success(items);
            }
        }, error);

        return output_list;
    };

    // Return the related job
    Run.prototype.get_job = function() {
        if (this.job) {
            var jobId = this.job.split('/').splice(-2, 1)[0];
            return Job.get({id: jobId});
        }
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
        if (!this._run_log && this.run_log) {
            this._run_log = RunLog.get({id: this.run_log.split('/').splice(-2, 1)[0]});
        }
        return this._run_log;
    };

    return Run;
});


/*
    Run-log model.
*/
angular.module('runLog', ['ngResource']).factory('RunLog', function($resource) {
    var RunLog = $resource(
        '/api/v1/run_log/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'}
        }
    );
    return RunLog;
});


/*
    Kill-request model.
*/
angular.module('killRequest', ['ngResource']).factory('KillRequest', function($resource) {
    var KillRequest = $resource(
        '/api/v1/kill_request/:id/',
        {'id': '@id'},
        {
            'get': {'method': 'GET'},
            'create': {'method': 'POST'}
        }
    );
    return KillRequest;
});
