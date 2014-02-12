from django.conf.urls import patterns, include, url

urlpatterns = patterns('handlebars_i18n.views',
    url(r'i18n/(?P<packages>\S+)', 'javascript_catalog'),
)
