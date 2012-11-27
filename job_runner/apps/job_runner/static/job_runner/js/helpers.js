// helper for formatting datetime
var formatDateTime = function(dateString) {
    if (dateString !== null) {
        return moment(dateString).format('YY-MM-DD HH:mm:ss');
    } else {
        return '';
    }
};

// helper for formatting the duration
var formatDuration = function(startDTS, endDTS) {
    if (startDTS !== null && endDTS !== null) {
        var start = moment(startDTS);
        var end = moment(endDTS);
        var duration = moment.duration(end.diff(start));

        return duration.days() + 'd, ' + duration.hours() + 'h, ' + duration.minutes() + 'min, ' + duration.seconds() + 'sec ';
    }
};

// helper for getting the duration in seconds
var getDurationInSec = function(startDTS, endDTS) {
    if (startDTS !== null && endDTS !== null) {
        var start = moment(startDTS);
        var end = moment(endDTS);
        var duration = moment.duration(end.diff(start));

        var output = duration.seconds();
        output = output + duration.days() * 24 * 60 * 60;
        output = output + duration.hours() * 60 * 60;
        output = output + duration.minutes() * 60;

        return output;
    }
};
