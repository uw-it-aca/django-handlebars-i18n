from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def hb_i18_script():
    return """<script src="%shandlebars-i18n/js/handlebars-i18n.js"></script>""" % settings.STATIC_URL

