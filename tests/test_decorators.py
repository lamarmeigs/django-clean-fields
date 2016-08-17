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


class UseCasesTestCase(TestCase):
    """Runs tests on expected use cases"""

    def test_multiple_cleaners_for_single_field(self):
        class MultipleCleanersModel(models.Model):
            some_field = models.IntegerField()
            other = models.IntegerField()

            @cleans_field('tests.MultipleCleanersModel.some_field')
            def add_one(self, some_field):
                return some_field + 1

            @cleans_field('tests.MultipleCleanersModel.some_field')
            def add_two(self, some_field):
                return some_field + 2

            @cleans_field_with_context('tests.MultipleCleanersModel.other')
            def add_three(self, other_field, data):
                return other_field + 3 if data['some_field'] else other_field

            @cleans_field_with_context('tests.MultipleCleanersModel.other')
            def add_four(self, other_field, data):
                return other_field + 4 if data['some_field'] else other_field

        dummy = MultipleCleanersModel(some_field=5, other=6)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 8)
        self.assertEqual(dummy.other, 13)

    def test_single_cleaner_for_multiple_fields(self):
        class MultipleFieldsModel(models.Model):
            field_1 = models.IntegerField()
            field_2 = models.IntegerField()
            field_3 = models.IntegerField()
            field_4 = models.IntegerField()

            @cleans_field('tests.MultipleFieldsModel.field_1')
            @cleans_field('tests.MultipleFieldsModel.field_2')
            def clean_integer_field(self, value):
                return value + 1

            @cleans_field_with_context('tests.MultipleFieldsModel.field_3')
            @cleans_field_with_context('tests.MultipleFieldsModel.field_4')
            def clean_integer_field_with_context(self, value, data):
                return value + 1 if data['field_1'] != 0 else value

        dummy = MultipleFieldsModel(field_1=1, field_2=2, field_3=3, field_4=4)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.field_1, 2)
        self.assertEqual(dummy.field_2, 3)
        self.assertEqual(dummy.field_3, 4)
        self.assertEqual(dummy.field_4, 5)

    def test_staticmethod_cleaner(self):
        class StaticCleanerModel(models.Model):
            some_field = models.IntegerField()
            other_field = models.IntegerField()

            @staticmethod
            @cleans_field('tests.StaticCleanerModel.some_field')
            def clean_some_field(some_field):
                return some_field + 1

            @staticmethod
            @cleans_field_with_context('tests.StaticCleanerModel.other_field')
            def clean_other_field(other_field, data):
                return other_field + 1 if data['some_field'] != 0 else 1

        dummy = StaticCleanerModel(some_field=5, other_field=6)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 6)
        self.assertEqual(dummy.other_field, 7)

    def test_classmethod_cleaner(self):
        class ClassCleanerModel(models.Model):
            some_field = models.IntegerField()
            other_field = models.IntegerField()

            @classmethod
            @cleans_field('tests.ClassCleanerModel.some_field')
            def clean_some_field(cls, some_field):
                assert cls == ClassCleanerModel
                return some_field + 1

            @classmethod
            @cleans_field_with_context('tests.ClassCleanerModel.other_field')
            def clean_other_field(cls, other_field, data):
                assert cls == ClassCleanerModel
                return other_field + 1

        dummy = ClassCleanerModel(some_field=5, other_field=6)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 6)
        self.assertEqual(dummy.other_field, 7)

    def test_independent_function_cleaner(self):
        class NoCleanerModel(models.Model):
            some_field = models.IntegerField()
            other_field = models.IntegerField()

        @cleans_field('tests.NoCleanerModel.some_field')
        def clean_some_field(some_field):
            return some_field + 1

        @cleans_field_with_context('tests.NoCleanerModel.other_field')
        def clean_other_field(other_field, data):
            return other_field + 1 if data['some_field'] != 0 else other_field

        dummy = NoCleanerModel(some_field=5, other_field=6)
        pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(dummy.some_field, 6)
        self.assertEqual(dummy.other_field, 7)

    def test_cleaner_raises_type_error(self):
        class RaiseErrorCleanerModel(models.Model):
            field_1 = models.IntegerField()
            field_2 = models.IntegerField()
            field_3 = models.IntegerField()
            field_4 = models.IntegerField()

            @cleans_field('tests.RaiseErrorCleanerModel.field_1')
            @cleans_field('tests.RaiseErrorCleanerModel.field_2')
            def clean_some_field(self, some_field):
                if isinstance(some_field, int):
                    return some_field
                raise TypeError('some_field is the wrong type')

            @cleans_field_with_context('tests.RaiseErrorCleanerModel.field_3')
            @cleans_field_with_context('tests.RaiseErrorCleanerModel.field_4')
            def clean_other_fields(self, other_field, data):
                if isinstance(other_field, int):
                    return other_field
                raise TypeError('other_field is the wrong type')

        dummy = RaiseErrorCleanerModel(
            field_1=5, field_2='str', field_3=4, field_4=4
        )
        with self.assertRaises(TypeError) as ctx:
            pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(str(ctx.exception), 'some_field is the wrong type')

        dummy = RaiseErrorCleanerModel(
            field_1=1, field_2=2, field_3='str', field_4=4
        )
        with self.assertRaises(TypeError) as ctx:
            pre_save.send(dummy.__class__, instance=dummy)
        self.assertEqual(str(ctx.exception), 'other_field is the wrong type')
