"""
This provides a management command that will gather i18n js catalogs.  It reads
each template, and if there is a {% i18n_catalog %} or
{% handlebars_i18n_scripts %} tag it will try to produce a catalog for the app
listed, in each language django supports.  Files go in
STATIC_ROOT/i18n/<app>/<lang>.js

Structure based on compressor's management command.
"""
import io
import os
import re
from fnmatch import fnmatch

from django.conf import settings
from django.utils.encoding import force_text

from django.core.management.base import NoArgsCommand
from django.template import (Context, Template,
                             TemplateDoesNotExist, TemplateSyntaxError)
try:
    from importlib import import_module
except ImportError:
    # Django versions < 1.9
    from django.utils.importlib import import_module

from django.conf.global_settings import LANGUAGES
from handlebars_i18n.views import get_javascript_catalog, render_javascript_catalog
from handlebars_i18n.utils import get_offline_catalog_path

try:
    from django.template.loaders.cached import Loader as CachedLoader
except ImportError:
    CachedLoader = None  # noqa


class Command(NoArgsCommand):
    def handle_noargs(self, **kwargs):
        for app in self.get_apps_to_catalog(**kwargs):
            self.build_catalogs_for_app(app)

    def build_catalogs_for_app(self, app):
        for language in LANGUAGES:
            lang_code = language[0]
            catalog, plural = get_javascript_catalog(lang_code, 'djangojs', [app])
            response = render_javascript_catalog(catalog, plural)

            output_path = get_offline_catalog_path(app, lang_code)
            basedir = os.path.dirname(output_path)
            if not os.path.isdir(basedir):
                os.makedirs(basedir)

            output_handle = io.open(output_path, "w", encoding="utf-8")
            output_handle.write(force_text(response.content))
            output_handle.close()


    def get_apps_to_catalog(self, **options):
        extensions = options.get('extensions') or ['html']
        # Taken from compressor
        paths = set()
        for loader in self.get_loaders():
            try:
                module = import_module(loader.__module__)
                get_template_sources = getattr(module,
                    'get_template_sources', None)
                if get_template_sources is None:
                    get_template_sources = loader.get_template_sources
                paths.update(list(get_template_sources('')))
            except (ImportError, AttributeError):
                # Yeah, this didn't work out so well, let's move on
                pass

        templates = set()
        for path in paths:
            for root, dirs, files in os.walk(path,
                    followlinks=options.get('followlinks', False)):
                templates.update(os.path.join(root, name)
                    for name in files if not name.startswith('.') and
                        any(fnmatch(name, "*%s" % glob) for glob in extensions))


        apps_to_catalog = {}
        for template in templates:
            apps = self.get_apps_from_template(template)
            for app in apps:
                apps_to_catalog[app] = True

        return map(lambda x: x[0], apps_to_catalog.items())

    def get_apps_from_template(self, template):
        found_apps = []

        handle = open(template, "r")
        value = handle.read()

        for match in re.findall(r'{%\s*i18n_catalog\s+"(\S+)"\s*%}', value):
            found_apps.append(match)

        for match in re.findall(r'{%\s*handlebars_i18n_scripts\s+"(\S+)"\s*%}', value):
            found_apps.append(match)

        handle.close()
        return found_apps

    # Taken from compressor's compressor/management/commands/compress.py
    def get_loaders(self):
        from django.template.loader import template_source_loaders
        if template_source_loaders is None:
            try:
                from django.template.loader import (
                    find_template as finder_func)
            except ImportError:
                from django.template.loader import (
                    find_template_source as finder_func)  # noqa
            try:
                # Force django to calculate template_source_loaders from
                # TEMPLATE_LOADERS settings, by asking to find a dummy template
                source, name = finder_func('test')
            except TemplateDoesNotExist:
                pass
            # Reload template_source_loaders now that it has been calculated ;
            # it should contain the list of valid, instanciated template loaders
            # to use.
            from django.template.loader import template_source_loaders
        loaders = []
        # If template loader is CachedTemplateLoader, return the loaders
        # that it wraps around. So if we have
        # TEMPLATE_LOADERS = (
        #    ('django.template.loaders.cached.Loader', (
        #        'django.template.loaders.filesystem.Loader',
        #        'django.template.loaders.app_directories.Loader',
        #    )),
        # )
        # The loaders will return django.template.loaders.filesystem.Loader
        # and django.template.loaders.app_directories.Loader
        for loader in template_source_loaders:
            if CachedLoader is not None and isinstance(loader, CachedLoader):
                loaders.extend(loader.loaders)
            else:
                loaders.append(loader)
        return loaders


