var AppRouter = Backbone.Router.extend({
    routes: {
        '': 'showDashboard',
        'jobs/': 'showJobs'
    },

    initialize: function() {
        $('.js-link').click(function(e){
            e.preventDefault();
            Backbone.history.navigate($(this).attr("href"),true);
        });
    },

    showDashboard: function(e) {
        $('header ul.nav li').removeClass('active');
        $('header ul.nav li.dashboard').addClass('active');
    },

    showJobs: function() {
        $('header ul.nav li').removeClass('active');
        $('header ul.nav li.jobs').addClass('active');
    }
});
