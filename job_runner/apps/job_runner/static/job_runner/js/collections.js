/*
    Collections
*/
var RunCollection = TastypieCollection.extend({
    model: Run,
    url: '/api/job_runner/v1/run/'
});

var JobCollection = TastypieCollection.extend({
    model: Job,
    url: '/api/job_runner/v1/job/'
});

var ServerCollection = TastypieCollection.extend({
    model: Server,
    url: '/api/job_runner/v1/server/'
});
