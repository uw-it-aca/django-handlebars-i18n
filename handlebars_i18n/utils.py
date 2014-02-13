from django.conf import settings
import os

def get_offline_catalog_path(app, language):
    file_name = "%s.js" % language
    output_path = os.path.join(settings.STATIC_ROOT, "i18n", app, file_name)

    return output_path

def has_offline_catalog_file(app, language):
    path = get_offline_catalog_path(app, language)
    return os.path.isfile(path)


def get_offline_catalog_url(app, language):
    return "%si18n/%s/%s.js" % (settings.STATIC_URL, app, language)

