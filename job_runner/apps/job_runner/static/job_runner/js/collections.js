/*
    Collections
*/
var RunCollection = TastypieCollection.extend({
    model: Run,
    url: '/api/v1/run/'
});

var JobCollection = TastypieCollection.extend({
    model: Job,
    url: '/api/v1/job/'
});

var ServerCollection = TastypieCollection.extend({
    model: Server,
    url: '/api/v1/server/'
});
