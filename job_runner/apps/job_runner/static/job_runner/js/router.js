var AppRouter = Backbone.Router.extend({
    // routes
    routes: {
        '': 'redirectToFirstProject',
        'project/:project/runs/': 'showDashboard',
        'project/:project/runs/:run/': 'showRunInRunView',
        'project/:project/jobs/': 'showJobs',
        'project/:project/jobs/:job/': 'showJob',
        'project/:project/jobs/:job/runs/:run/': 'showRunInJobView'
    },

    // constructor
    initialize: function() {
        $('.js-link').live('click', function(e){
            e.preventDefault();
            Backbone.history.navigate(this.pathname, true);
        });
    },

    ////
    // route callbacks
    ////

    redirectToFirstProject: function(e) {
        window.location.href = '/project/'+ projectCollection.models[0].id + '/runs/';
    },

    showDashboard: function(projectId) {
        this.activateNavigation('dashboard');
        this.updateProjectNav(projectId);
    },

    showRunInRunView: function(projectId, runId) {
        this.showDashboard(projectId);
    },

    showJobs: function(projectId) {
        this.activateNavigation('jobs');
        this.updateProjectNav(projectId);
    },

    showJob: function(projectId, jobId) {
        this.showJobs(projectId);
    },

    showRunInJobView: function(projectId, jobId, runId) {
        this.showJobs(projectId);
    },


    ////
    // helpers
    ////
    activateNavigation: function(name) {
        $('header ul.nav li').removeClass('active');
        $('header ul.nav li.'+ name).addClass('active');
    },

    updateProjectNav: function(project_id) {
        var project = projectCollection.get(project_id);
        $('#project-list span').html(project.attributes.title);
    }

});
