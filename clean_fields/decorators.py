from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.db.models.signals import pre_save
from django.dispatch import receiver

from clean_fields.exc import CleanFieldsConfigurationError
from clean_fields.utils import (
    get_model_field_names, get_model_field_value, parse_field_ref
)


def cleans_field(field_ref):
    """Decorator to registers a field cleaning methods on the pre_save signal.

    Args:
        field_ref (str): a label for the model field to clean, following the
            convention `app_name.ModelName.field_name`
    """
    model_label, field_name = parse_field_ref(field_ref)

    def _clean_wrapper(cleaner_function):
        # Register a pre-save signal handler that calls the cleaner_function
        # on a model instance, and assigns the result to the instance's field.
        @receiver(pre_save, sender=model_label, weak=False)
        def signal_handler(sender, instance, **kwargs):
            """Run the cleaner_function on instance's field"""
            try:
                field_value = get_model_field_value(instance, field_name)
            except AttributeError:
                raise CleanFieldsConfigurationError(
                    model_label,
                    field_name,
                    cleaner_function.__name__
                )

            cleaned_value = call_cleaner(
                cleaner_function,
                [field_value],
                instance
            )
            setattr(instance, field_name, cleaned_value)

        # To ensure the wrapped method can still be invoked, define an
        # additional function that executes the method with the given arguments
        # and returns the result. This function is what the decorator returns.
        def _run_cleaner(*args, **kwargs):
            return cleaner_function(*args, **kwargs)

        return _run_cleaner
    return _clean_wrapper


def cleans_field_with_context(field_ref):
    """Decorator to register field cleaning methods that require additional
    field values as parameters on the pre_save signal.

    Args:
        field_ref (str): a label for the model field to clean, following the
            convention `app_name.ModelName.field_name`
    """
    model_label, field_name = parse_field_ref(field_ref)

    def _clean_with_context_wrapper(cleaner_function):
        # Register a pre-save signal handler that calls the cleaner_function
        # on a model instance, and assigns the result to the instance's field.
        @receiver(pre_save, sender=model_label, weak=False)
        def signal_handler(sender, instance, **kwargs):
            # Collect all the model instance's field values in a dictionary
            context = {}
            for name in get_model_field_names(instance):
                context[name] = get_model_field_value(instance, name)
            try:
                field_value = context[field_name]
            except KeyError:
                raise CleanFieldsConfigurationError(
                    model_label,
                    field_name,
                    cleaner_function.__name__
                )

            cleaned_value = call_cleaner(
                cleaner_function,
                [field_value, context],
                instance
            )
            setattr(instance, field_name, cleaned_value)

        # Define an additional wrapper to execute cleaner_function with
        # given arguments. This ensures the wrapped method can still be called.
        def _run_cleaner_with_context(*args, **kwargs):
            return cleaner_function(*args, **kwargs)

        return _run_cleaner_with_context
    return _clean_with_context_wrapper


def call_cleaner(cleaner_callable, args, instance):
    """Invokes the cleaner_callable with given arguments.

    The cleaner_callable could be of many types: an instance method, a static
    method, a class method, or a function. This function tries to address these
    in the following order:
        - callable is an method bound to instance
        - callable is bound to instance with an already-run inner decorator
        - callable is an independent function

    Args:
        cleaner_callable (callable): method/function to invoke
        args (list): list of arguments to be passed to cleaner_callable
        instance (model instance): model instance for which this cleaner should
            be called

    Return:
        The return value of cleaner_callable
    """
    # First, try to invoke a method on instance with the same name as
    # cleaner_callable. This will handle the case in which cleaner_callable is
    # an instance method.
    field_cleaner = getattr(instance, cleaner_callable.__name__, None)
    if field_cleaner is not None:
        cleaned_value = field_cleaner(*args)
    else:
        # In case cleaner_callable is a wrapper to a callable bound to
        # instance, invoke it with instance as the first argument
        try:
            cleaned_value = cleaner_callable(instance, *args)
        except TypeError as e:
            # Except in the case of legitimate TypeErrors raised from within
            # cleaner_callable, invoke the callable as an independent function
            if not re.search(
                r'takes( exactly)? \d( positional)? arguments?',
                str(e)
            ):
                raise e
            cleaned_value = cleaner_callable(*args)
    return cleaned_value
