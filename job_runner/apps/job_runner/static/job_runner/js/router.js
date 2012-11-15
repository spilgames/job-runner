var AppRouter = Backbone.Router.extend({
    routes: {
        '': 'redirectToFirstProject',
        'project/:project/runs/': 'showDashboard',
        'project/:project/jobs/': 'showJobs'
    },

    initialize: function() {
        $('.js-link').click(function(e){
            e.preventDefault();
            Backbone.history.navigate(this.pathname, true);
        });
    },

    redirectToFirstProject: function(e) {
        window.location.href = '/project/'+ projectCollection.models[0].id + '/runs/';
    },

    activateNavigation: function(name) {
        $('header ul.nav li').removeClass('active');
        $('header ul.nav li.'+ name).addClass('active');
    },

    updateProjectNav: function(project_id) {
        var project = projectCollection.get(project_id);
        $('#project-list span').html(project.attributes.title);
    },

    showDashboard: function(project) {
        this.activateNavigation('dashboard');
        this.updateProjectNav(project);
    },

    showJobs: function(project) {
        this.activateNavigation('jobs');
        this.updateProjectNav(project);
    }
});
