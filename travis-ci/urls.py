from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^', include('handlebars_i18n.urls')),
)
