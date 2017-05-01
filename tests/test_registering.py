# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase

from modeltrans.exceptions import AlreadyRegistered
from modeltrans.manager import (MultilingualManager, MultilingualQuerySet,
                                get_translatable_fields_for_model)
from modeltrans.translator import TranslationOptions, translator
from tests.app.models import Blog


class ReRegisterTest(TestCase):
    def test_re_register_model(self):
        class BlogTranslationOptions(TranslationOptions):
            fields = ('title', )

        with self.assertRaisesMessage(AlreadyRegistered, 'Model "Blog" is already registered for translation'):
            translator.register(Blog, BlogTranslationOptions)

    def test_register_with_invalid_language(self):
        class TestModel(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )
            required_languages = ('en', 'nl', 'spanisch')

        expected_message = (
            'Language "spanisch" is in required_languages on '
            'Model "TestModel" but not in settings.AVAILABLE_LANGUAGES.'
        )

        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translator.register(TestModel, TestModelTranslationOptions)

    def test_register_with_invalid_language_dict(self):
        class TestModel2(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )
            required_languages = {
                'vlaams': ('name', )
            }
        expected_message = (
            'Language "vlaams" is in required_languages on Model "TestModel2" '
            'but not in settings.AVAILABLE_LANGUAGES.'
        )
        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translator.register(TestModel2, TestModelTranslationOptions)

    def test_register_with_invalid_field(self):
        class TestModel3(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )
            required_languages = {
                'en': ('title', )
            }
        expected_message = (
            'Fieldname "title" in required_languages which is not defined as '
            'translatable for Model "TestModel3".'
        )
        with self.assertRaisesMessage(ImproperlyConfigured, expected_message):
            translator.register(TestModel3, TestModelTranslationOptions)

    def test_register_model_with_custom_manager(self):

        class CustomQuerySet(models.query.QuerySet):
            pass

        class CustomManager(models.Manager):
            def get_queryset(self):
                return CustomQuerySet()

            def custom_method(self):
                return 'foo'

        class TestModel4(models.Model):
            name = models.CharField(max_length=100)

            objects = CustomManager()

            class Meta:
                app_label = 'django-modeltrans_tests'

        class TestModelTranslationOptions(TranslationOptions):
            fields = ('name', )

        translator.register(TestModel4, TestModelTranslationOptions)

        self.assertIsInstance(TestModel4.objects, CustomManager)
        self.assertIsInstance(TestModel4.objects, MultilingualManager)

        self.assertEquals(TestModel4.objects.custom_method(), 'foo')
        self.assertIsInstance(TestModel4.objects.all(), MultilingualQuerySet)

    def test_get_translatable_fiels_for_model(self):
        class TestModel5(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'django-modeltrans_tests'

        fields = get_translatable_fields_for_model(TestModel5)
        self.assertEquals(fields, None)
