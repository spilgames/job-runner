/*
    Collections
*/
var GroupCollection = TastypieCollection.extend({
    model: Group,
    url: '/api/v1/group/'
});

var ProjectCollection = TastypieCollection.extend({
    model: Project,
    url: '/api/v1/project/'
});

var WorkerCollection = TastypieCollection.extend({
    model: Worker,
    url: '/api/v1/worker/'
});

var JobTemplateCollection = TastypieCollection.extend({
    model: JobTemplate,
    url: '/api/v1/job_template/'
});

var JobCollection = TastypieCollection.extend({
    model: Job,
    url: '/api/v1/job/'
});

var RunCollection = TastypieCollection.extend({
    model: Run,
    url: '/api/v1/run/'
});

var KillRequestCollection = TastypieCollection.extend({
    model: KillRequest,
    url: '/api/v1/kill_request/'
});
