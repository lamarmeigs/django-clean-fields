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
        # on model instance, and assigns the result to the instance's field.
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
            field_cleaner = getattr(instance, cleaner_function.__name__)
            setattr(instance, field_name, field_cleaner(field_value))

        # To ensure the wrapped method can still be invoked, define an
        # additional function that executes the method with the given arguments
        # and returns the result. This function is what the decorator returns.
        def _run_cleaner(*args, **kwargs):
            return cleaner_function(*args, **kwargs)

        return _run_cleaner
    return _clean_wrapper