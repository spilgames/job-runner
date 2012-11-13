var ProjectView = Backbone.View.extend({
    el: $('#project-list'),

    initialize: function(options) {
        _.bindAll(this, 'renderProject');
        var self = this;

        _(options.projectCollection.models).each(function(project) {
            self.renderProject(project);
        });
    },

    renderProject: function(project) {
        $('.dropdown-menu', self.el).append('<li><a href="/project/'+ project.id +'/runs/">'+ project.attributes.title +'</a></li>');
    }

});
