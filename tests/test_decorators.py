from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from unittest import TestCase

from django.db import models
from django.db.models.signals import pre_save
from mock import Mock, patch

from clean_fields.decorators import (
    call_cleaner, cleans_field, cleans_field_with_context
)
from clean_fields.exc import CleanFieldsConfigurationError


class CleansFieldTestCase(TestCase):
    """Tests the internal workings of the cleans_field decorator"""

    def test_pre_save_signal_handler_registered(self):
        with patch.object(pre_save, 'connect') as mock_connect:
            cleans_field('app_name.ModelName.field_name')(lambda x: x)
        self.assertEqual(mock_connect.call_count, 1)

    def test_signal_handler_raises_error_on_incorrect_field(self):
        class BadFieldModel(models.Model):
            some_field = models.IntegerField()

            @cleans_field('tests.BadFieldModel.not_a_field')
            def clean_some_field(self, some_field):
                return some_field + 1

        dummy = BadFieldModel(some_field=5)
        with self.assertRaises(CleanFieldsConfigurationError) as ctx:
            pre_save.send(dummy.__class__, instance=dummy)
        self.assertIn('tests.BadFieldModel', str(ctx.exception))
        self.assertIn('not_a_field', str(ctx.exception))
        self.assertIn('clean_some_field', str(ctx.exception))

    def test_signal_handler_raises_no_error_on_empty_field(self):
        class NullableFieldModel(models.Model):
            some_field = models.IntegerField(null=True, blank=True)

            @cleans_field('tests.NullableFieldModel.some_field')
            def clean_some_field(self, some_field):
                return some_field + 1 if some_field else 1

        dummy = NullableFieldModel(some_field=None)
        try:
            pre_save.send(dummy.__class__, instance=dummy)
        except Exception as error:
            self.fail(
                'Sending pre_save signal resulted in unexpected error:\n\t'
                '{error}'.format(error=str(error))
            )

    def test_returns_cleaner_executor(self):
        """Ensures decorated callables can still be invoked independently"""
        cleaner = Mock()
        wrapped_cleaner = cleans_field('app.Model.field_name')(cleaner)
        wrapped_cleaner(1, 2, 'foobar')
        cleaner.assert_called_once_with(1, 2, 'foobar')


class CleansFieldWithContextTestCase(TestCase):
    """Tests the functionality of the cleans_field_with_context decorator"""

    def test_pre_save_signal_handler_registered(self):
        with patch.object(pre_save, 'connect') as mock_connect:
            cleans_field_with_context('app.ModelName.field_name')(lambda x: x)
        self.assertEqual(mock_connect.call_count, 1)

    def test_signal_handler_raises_error_on_incorrect_field(self):
        class BadFieldContextModel(models.Model):
            some_field = models.IntegerField()

            @cleans_field_with_context('tests.BadFieldContextModel.no_field')
            def clean_some_field(self, some_field, data):
                return some_field + 1

        dummy = BadFieldContextModel(some_field=5)
        with self.assertRaises(CleanFieldsConfigurationError) as ctx:
            pre_save.send(dummy.__class__, instance=dummy)
        self.assertIn('tests.BadFieldContextModel', str(ctx.exception))
        self.assertIn('no_field', str(ctx.exception))
        self.assertIn('clean_some_field', str(ctx.exception))

    def test_signal_handler_raises_no_error_on_empty_field(self):
        class NullableFieldContextModel(models.Model):
            field = models.IntegerField(null=True, blank=True)

            @cleans_field_with_context('tests.NullableFieldContextModel.field')
            def clean_field(self, field, data):
                return field + 1 if field else 1

        dummy = NullableFieldContextModel(field=None)
        try:
            pre_save.send(dummy.__class__, instance=dummy)
        except Exception as error:
            self.fail(
                'Sending pre_save signal resulted in unexpected error:\n\t'
                '{error}'.format(error=str(error))
            )

    def test_returns_cleaner_executor(self):
        cleaner = Mock()
        wrapped_cleaner = cleans_field_with_context('app.Model.field')(cleaner)
        wrapped_cleaner(1, 2, 'foobar')
        cleaner.assert_called_once_with(1, 2, 'foobar')


class CleansFieldUseCasesTestCase(TestCase):
    """Runs tests on possible use cases"""

    def test_multiple_cleaners_for_single_field(self):
        class MultipleCleanersModel(models.Model):
            some_field = models.IntegerField()

            @cleans_field('tests.MultipleCleanersModel.some_field')
            def add_one(self, some_field):
                return some_field + 1

            @cleans_field('tests.MultipleCleanersModel.some_field')
            def add_two(self, some_field):
                return some_field + 2

        dummy = MultipleCleanersModel(some_field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 8)

    def test_single_cleaner_for_multiple_fields(self):
        class MultipleFieldsModel(models.Model):
            some_field = models.IntegerField()
            other_field = models.IntegerField()

            @cleans_field('tests.MultipleFieldsModel.some_field')
            @cleans_field('tests.MultipleFieldsModel.other_field')
            def clean_integer_field(self, value):
                return value + 1

        dummy = MultipleFieldsModel(some_field=4, other_field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 5)
        self.assertEqual(dummy.other_field, 6)

    def test_staticmethod_cleaner(self):
        class StaticCleanerModel(models.Model):
            some_field = models.IntegerField()

            @staticmethod
            @cleans_field('tests.StaticCleanerModel.some_field')
            def clean_some_field(some_field):
                return some_field + 1

        dummy = StaticCleanerModel(some_field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 6)

    def test_classmethod_cleaner(self):
        class ClassCleanerModel(models.Model):
            some_field = models.IntegerField()

            @classmethod
            @cleans_field('tests.ClassCleanerModel.some_field')
            def clean_some_field(cls, some_field):
                assert cls == ClassCleanerModel
                return some_field + 1

        dummy = ClassCleanerModel(some_field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 6)

    def test_independent_function_cleaner(self):
        class NoCleanerModel(models.Model):
            some_field = models.IntegerField()

        @cleans_field('tests.NoCleanerModel.some_field')
        def clean_some_field(some_field):
            return some_field + 1

        dummy = NoCleanerModel(some_field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 6)

    def test_cleaner_raises_type_error(self):
        class ErrorRaisingCleanerModel(models.Model):
            some_field = models.IntegerField()
            other_field = models.IntegerField()

            @cleans_field('tests.ErrorRaisingCleanerModel.other_field')
            @cleans_field('tests.ErrorRaisingCleanerModel.some_field')
            def clean_some_field(self, some_field):
                if isinstance(some_field, int):
                    return some_field
                raise TypeError('some_field is the wrong type')

        dummy = ErrorRaisingCleanerModel(some_field=5, other_field='str')
        with self.assertRaises(TypeError) as ctx:
            pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(str(ctx.exception), 'some_field is the wrong type')


class CleansFieldWithContextUseCasesTestCase(TestCase):
    """Runs tests on possible use cases"""

    def test_multiple_cleaners_for_single_field(self):
        class ManyCleanersContextModel(models.Model):
            field = models.IntegerField()

            @cleans_field_with_context('tests.ManyCleanersContextModel.field')
            def add_one(self, some_field, data):
                return some_field + 1

            @cleans_field_with_context('tests.ManyCleanersContextModel.field')
            def add_two(self, some_field, data):
                return some_field + 2

        dummy = ManyCleanersContextModel(field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.field, 8)

    def test_single_cleaner_for_multiple_fields(self):
        class MultipleFieldContextModel(models.Model):
            field = models.IntegerField()
            other = models.IntegerField()

            @cleans_field_with_context('tests.MultipleFieldContextModel.field')
            @cleans_field_with_context('tests.MultipleFieldContextModel.other')
            def clean_integer_field(self, value, data):
                return value + 1

        dummy = MultipleFieldContextModel(field=4, other=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.field, 5)
        self.assertEqual(dummy.other, 6)

    def test_staticmethod_cleaner(self):
        class StaticCleanerContextModel(models.Model):
            field = models.IntegerField()

            @staticmethod
            @cleans_field_with_context('tests.StaticCleanerContextModel.field')
            def clean_field(field, data):
                return field + 1

        dummy = StaticCleanerContextModel(field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.field, 6)

    def test_classmethod_cleaner(self):
        class ClassCleanerContextModel(models.Model):
            field = models.IntegerField()

            @classmethod
            @cleans_field_with_context('tests.ClassCleanerContextModel.field')
            def clean_some_field(cls, some_field, data):
                assert cls == ClassCleanerContextModel
                return some_field + 1

        dummy = ClassCleanerContextModel(field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.field, 6)

    def test_independent_function_cleaner(self):
        class NoCleanerContextModel(models.Model):
            some_field = models.IntegerField()

        @cleans_field_with_context('tests.NoCleanerContextModel.some_field')
        def clean_some_field(some_field, data):
            return some_field + 1

        dummy = NoCleanerContextModel(some_field=5)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 6)

    def test_cleaner_raises_type_error(self):
        class ErrorContextModel(models.Model):
            some_field = models.IntegerField()
            other_field = models.IntegerField()

            @cleans_field_with_context('tests.ErrorContextModel.other_field')
            @cleans_field_with_context('tests.ErrorContextModel.some_field')
            def clean_some_field(self, some_field, data):
                if isinstance(some_field, int):
                    return some_field
                raise TypeError('some_field is the wrong type')

        dummy = ErrorContextModel(some_field=5, other_field='str')
        with self.assertRaises(TypeError) as ctx:
            pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(str(ctx.exception), 'some_field is the wrong type')


def dummy_wrapper(fn):
    """Simple wrapper used for testing"""
    def _run_callable(*args, **kwargs):
        return fn(*args, **kwargs)
    return _run_callable


class CallCleanerTestCase(TestCase):
    def test_instance_method_cleaner(self):
        class InstanceMethodModel(models.Model):
            some_field = models.IntegerField()

            def clean_some_field(self, some_field):
                return some_field + 1

        dummy = InstanceMethodModel(some_field=5)
        value = call_cleaner(dummy.clean_some_field, [dummy.some_field], dummy)
        self.assertEqual(value, 6)

    def test_wrapped_instance_method_cleaner(self):
        class WrappedInstanceMethodModel(models.Model):
            some_field = models.IntegerField()

            def clean_some_field(self, some_field):
                return some_field + 1

        dummy = WrappedInstanceMethodModel(some_field=5)
        wrapped_cleaner = dummy_wrapper(dummy.clean_some_field)
        value = call_cleaner(wrapped_cleaner, [dummy.some_field], dummy)
        self.assertEqual(value, 6)

    def test_wrapped_instance_method_cleaner_raises_type_error(self):
        class ErrorRaisingWrappedMethodModel(models.Model):
            some_field = models.IntegerField()

            def clean_some_field(self, some_field):
                raise TypeError('this is a legitimate error')

        dummy = ErrorRaisingWrappedMethodModel(some_field=5)
        wrapped_cleaner = dummy_wrapper(dummy.clean_some_field)
        with self.assertRaises(TypeError) as ctx:
            call_cleaner(wrapped_cleaner, [dummy.some_field], dummy)
        self.assertEqual(str(ctx.exception), 'this is a legitimate error')

    def test_function_cleaner(self):
        class FunctionCleanerModel(models.Model):
            some_field = models.IntegerField()

        def clean_some_field(some_field):
            return some_field + 1

        dummy = FunctionCleanerModel(some_field=5)
        value = call_cleaner(clean_some_field, [dummy.some_field], dummy)
        self.assertEqual(value, 6)
