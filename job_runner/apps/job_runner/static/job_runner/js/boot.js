google.load("visualization", "1", {packages:["corechart"]});

// base URL
var urlRegex = new RegExp('(\/project\/\\d+\/)');
var urlRegexMatch = urlRegex.exec(window.location.href);
var baseURL = '';

if (urlRegexMatch) {
    baseURL = urlRegexMatch[1];
}

// fix navigation links
$('a.js-patch-link').each(function(item, a) {
    $(a).attr('href', baseURL +$(a).attr('href'));
});


// collections
var groupCollection = new GroupCollection();
var projectCollection = new ProjectCollection();

// pre-fetch all data
groupCollection.fetch_all({success: function() {
    projectCollection.fetch_all({success: function() {

        // router
        var appRouter = new AppRouter();

        // modal view
        var modalView = new ModalView();
        
        var projectView = new ProjectView({
            router: appRouter,
            projectCollection: projectCollection
        });

        var runView = new RunView({
            router: appRouter,
            projectCollection: projectCollection,
            modalView: modalView
        });

        var jobView = new JobView({
            router: appRouter,
            groupCollection: groupCollection,
            projectCollection: projectCollection,
            modalView: modalView
        });

        Backbone.history.start({pushState: true});

    }});
}});
