# django_clean_fields
This Django app enables the definition of methods that will scrub a model object's field values before committing them to the database, without having to override the `save` method. For instance, in the example below, all Article titles are coerced into a predictable format. This happens automatically on save, without having to invoke `clean_title` directly.

```
from django.core.exceptions import ValidationError
from django.db import models
from clean_fields.models import NaiveCleanFieldsModel

class Article(NaiveCleanFieldsModel):
    title = models.CharField(max_length=30)

    def clean_title(self, unsaved_title):
        if "you'll never believe" in unsaved_title.lower():
            raise ValidationError('Sensationalist Clickbait Not Allowed')
        return unsaved_title.title()
```

### Usage
The app provides a single class, `NaiveCleanFieldsModel`, which extends `django.db.models.Model`. Models can inherit from this abstract base directly. On save, they will first invoke any methods that follow the naming convention `clean_{field_name}`. Such methods should accept the current value of the named field and either return a finalized value to be saved, or raise an error. If an error is raised, nothing will be committed to the database.

### Discussion
There is solid reasoning behind the omission of similar behavior in Django's core: it encourages a separation between a user's interaction with model objects and a developer's interaction with model objects. This rigorous definition of user roles is usually a Good Thing, but it can impose an unnecessary burden on projects that don't require user-driven interfaces. Be sure that this workflow benefits your project before installing it.

If in doubt, it's worth noting some built-in alternative means to accomplish similar cleaning behavior. For instance:

1. The forms API
[Django form-field validation](https://docs.djangoproject.com/en/dev/ref/forms/validation/) allows cleaning both specific values or the entirety of a submitted form. Used with a [ModelForm](https://docs.djangoproject.com/en/dev/topics/forms/modelforms/#modelform), this is the best way to scrub data delivered via the user interface.

However, forms and their validation are intended to be used within the context of a web page. They loose much of their simplicity when handled entirely on the backend.

2. Model field constraints and validators
Model fields provide two ways avoid committing erroneous values to the database. The first are [field options](https://docs.djangoproject.com/en/def/ref/models/fields/#field-options); passed as keyword arguments to your fields declarations, these will enforce value contraints on the database level (eg. CharField's max_length). The second is the ability to define [validators](https://docs.djangoproject.com/en/dev/ref/validators/#module-django.core.validators). These functions, more flexible in Python than at the database level, will raise errors if the values to be saved to not adhere to some defined pattern or convention.

While both these options keep the validation at the model level, their benefit is merely error prevention. Neither allow the ability to "massage" data into an acceptable format.

3. Signal handling
Finally, field scrubbing can be done by [handling built-in Django signals](https://docs.djangoproject.com/en/dev/topics/signals/), specifically, the [pre-save signal](https://docs.djangoproject.com/en/dev/ref/signals/#django.db.models.signals.pre_save). This workflow is most similar to that of django-clean-fields: a callable function can be configured to receive the signal, and will therefore be invoked before any model object's call to `save`.

The greatest shortcoming of this approach is that it encourages bad OO design: signal handlers of this nature would easily be defined apart from the models which they are meant to modify. Even implemented as staticmethods on the appropriate models, their method signature is obtuse, and therefore difficult to use outside of the context of signals.
