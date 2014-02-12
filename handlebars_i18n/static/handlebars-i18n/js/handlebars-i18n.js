// Adds a helper for django's i18n js api
Handlebars.registerHelper("trans", function() {
    switch(arguments.length) {
        case 1:
            // No text to translate
            return no_trans_key(arguments[0]);
        case 2:
            // A single translation key
            return single(arguments[0], arguments[1]);
        case 3:
            // An invalid plural - treat it like it's single
            return single(arguments[0], arguments[2]);
        case 4:
            // Proper plural
            return plural(arguments[0], arguments[1], arguments[2], arguments[3]);
        default:
            // Something else - just return something empty.
            return no_trans_key({});
    };

    function no_trans_key() {
        return "";
    }

    function single(key, obj) {
        var base = gettext(key);
        return interpolate(base, obj.data, true);
    }

    function plural(key1, key2, count, obj) {
        var base = ngettext(key1, key2, count);
        return interpolate(base, obj.data, true);
    }

});
