# django-clean-fields
This Django utility allows the definition of methods or functions to clean model object field values on save.


## Installation
Since django-clean-fields is not a Django app, simply include it on your `PYTHONPATH`. The easiest way to do this is installing via `pip`:

```bash
pip install django-clean-fields
```

No changes to the project's settings are necessary.


## Usage
Two alternate implementation options are available: an extended model class that closely resembles conventions used by the [Django forms API](https://docs.djangoproject.com/en/dev/ref/forms/validation/), and a decorator that registers a callable with the [pre_save signal](https://docs.djangoproject.com/en/dev/ref/signals/#django.db.models.signals.pre_save). Which approach to use is a decision left to the developer. The former option may provide the most familiarity with existing conventions; the latter offers more flexibility.

### CleanFieldsModel
Any model inheriting from the abstract `clean_fields.models.CleanFieldsModel` will check for and run cleaner methods as its first action when saving. Such methods should match the conventions used by [form field validators](https://docs.djangoproject.com/en/dev/ref/forms/validation/), namely:

- methods must be named `clean_<field_name>`
- methods must accept no parameters
- methods must return the "cleaned" value, ready to be written to the database
- method may raise an exception to interrupt saving

Example:

```python
from django.core.exceptions import ValidationError
from django.db import models
from clean_fields.models import CleanFieldsModel

class Article(CleanFieldsModel):
    title = models.CharField(max_length=30)

    def clean_title(self):
        if "you'll never believe" in self.title.lower():
            raise ValidationError('Sensationalist Clickbait Not Allowed')
        return self.title.title()
```

### Decorators
The `clean_fields.decorators.cleans_field` decorator can be applied to any callable, which will then be invoked when the [pre_save signal](https://docs.djangoproject.com/en/dev/ref/signals/#django.db.models.signals.pre_save) is sent by the corresponding model. The decorator requires a single argument: a reference string identifying the field to clean, which must follow the pattern "app_name.ModelName.field_name". Note that the full reference must be provided even if the callable is within the model class itself.

Any decorated callable must accept the current field value and return the "cleaned" value. The code below has the identical effect as the above example.

Example:

```python
from django.core.exceptions import ValidationError
from django.db import models
from clean_fields.decorators import cleans_field

class Article(models.Model):
    title = models.CharField(max_length=30)

    @cleans_field('your_app.Article.title')
    def ensure_title_case(self, unsaved_title):
        return unsaved_title.title()


# Multiple cleaners can be defined for a single field.
# Also, they needn't be instance methods on the model object.
@cleans_field('your_app.Article.title')
def validate_dignified_title(unsaved_title):
    if "you'll never believe" in unsaved_title.lower():
        raise ValidationError('Sensationalist Clickbait Not Allowed')
    return unsaved_title
```

If references to other fields on the model instance are necessary, the `clean_fields.decorators.cleans_field_with_context` decorator should be used instead. This decorator works the same as `cleans_field`, but passes an additional parameter to the cleaner: a dictionary containing the current field names and values.

Example:

```python
from django.db import models
from clean_fields.decorators import cleans_field_with_context

class Article(models.Model):
    title = models.CharField(max_length=30)
    is_published = models.BooleanField()

    @cleans_field_with_context('your_app.Article.title')
    def ensure_title_case_when_unpublished(self, unsaved_title, data):
        if data['is_published']:
            return unsaved_title
        else:
            return unsaved_title.title()
```


## Discussion
There is solid reasoning behind the omission of similar behavior in Django's core. For one, it might create a feeling of false security. Validation runs on save, but that does not prevent "uncleaned" data from being committed to the database (for instance, via the ORM's [`bulk_create`](https://docs.djangoproject.com/en/dev/ref/models/querysets/#bulk-create) or [`update`](https://docs.djangoproject.com/en/dev/ref/models/querysets/#update) methods, which circumvent `save()`). Furthermore, a lack of model-level validation encourages a separation between a user's interaction with model objects and a developer's interaction with model objects. This rigorous definition of user roles is usually a Good Thing, but it can impose an unnecessary burden on projects that don't require user-driven interfaces. Be sure that this workflow benefits your project before installing it.

If in doubt, it's worth noting some built-in alternative means to accomplish similar cleaning behavior. For instance:

1. The forms API

    [Django form-field validation](https://docs.djangoproject.com/en/dev/ref/forms/validation/) allows cleaning both specific values or the entirety of a submitted form. Used with a [ModelForm](https://docs.djangoproject.com/en/dev/topics/forms/modelforms/#modelform), this is the best way to scrub data delivered via the user interface.

    However, forms and their validation are intended to be used within the context of a web page. They lose much of their simplicity when handled entirely on the backend.

2. Model field constraints and validators

    Model fields provide two ways to avoid committing erroneous values to the database. The first are [field options](https://docs.djangoproject.com/en/def/ref/models/fields/#field-options); passed as keyword arguments to your fields declarations, these will enforce value contraints on the database level (eg. CharField's max_length). The second is the ability to define [validators](https://docs.djangoproject.com/en/dev/ref/validators/#module-django.core.validators). These functions, more flexible in Python than at the database level, will raise errors if the values to be saved to not adhere to some defined pattern or convention.

    While both these options keep the validation at the model level, their benefit is merely error prevention. Neither allow the ability to "massage" data into an acceptable format.

3. Model Validation

    Django does provide some support custom [model object validation](https://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects) via the [`Model.clean()` method](https://docs.djangoproject.com/en/dev/ref/models/instances/#django.db.models.Model.clean). This allows modifying attributes, allows access to multiple fields, and will be called via the [`Model.full_clean()` method](https://docs.djangoproject.com/en/dev/ref/models/instances/#django.db.models.Model.full_clean).

    This sort of custom validation sounds ideal, except that it is not called when a model object is saved. `full_clean()` or `clean()` must be invoked manually by any object other than a `ModelForm`. Moreover, from a design perspective, it's preferable to have methods with as narrow a focus as possible: a single method to clean a single aspect of a single field is better than `clean()`, which must handle all validation on all fields.

4. Signal handling

    The `cleans_field` decorator already leverages [built-in Django signals](https://docs.djangoproject.com/en/dev/topics/signals/) (specifically, the [pre_save signal](https://docs.djangoproject.com/en/dev/ref/signals/#django.db.models.signals.pre_save)). It is possible to handle field scrubbing directly by defining your own signal handlers and connecting them to the appropriate signal.

    The greatest shortcoming of this approach is that it encourages bad OO design: signal handlers of this nature would easily be defined apart from the models which they are meant to modify. Even implemented as staticmethods on the appropriate models, their method signature is obtuse, and therefore difficult to use outside of the context of signals.

This project intends to pick up the slack where the above built-in methods fall short, providing a simple interface to support streamlined model design. It's not uncircumventable, so _caveat emptor_, but aims to make your life easier.
