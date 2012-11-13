// collections
var groupCollection = new GroupCollection();
var projectCollection = new ProjectCollection();
var workerCollection = new WorkerCollection();
var jobTemplateCollection = new JobTemplateCollection();
var jobCollection = new JobCollection();


// pre-fetch all data
groupCollection.fetch_all({success: function() {
    projectCollection.fetch_all({success: function() {
        workerCollection.fetch_all({success: function() {
            jobTemplateCollection.fetch_all({success: function() {
                jobCollection.fetch_all({success: function() {

                    // router
                    var appRouter = new AppRouter();
                    
                    var projectView = new ProjectView({
                        router: appRouter,
                        projectCollection: projectCollection
                    });

                    var runView = new RunView({
                        router: appRouter,
                        projectCollection: projectCollection,
                        workerCollection: workerCollection,
                        jobTemplateCollection: jobTemplateCollection,
                        jobCollection: jobCollection
                    });

                    var jobView = new JobView({
                        router: appRouter,
                        groupCollection: groupCollection,
                        projectCollection: projectCollection,
                        workerCollection: workerCollection,
                        jobTemplateCollection: jobTemplateCollection,
                        jobCollection: jobCollection
                    });

                    Backbone.history.start({pushState: true});
                    
                }});
            }});
        }});
    }});
}});
