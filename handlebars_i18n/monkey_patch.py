from __future__ import unicode_literals
from collections import OrderedDict
import locale
import os
import re
import sys
import gettext as gettext_module
from threading import local
import warnings
import codecs

from django.utils.importlib import import_module
from django.core.management.utils import find_command, popen_wrapper
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.encoding import force_str, force_text
from django.utils._os import npath, upath
from django.utils.safestring import mark_safe, SafeData
from django.utils import six
from django.utils.six import StringIO
from django.utils.translation import TranslatorCommentWarning


import django.utils.translation.trans_real

from django.utils.translation.trans_real import to_locale, DjangoTranslation

from django.conf import settings

if settings.DEBUG or getattr(settings, "I18N_RELOAD_ON_CHANGE", False):
    def has_reload_i18n_setting():
        """If DEBUG or I18N_RELOAD_ON_CHANGE is True, return True."""
        from django.conf import settings

        if settings.DEBUG:
            return True

        if getattr(settings, "I18N_RELOAD_ON_CHANGE", False):
            return True

        return False


    def purge_i18n_caches():
        """Removes the local cache, and the gettext cache."""
        global _translations
        _translations = {}

        # gettext chose to do caching at the lowest level possible, and not provide
        # an API for clearing translations. I don't like this, but without a
        # change to gettext, or a local fixed copy, this is the option for keeping
        # files from being cached by path
        gettext_module._translations = {}


    def needs_compilation(domain, path, lang):
        """
    Check to see if a .mo file needs to be compiled. Files need to be compiled
    when DEBUG is true and one of the following conditions is met: the .po file
    is missing, or the .po file is older than the .mo file.
    """
        # Turn off checking for production
        if not has_reload_i18n_setting():
            return False

        mo_file = ".".join([domain, "mo"])
        po_file = ".".join([domain, "po"])
        mo_path = os.path.join(path, lang, "LC_MESSAGES", mo_file)
        po_path = os.path.join(path, lang, "LC_MESSAGES", po_file)

        # If there's no plain text, there's nothing to compile
        if not os.path.exists(po_path):
            return False

        # If there's no compiled version, we do need to compile
        if not os.path.exists(mo_path):
            return True

        # If the plain text is newer than the compiled, we need to compile
        mo_mod = os.path.getmtime(mo_path)
        po_mod = os.path.getmtime(po_path)

        if po_mod > mo_mod:
            return True

        return False


    def compile_messages(domain, path, lang):
        """Compiles a .po file into a .mo file by domain, path, and lang."""
        po_file = ".".join([domain, "po"])
        file_path = os.path.join(path, lang, "LC_MESSAGES", po_file)
        compile_message_file(file_path)


    def compile_message_file(path):
        """Compiles a .po file into a .mo file by path."""
        program = 'msgfmt'
        if find_command(program) is None:
            raise TranslationError("Can't find %s. Make sure you have GNU gettext tools 0.15 or newer installed." % program)

        def _has_bom(fn):
            with open(fn, 'rb') as f:
                sample = f.read(4)
            return sample[:3] == b'\xef\xbb\xbf' or \
                sample.startswith(codecs.BOM_UTF16_LE) or \
                sample.startswith(codecs.BOM_UTF16_BE)

        if _has_bom(path):
            raise TranslationError("The %s file has a BOM (Byte Order Mark). Django only supports .po files encoded in UTF-8 and without any BOM." % path)
        pf = os.path.splitext(path)[0]
        args = [program, '--check-format', '-o', npath(pf + '.mo'), npath(pf + '.po')]
        output, errors, status = popen_wrapper(args)
        if status:
            if errors:
                msg = "Execution of %s failed: %s" % (program, errors)
            else:
                msg = "Execution of %s failed" % program
            raise TranslationError(msg)

    def translation(language):
        """
    Returns a translation object.

    This translation object will be constructed out of multiple GNUTranslations
    objects by merging their catalogs. It will construct a object for the
    requested language and add a fallback to the default language, if it's
    different from the requested language.
    """
        global _translations

        from django.conf import settings

        # If DEBUG is True, disable all caching. needs_compilation needs more
        # info than we have here, but at least it will just be reads
        if has_reload_i18n_setting():
            purge_i18n_caches()

        t = _translations.get(language, None)
        if t is not None:
            return t

        globalpath = os.path.join(os.path.dirname(upath(sys.modules[settings.__module__].__file__)), 'locale')

        def _fetch(lang, fallback=None):

            global _translations

            res = _translations.get(lang, None)
            if res is not None:
                return res

            loc = to_locale(lang)

            def _translation(path):
                try:
                    if needs_compilation('django', path, lang):
                        compile_messages('django', path, lang)
                    t = gettext_module.translation('django', path, [loc], DjangoTranslation)
                    t.set_language(lang)
                    return t
                except IOError:
                    return None

            res = _translation(globalpath)

            # We want to ensure that, for example, "en-gb" and "en-us" don't share
            # the same translation object (thus, merging en-us with a local update
            # doesn't affect en-gb), even though they will both use the core "en"
            # translation. So we have to subvert Python's internal gettext caching.
            base_lang = lambda x: x.split('-', 1)[0]
            if base_lang(lang) in [base_lang(trans) for trans in list(_translations)]:
                res._info = res._info.copy()
                res._catalog = res._catalog.copy()

            def _merge(path):
                t = _translation(path)
                if t is not None:
                    if res is None:
                        return t
                    else:
                        res.merge(t)
                return res

            for appname in reversed(settings.INSTALLED_APPS):
                app = import_module(appname)
                apppath = os.path.join(os.path.dirname(upath(app.__file__)), 'locale')

                if os.path.isdir(apppath):
                    res = _merge(apppath)

            for localepath in reversed(settings.LOCALE_PATHS):
                if os.path.isdir(localepath):
                    res = _merge(localepath)

            if res is None:
                if fallback is not None:
                    res = fallback
                else:
                    return gettext_module.NullTranslations()
            _translations[lang] = res
            return res

        default_translation = _fetch(settings.LANGUAGE_CODE)
        current_translation = _fetch(language, fallback=default_translation)

        return current_translation


    class TranslationError(Exception):
        msg = None

        def __init__(self, msg):
            self.msg = msg
        pass


    django.utils.translation.trans_real.has_reload_i18n_setting = has_reload_i18n_setting
    django.utils.translation.trans_real.purge_i18n_caches = purge_i18n_caches
    django.utils.translation.trans_real.needs_compilation = needs_compilation
    django.utils.translation.trans_real.compile_messages = compile_messages
    django.utils.translation.trans_real.compile_message_file = compile_message_file
    django.utils.translation.trans_real.translation = translation
    django.utils.translation.trans_real.TranslationError = TranslationError


