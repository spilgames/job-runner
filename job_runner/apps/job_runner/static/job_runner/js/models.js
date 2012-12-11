/*
    Tastypie classes
*/
var TastypieModel = Backbone.Model.extend({
    base_url: function() {
        var temp_url = Backbone.Model.prototype.url.call(this);
        return (temp_url.charAt(temp_url.length - 1) == '/' ? temp_url : temp_url + '/');
    },

    url: function() {
        if (this.attributes.resource_uri !== undefined) {
            return this.attributes.resource_uri;
        } else {
            return this.base_url();
        }
    }
});

var TastypieCollection = Backbone.Collection.extend({
    parse: function(response) {
        this.recent_meta = response.meta || {};
        return response.objects || response;
    },

    fetch_all: function(options) {
        var self = this;

        if (options === undefined) {
            this.reset();
            options = {'add': true};
        } else {
            options.add = true;
        }

        var success_callback = null;

        if (options.success !== undefined) {
            success_callback = options.success;
        } else {
            success_callback = function() {};
        }

        options.success = function() {
            if (self.recent_meta.next !== null) {
                if (options.data === undefined) {
                    options.data = {};
                }

                options.data.offset = self.recent_meta.offset + self.recent_meta.limit;
                self.fetch_all(options);
            } else {
                success_callback();
            }
        };

        self.fetch(options);
    }
});



/*
    Models
*/
var Run = TastypieModel.extend({
    // return the state of the run
    state: function() {
        if (this.attributes.enqueue_dts === null) {
            return 'scheduled';
        } else if (this.attributes.enqueue_dts !== null && this.attributes.start_dts === null) {
            return 'in_queue';
        } else if (this.attributes.start_dts !== null && this.attributes.return_dts === null) {
            return 'started';
        } else if (this.attributes.return_dts !== null && this.attributes.return_success === true) {
            return 'completed';
        } else if (this.attributes.return_dts !== null && this.attributes.return_success === false) {
            return 'completed_with_error';
        }
    },

    // return the human readable state
    humanReadableState: function() {
        return {
            'scheduled': 'Scheduled',
            'in_queue': 'In queue',
            'started': 'Started',
            'completed': 'Completed',
            'completed_with_error': 'Completed with error'
        }[this.state()];
    }
});

var Group = TastypieModel.extend();
var Project = TastypieModel.extend();
var Worker = TastypieModel.extend();
var Job = TastypieModel.extend();
var JobTemplate = TastypieModel.extend();
var KillRequest = TastypieModel.extend();
