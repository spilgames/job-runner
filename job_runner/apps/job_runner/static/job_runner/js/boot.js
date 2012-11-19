// notifier
var notifier = new Notifier();

// collections
var groupCollection = new GroupCollection();
var projectCollection = new ProjectCollection();

// pre-fetch all data
groupCollection.fetch_all({success: function() {
    projectCollection.fetch_all({success: function() {

        // router
        var appRouter = new AppRouter();
        
        var projectView = new ProjectView({
            router: appRouter,
            projectCollection: projectCollection
        });

        var runView = new RunView({
            router: appRouter,
            projectCollection: projectCollection,
            notifier: notifier
        });

        var jobView = new JobView({
            router: appRouter,
            groupCollection: groupCollection,
            projectCollection: projectCollection
        });

        Backbone.history.start({pushState: true});

    }});
}});
