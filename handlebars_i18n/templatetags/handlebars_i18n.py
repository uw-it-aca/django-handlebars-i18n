from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def hb_i18_script():
    return """<script src="%shandlebars-i18n/js/handlebars-i18n.js"></script>""" % settings.STATIC_URL

@register.simple_tag
def i18n_catalog(app):
    return """<script src="%s"></script>""" % reverse('handlebars_i18n.views.javascript_catalog', kwargs= { "packages": app })


@register.simple_tag
def handlebars_i18n_scripts(app):
    return "".join([hb_i18_script(), i18n_catalog(app)])

