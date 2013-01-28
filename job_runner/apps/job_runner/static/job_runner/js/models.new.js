angular.module('project', ['ngResource']).factory('Project', function($resource) {
    var Project = $resource('/api/v1/project/:id/', {'id': '@id'});

    Project.all = function() {
        var forEach = angular.forEach;
        var value = [];
        var projects = Project.get(function() {
            forEach(projects.objects, function(project) {
                value.push(new Project(project));
            });
        });

        return value;
    };

    return Project;
});
