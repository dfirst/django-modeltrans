# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Generated by django-modeltrans {version} on {timestamp}
from __future__ import unicode_literals

import inspect
import sys

from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now

from modeltrans import __version__ as VERSION
from modeltrans.utils import split_translated_fieldname

from .settings import DEFAULT_LANGUAGE

try:
    from modeltranslation.translator import translator
    DJANGO_MODELTRANSLATION_AVAILABLE = True
except ImportError:
    DJANGO_MODELTRANSLATION_AVAILABLE = False


def _raise_if_not_django_modeltranslation():
    if not DJANGO_MODELTRANSLATION_AVAILABLE:
        raise ImproperlyConfigured(
            'django-modeltranslation must be still installed when creating'
            'the modeltranslation -> modeltrans migrations.'
        )


def get_translatable_models():
    _raise_if_not_django_modeltranslation()
    return translator.get_registered_models()


def get_translated_fields(Model):
    '''
    Enumerates the translated fields for a model according to django-modeltranslation.
    For example: title_nl, title_en, title_fr, body_nl, body_en, body_fr
    '''
    _raise_if_not_django_modeltranslation()

    options = translator.get_options_for_model(Model)
    for original_field, fields in options.fields.items():
        for translated in fields:
            yield translated.name


def copy_translations(model, fields):
    for m in model.objects.all():
        m.i18n = {}
        for field in fields:
            value = getattr(m, field)
            if value is None:
                continue

            original_field, lang = split_translated_fieldname(field)

            if lang == DEFAULT_LANGUAGE:
                setattr(m, original_field, value)
            else:
                m.i18n[field] = value

        m.save()


class I18nMigration(object):
    helper_functions = (
        split_translated_fieldname,
        copy_translations,
    )

    def __init__(self, app):
        self.models = []
        self.app = app

    def get_helper_functions(self):
        for fn in self.helper_functions:
            yield inspect.getsource(fn)

    def add_model(self, Model, fields):
        self.models.append(
            (Model, fields)
        )

    def write(self, out=None):
        if out is None:
            out = sys.stdout

        from modeltrans import settings

        indexes = '\n'.join(
            [CREATE_INDEX_TEMPLATE.format(table=Model._meta.db_table) for Model, fields in self.models]
        )

        out.write(MIGRATION_TEMPLATE.format(
            version=VERSION,
            DEFAULT_LANGUAGE=settings.DEFAULT_LANGUAGE,
            timestamp=now().strftime('%Y-%m-%d %H:%M'),
            helpers='\n\n'.join(self.get_helper_functions()),
            todo=',\n        '.join([str((Model.__name__, fields)) for Model, fields in self.models]),
            app=self.app,
            last_migration='# TODO: actually fetch this from somewhere',
            indexes=indexes
        ))


CREATE_INDEX_TEMPLATE = '''
        migrations.RunSQL(
            [("CREATE INDEX IF NOT EXISTS {table}_i18n_gin ON {table} USING gin (i18n jsonb_path_ops);", None)],
            [('DROP INDEX {table}_i18n_gin;', None)],
        ),'''

MIGRATION_TEMPLATE = '''
# -*- coding: utf-8 -*-
# Generated by django-modeltrans {version} on {timestamp}

from __future__ import print_function, unicode_literals

from django.db import migrations

DEFAULT_LANGUAGE = '{DEFAULT_LANGUAGE}'


{helpers}

def forwards(apps, schema_editor):
    app = '{app}'
    todo = (
        {todo},
    )

    for model, fields in todo:
        Model = apps.get_model(app, model)

        copy_translations(Model, fields)


class Migration(migrations.Migration):

    dependencies = [
        ('{app}', '{last_migration}'),
    ]

    operations = [
        # The copying of values is (sort of) reversable by a no-op:
        #  - values are copied into i18n (which is not used by anything but django-modeltrans)
        #  - the default language is copied to the orignal field, which was not used
        #    with django-modeltrans.
        migrations.RunPython(forwards, migrations.RunPython.noop),
        {indexes}
    ]
'''
