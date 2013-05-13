appModule.directive('markdown', function($interpolate) {
    var converter = new Showdown.converter();
    return {
        restrict: 'E',
        compile: function(element, attrs) {
            var exp = $interpolate(element.text());
            return function(scope, element, attrs) {
                scope.$watch(exp, function(newValue, oldValue) {
                    var htmlText = converter.makeHtml(newValue);
                    element.html(htmlText);
                });
            };
        }
    };
});
