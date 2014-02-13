django-handlebars-i18n
======================

Tools for using django translations in handlebars templates, and making it easier to use translations.

To install:

    pip install -e git://github.com/vegitron/django-handlebars-i18n#egg=Django-Handlebars-I18N
    
To use, you need to do the following:

* add 'handlebars_i18n', to your settings.py file's INSTALLED_APPLICATIONS:
* add  url(r'^t18n/', include('handlebars_i18n.urls')), to your project's urls.py file
* Add the following to the page you want to use django translations in handlebars:


    {% load handlebars_i18n %}
    
    {% handlebars_i18n_scripts "app_name" %}

*note: you must have handlebars.js loaded on the page before the handlebars_i18n_scripts template tag*

That will load 2 javascript files onto your page.  One can be compressed the other is (currently) dynamically generated.  To load them separately, you can use

    {% hb_i18_script %}
    {% i18n_catalog "app_name" %}
    
The script is compressable, the catalog is not.

Then in your handlebars templates you can start using the {{ trans }} tag.  

    {{ trans "single value with %(name)s" }}
    
    {{ trans "There is one item" "There are %(count_variable) items" count_variable }}
    
The strings are given the handlebars context, so %(variable)s values will be interpolated.    

Content comes from <app_name>/locale/<language>/LC_MESSAGES/djangojs.po, or if you're compiling message files, djangojs.mo.  For information on how Django determines locale, see https://docs.djangoproject.com/en/dev/topics/i18n/translation/  For more information on the underlying gettext library, and documentation of the .po files, see https://www.gnu.org/software/gettext/manual/
