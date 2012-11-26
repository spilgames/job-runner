var AppRouter = Backbone.Router.extend({
    // routes
    routes: {
        '': 'redirectToFirstProject',
        'project/:project/runs/': 'showDashboard',
        'project/:project/runs/:run/': 'showRun',
        'project/:project/jobs/': 'showJobs',
        'project/:project/jobs/:job/': 'showJob'
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

    showDashboard: function(project) {
        this.activateNavigation('dashboard');
        this.updateProjectNav(project);
    },

    showRun: function(project, run_id) {
        this.showDashboard(project);
    },

    showJobs: function(project) {
        this.activateNavigation('jobs');
        this.updateProjectNav(project);
    },

    showJob: function(project, job_id) {
        this.showJobs(project);
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
