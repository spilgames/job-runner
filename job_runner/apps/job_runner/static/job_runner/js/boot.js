// collections
var projectCollection = new ProjectCollection();

// projects
projectCollection.fetch_all({success: function() {

    // router
    var appRouter = new AppRouter();

    var projectView = new ProjectView({
        router: appRouter,
        projectCollection: projectCollection
    });

    // var runView = new RunView({router: appRouter});
    // var jobsView = new JobsView({router: appRouter});
    Backbone.history.start({pushState: true});

}});

