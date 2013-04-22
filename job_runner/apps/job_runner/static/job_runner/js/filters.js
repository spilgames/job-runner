var jobrunnerFilters = angular.module('jobrunner.filters', []);

jobrunnerFilters.filter('formatdts', function() {
    return function(dtsString) {
        if (dtsString !== null) {
            return moment(dtsString).format('YYYY-MM-DD HH:mm:ss');
        }
    };
});
