var appRouter = new AppRouter();
var runView = new RunView({router: appRouter});
var jobsView = new JobsView({router: appRouter});
Backbone.history.start({pushState: true});
