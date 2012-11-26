// base URL
var urlRegex = new RegExp('(\/project\/\\d+\/)');
var baseURL = urlRegex.exec(window.location.href)[1];

// fix navigation links
$('a.js-patch-link').each(function(item, a) {
    $(a).attr('href', baseURL +$(a).attr('href'));
});


// collections
var groupCollection = new GroupCollection();
var projectCollection = new ProjectCollection();

var appRouter = null;

// pre-fetch all data
groupCollection.fetch_all({success: function() {
    projectCollection.fetch_all({success: function() {

        // router
        appRouter = new AppRouter();
        
        var projectView = new ProjectView({
            router: appRouter,
            projectCollection: projectCollection
        });

        var runView = new RunView({
            router: appRouter,
            projectCollection: projectCollection
        });

        var jobView = new JobView({
            router: appRouter,
            groupCollection: groupCollection,
            projectCollection: projectCollection
        });

        Backbone.history.start({pushState: true});

    }});
}});
