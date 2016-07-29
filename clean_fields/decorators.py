from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db.models.signals import pre_save
from django.dispatch import receiver

from clean_fields.exc import CleanFieldsConfigurationError


class NoValue(object):
    """Empty class for disambiguating calls to getattr"""
    pass


def cleans_field(field_ref):
    """Decorator to registers a field cleaning methods on the pre_save signal.

    Args:
        field_ref (str): a label for the model field to clean, following the
            convention `app_name.ModelName.field_name`
    """
    app_name, model_name, field_name = field_ref.split('.')
    model_label = '.'.join([app_name, model_name])

    def _clean_wrapper(cleaner_function):
        # Register a pre-save signal handler that calls the cleaner_function
        # on a model instance, and assigns the result to the instance's field.
        @receiver(pre_save, sender=model_label, weak=False)
        def signal_handler(sender, instance, **kwargs):
            """Run the cleaner_function on instance's field"""
            field_value = getattr(instance, field_name, NoValue)
            if field_value == NoValue:
                raise CleanFieldsConfigurationError(
                    model_label,
                    field_name,
                    cleaner_function.__name__
                )

            # The cleaner_function callable, while here recognized only as a
            # function, could actually be of many types: an instance method,
            # a static method, a class method, or a function. To handle these
            # cases, first try to execute the callable bound to the instance.
            # If none exist, the callable either has an already-run inner
            # decorator (in which case, must be called with instance as a first
            # argument), or is a function (which can be called directly).
            field_cleaner = getattr(instance, cleaner_function.__name__, None)
            if field_cleaner is not None:
                cleaned_value = field_cleaner(field_value)
            else:
                try:
                    cleaned_value = cleaner_function(instance, field_value)
                except TypeError as e:
                    if (
                        'takes exactly 1 argument' not in str(e) and
                        'takes 1 positional argument' not in str(e)
                    ):
                        raise e
                    cleaned_value = cleaner_function(field_value)
            setattr(instance, field_name, cleaned_value)

        # To ensure the wrapped method can still be invoked, define an
        # additional function that executes the method with the given arguments
        # and returns the result. This function is what the decorator returns.
        def _run_cleaner(*args, **kwargs):
            return cleaner_function(*args, **kwargs)

        return _run_cleaner
    return _clean_wrapper
