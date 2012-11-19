// source: https://raw.github.com/0xfe/experiments/master/www/notifyme.html

function Notifier() {}

// Returns "true" if this browser supports notifications.
Notifier.prototype.HasSupport = function() {
    if (window.webkitNotifications) {
        return true;
    } else {
        return false;
    }
};

// Request permission for this page to send notifications. If allowed,
// calls function "cb" with true.
Notifier.prototype.RequestPermission = function(cb) {
    window.webkitNotifications.requestPermission(function() {
        if (cb) { cb(window.webkitNotifications.checkPermission() === 0); }
    });
};

// Popup a notification with icon, title, and body. Returns false if
// permission was not granted.
Notifier.prototype.Notify = function(icon, title, body) {
    if (window.webkitNotifications.checkPermission() === 0) {
        var popup = window.webkitNotifications.createNotification(
            icon, title, body);
        popup.show();

        return true;
    }

    return false;
};
