---
title: "Creating new fields"
slug: "target-api-new-fields"
excerpt: "How to create a Field, including the available templates."
hidden: false
createdAt: "2020-05-07T22:38:40.352Z"
updatedAt: "2021-11-16T03:05:31.721Z"
---
Before creating a new target type, the first step is to create all of the target type's fields.

Defining a Field
----------------

To define a new field:

1. Subclass one of the below field templates, like `IntField` or `BoolField`; or, subclass an existing field, like `SingleSourceField`. 
2. Set the class property `alias`. This is the symbol that people use in BUILD files.
3. Set the class property `help`. This is used by `pants help`.

For example:

```python
from pants.engine.target import IntField

class TimeoutField(IntField):
    alias = "timeout"
    help = "How long to run until timing out."
```

### `default`

The `default` is used whenever a user does not explicitly specify the field in a BUILD file.

```python
class TimeoutField(IntField):
    alias = "timeout"
    help = "..."
    default = 60
```

If you don't override this property, `default` will be set to `None`, which signals that the value was undefined.

### `required`

Set `required = True` to require explicitly defining the field.

```python
class TimeoutField(IntField):
    alias = "timeout"
    help = "..."
    required = True
```

If you set `required = True`, the `default` will be ignored.

> 📘 Reminder: subclass existing fields to modify their behavior
> 
> If you want to change how an existing field behaves, you should subclass the original field. For example, if you want to change a default value, subclass the original field. When doing this, you only need to override the properties you want to change.
> 
> See [Concepts](doc:target-api-concepts) for how subclassing plays a key role in the Target API.

Adding custom validation
------------------------

The field templates will validate that users are using the correct _types_, like ints or strings. But you may want to add additional validation, such as banning certain values.

To do this, override the classmethod `compute_value`:

```python
from pants.engine.target import IntField, InvalidFieldException

class UploadTimeout(IntField):
    alias = "timeout"
    help = "..."
    default = 30

    @classmethod
    def compute_value(
        cls, raw_value: Optional[int], *, address: Address
    ) -> int:
      value_or_default = super().compute_value(raw_value, address=address)
      if value_or_default < 10 or value_or_default > 300:
          raise InvalidFieldException(
              f"The {repr(cls.alias)} field in target {address} must "
              f"be between 10 and 300, but was {value_or_default}."
          )
      return value_or_default
```

Be careful to use the same type hint for the parameter `raw_value` as used in the template. This is used to generate the documentation in `pants help my_target`.

> 🚧 Cannot use new type hint syntax with `compute_value()` and `default`
> 
> You cannot use the [new type hint syntax](https://mypy-lang.blogspot.com/2021/01/) with the Target API, i.e. `list[str] | None` instead of `Optional[List[str]]`. The new syntax breaks `pants help`.
> 
> Otherwise, it's safe to use the new syntax when writing plugins.

Available templates
-------------------

All templates are defined in `pants.engine.target`.

### `BoolField`

Use this when the option is a boolean toggle. You must either set `required = True` or set `default` to `False` or `True`.

### `TriBoolField`

This is like `BoolField`, but allows you to use `None` to represent a third state. You do not have to set `required = True` or `default`, as the field template defaults to `None` already.

### `IntField`

Use this when you expect an integer. This will reject floats.

### `FloatField`

Use this when you expect a float. This will reject integers.

### `StringField`

Use this when you expect a single string.

> 📘 `StringField` can be like an enum
> 
> You can set the class property `valid_choices` to limit what strings are acceptable. This class property can either be a tuple of strings or an `enum.Enum`. 
> 
> For example:
> 
> ```python
> class LeafyGreensField(StringField):
>     alias = "leafy_greens"
>     valid_choices = ("kale", "spinach", "chard")
> ```
> 
> or:
> 
> ```python
> class LeafyGreens(Enum):
>     KALE = "kale"
>     SPINACH = "spinach"
>     CHARD = "chard"
> 
> class LeafyGreensField(StringField):
>     alias = "leafy_greens"
>     valid_choices = LeafyGreens
> ```

### `StringSequenceField`

Use this when you expect 0-n strings. 

The user may use a tuple, set, or list in their BUILD file; Pants will convert the value to an immutable tuple.

### `SequenceField`

Use this when you expect a homogenous sequence of values other than strings, such as a sequence of integers. 

The user may use a tuple, set, or list in their BUILD file; Pants will convert the value to an immutable tuple.

You must set the class properties `expected_element_type` and `expected_type_description`.  You should also change the type signature of the classmethod `compute_value` so that Pants can show the correct types when running `pants help $target_type`.

```python
class ExampleIntSequence(SequenceField):
    alias = "int_sequence"
    expected_element_type = int
    expected_type_description = "a sequence of integers"

    @classmethod
    def compute_value(
        raw_value: Optional[Iterable[int]], *, address: Address
    ) -> Optional[Tuple[int, ...]]:
        return super().compute_value(raw_value, address=address)
```

### `DictStringToStringField`

Use this when you expect a dictionary of string keys with strings values, such as `{"k": "v"}`.

The user may use a normal Python dictionary in their BUILD file. Pants will convert this into an instance of `pants.util.frozendict.FrozenDict`, which is a lightweight wrapper around the native `dict` type that simply removes all mechanisms to mutate the dictionary.

### `DictStringToStringSequenceField`

Use this when you expect a dictionary of string keys with a sequence of strings values, such as `{"k": ["v1", "v2"]}`.

The user may use a normal Python dictionary in their BUILD file, and they may use a tuple, set, or list for the dictionary values. Pants will convert this into an instance of `pants.util.frozendict.FrozenDict`, which is a lightweight wrapper around the native `dict` type that simply removes all mechanisms to mutate the dictionary. Pants will also convert the values into immutable tuples, resulting in a type hint of `FrozenDict[str, Tuple[str, ...]]`.

### `Field` - the fallback class

If none of these templates work for you, you can subclass `Field`, which is the superclass of all of these templates.

You must give a type hint for `value`,  define the classmethod `compute_value`, and either set `required = True` or define the class property `default`.

For example, we could define a `StringField` explicitly like this:

```python
from typing import Optional

from pants.engine.addresses import Address
from pants.engine.target import Field, InvalidFieldTypeException


class VersionField(Field):
    alias = "version"
    value: Optional[str]
    default = None
    help = "The version to build with."

   @classmethod
   def compute_value(
       cls, raw_value: Optional[str], *, address: Address
   ) -> Optional[str]:
       value_or_default = super().compute_value(raw_value, address=address)
       if value_or_default is not None and not isinstance(value, str):
           # A helper exception message to generate nice error messages
           # automatically. You can use another exception if you prefer.
           raise InvalidFieldTypeException(
                address, cls.alias, raw_value, expected_type="a string",
           )
       return value_or_default
```

> 👍 Asking for help
> 
> Have a tricky field you're trying to write? We would love to help! See [Getting Help](doc:community).

Examples
--------

```python plugins/target_types.py
from typing import Optional

from pants.engine.target import (
    BoolField,
    IntField,
    InvalidFieldException,
    MultipleSourcesField,
    StringField
)


class FortranVersion(StringField):
    alias = "fortran_version"
    required = True
    valid_choices = ("f95", "f98")
    help = "Which version of Fortran should this use?"

 
class CompressToggle(BoolField):
    alias = "compress"
    default = False
    help = "Whether to compress the generated file."


class UploadTimeout(IntField):
    alias = "upload_timeout"
    default = 100
    help = (
      "How long to upload (in seconds) before timing out.\n\n"
      "This must be between 10 and 300 seconds."
    )
    
    @classmethod
    def compute_value(
        cls, raw_value: Optional[int], *, address: Address
    ) -> int:
      value_or_default = super().compute_value(raw_value, address=address)
      if value_or_default < 10 or value_or_default > 300:
          raise InvalidFieldException(
              f"The {repr(cls.alias)} field in target {address} must "
              f"be between 10 and 300, but was {value_or_default}."
          )
      return value_or_default


# Example of subclassing an existing field. 
# We don't need to define `alias = sources` because the 
# parent class does this already.
class FortranSources(MultipleSourcesField):
    default = ("*.f95",)
```
