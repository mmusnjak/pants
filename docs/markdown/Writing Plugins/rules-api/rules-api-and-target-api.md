---
title: "Rules and the Target API"
slug: "rules-api-and-target-api"
excerpt: "How to use the Target API in rules."
hidden: false
createdAt: "2020-05-07T22:38:40.217Z"
updatedAt: "2022-07-25T17:50:52.879Z"
---
Start by reading the [Concepts](doc:target-api-concepts) of the Target API.

Note that the engine does not have special knowledge about `Target`s and `Field`s. To the engine, these are like any other types you'd use, and the `@rule`s to work with targets are like any other `@rule`.

How to read values from a `Target`
----------------------------------

As explained in [Concepts](doc:target-api-concepts), a `Target` is an addressable combination of fields, where each field gives some metadata about your code.

To read a particular `Field` for a `Target`, look it up with the `Field`'s class in square brackets, like you would look up a normal Python dictionary:

```python
from pants.backend.python.target_types import PythonTestsTimeoutField

timeout_field = target[PythonTestsTimeoutField]
print(timeout_field.value)
```

This will return an instance of the `Field`  subclass you looked up, which has two properties: `alias: str` and `value`. The type of `value` depends on the particular field. For example, `PythonTestsTimeout` subclasses `IntField`, so `value` has an `int` type.

Looking up a field with `tgt[MyField]` will fail if the field is not registered on the target type.

If the `Field` might not be registered, and you're okay with using a default value, you can instead use the method `.get()`. When the `Field` is not registered, this will call the constructor for that `Field` with `raw_value=None`, which is equivalent to if the user left off the field from their BUILD file.

```python
from pants.backend.python.target_types import PythonTestsTimeoutField

timeout_field = target.get(PythonTestsTimeoutField)
print(timeout_field.value)
```

Often, you may want to see if a target type has a particular `Field` registered. This is useful to filter targets. Use the methods `.has_field()` and `.has_fields()`.

```python
from pants.backend.python.target_types import PythonTestsTimeoutField, PythonSourceField

if target.has_field(PythonSourceField):
    print("My plugin can work on this target.")

if target.has_fields([PythonSourceField, PythonTestsTimeoutField]):
    print("The target has both Python sources and a timeout field")
```

### `Field` subclasses

As explained in [Concepts](doc:target-api-concepts), subclassing `Field`s is key to how the Target API works.

The `Target` methods `[MyField]`, `.has_field()` and `.get()` understand when a `Field` is subclassed, as follows:

```python
>>> docker_tgt.has_field(DockerSourceField)
True
>>> docker_tgt.has_field(SingleSourceField)
True
>>> python_test_tgt.has_field(DockerSourceField)
False
>>> python_test_tgt.has_field(SingleSourceField)
True
```

This allows you to express specifically which types of `Field`s you need to work. For example, the `pants filedeps` goal only needs `SourceField`, and works with any subclasses. Meanwhile, Black and isort need `PythonSourceField`, and work with any subclasses. Finally, the Pytest runner needs `PythonTestSourceField` (or any subclass).

### A Target's `Address`

Every target is identified by its `Address`, from `pants.engine.addresses`. Many types used in the Plugin API will use `Address` objects as fields, and it's also often useful to use the `Address` when writing the description for a `Process` you run.

A `Target` has a field `address: Address`, e.g. `my_tgt.address`.

You can also create an `Address` object directly, which is often useful in tests:

- `project:tgt` -> `Address("project", target_name="tgt")`
- `project/` -> `Address("project")`
- `//:top-level` -> `Address("", target_name="top_level")`
- `project/app.py:tgt` -> `Address("project", target_name="tgt", relative_file_name="app.py")`
- `project:tgt#generated` -> `Address("project", target_name="tgt", generated_name="generated")`
- `project:tgt@shell=zsh` -> `Address("project", target_name="tgt", parameters={"shell": "zsh"})`

You can use `str(address)` or `address.spec` to get the normalized string representation. `address.spec_path` will give the path to the parent directory of the target's original BUILD file.

How to resolve targets
----------------------

How do you get `Target`s in the first place in your plugin? 

As explained in [Goal rules](doc:rules-api-goal-rules), to get all the targets specified on the command line by a user, you can request the type `Targets` as a parameter to your `@rule` or `@goal_rule`. From there, you can optionally filter out the targets you want, such as by using `target.has_field()`.

```python
from pants.engine.target import Targets

@rule
async def example(targets: Targets) -> Foo:
    logger.info(f"User specified these targets: {[tgt.address.spec for tgt in targets]}")
    ...
```

(You can also request `Addresses` (from `pants.engine.addresses`) as a parameter to your `@rule` if you only need the addresses specified on the command line by a user.)

Use `AllTargets` to instead get all targets defined in the repository.

```python
from pants.engine.target import AllTargets

@rule
async def example(targets: AllTargets) -> Foo:
    logger.info(f"All targets: {[tgt.address.spec for tgt in targets]}")
    ...
```

For most [Common plugin tasks](doc:common-plugin-tasks), like adding a linter, Pants will have already filtered out the relevant targets for you and will pass you only the targets you care about.

Given targets, you can find their direct and transitive dependencies. See the below section "The Dependencies field".

You can also find targets by writing your own `Spec`s, rather than using what the user provided. (The types come from `pants.base.specs`.)

```python
# Inside an `@rule`, use `await Get` like this.
await Get(
    Targets,
    RawSpecs(
        description_of_origin="my plugin",  # Used in error messages for invalid specs.
        # Each of these keyword args are optional.
        address_literals=(
            AddressLiteralSpec("my_dir", target_component="tgt"),  # `my_dir:tgt`
            AddressLiteralSpec("my_dir", target_component="tgt", generated_component="gen"),  # `my_dir:tgt#gen`
            AddressLiteralSpec("my_dir/f.ext", target_component="tgt"),  # `my_dir/f.ext:tgt`
        ),
        file_literals=(FileLiteralSpec("my_dir/f.ext"),),  # `my_dir/f.ext`
        file_globs=(FileGlobSpec("my_dir/*.ext"),),  # `my_dir/*.ext`
        dir_literals=(DirLiteralSpec("my_dir"),),  # `my_dir/`
        dir_globs=(DirGlobSpec("my_dir"),),  # `my_dir:`
        recursive_globs=(RecursiveGlobSpec("my_dir"),),  # `my_dir::`
        ancestor_globs=(AncestorGlobSpec("my_dir"),),  # i.e. `my_dir` and all ancestors
    )
)
```

Finally, you can look up an `Address` given a raw address string, using `AddressInput`. This is often useful to allow a user to refer to targets in [Options](doc:rules-api-subsystems) and in `Field`s in your `Target`. For example, this mechanism is how the `dependencies` field works. This will error if the address does not exist.

```python
from pants.engine.addresses import AddressInput, Address
from pants.engine.rules import Get, rule

@rule
async def example(...) -> Foo:
    address = await Get(
        Address,
        AddressInput,
        AddressInput.parse("project/util:tgt", description_of_origin="my custom rule"),
    )
```

Given an `Address`, there are two ways to find its corresponding `Target`:

```python
from pants.engine.addresses import AddressInput, Address, Addresses
from pants.engine.rules import Get, rule
from pants.engine.target import Targets, WrappedTarget, WrappedTargetRequest

@rule
async def example(...) -> Foo:
    address = Address("project/util", target_name="tgt")

    # Approach #1
    wrapped_target = await Get(
        WrappedTarget,
        WrappedTargetRequest(address, description_of_origin="my custom rule"),
    )
    target = wrapped_target.target

    # Approach #2
    targets = await Get(Targets, Addresses([address]))
    target = targets[0]
```

The `Dependencies` field
------------------------

The `Dependencies` field is an `AsyncField`, which means that you must use the engine to hydrate its values, rather than using `Dependencies.value` like normal.

```python
from pants.engine.target import Dependencies, DependenciesRequest, Targets
from pants.engine.rules import Get, rule

@rule
async def demo(...) -> Foo:
    ...
    direct_deps = await Get(Targets, DependenciesRequest(target.get(Dependencies)))
```

`DependenciesRequest` takes a single argument: `field: Dependencies`. The return type `Targets` is a `Collection` of individual `Target` objects corresponding to each direct dependency of the original target.

If you only need the addresses of a target's direct dependencies, you can use `Get(Addresses, DependenciesRequest(target.get(Dependencies))` instead. (`Addresses` is defined in `pants.engine.addresses`.)

### Transitive dependencies with `TransitiveTargets`

If you need the transitive dependencies of a target—meaning both the direct dependencies and those dependencies' dependencies—use `Get(TransitiveDependencies, TransitiveTargetsRequest)`.

```python
from pants.engine.target import TransitiveTargets, TransitiveTargetsRequest
from pants.engine.rules import Get, rule

@rule
async def demo(...) -> Foo:
    ...
    transitive_targets = await Get(TransitiveTargets, TransitiveTargetsRequest([target.address]))
```

`TransitiveTargetsRequest` takes an iterable of `Address`es.

`TransitiveTargets` has two fields: `roots: tuple[Target, ...]` and `dependencies: tuple[Target, ...]`. `roots` stores the original input targets, and `dependencies` stores the transitive dependencies of those roots. `TransitiveTargets` also has a property `closure: FrozenOrderedSet[Target]` which merges the roots and dependencies.

### Dependencies-like fields

You may want to have a field on your target that's like the normal `dependencies` field, but you do something special with it. For example, Pants's [archive](https://github.com/pantsbuild/pants/blob/969c8dcba6eda0c939918b3bc5157ca45099b4d1/src/python/pants/core/target_types.py#L231-L257) target type has the fields `files` and `packages`, rather than `dependencies`, and it has special logic on those fields like running the equivalent of `pants package` on the `packages` field.

Instead of subclassing `Dependencies`, you can subclass `SpecialCasedDependencies` from `pants.engine.target`. You must set the `alias` class property to the field's name.

```python
from pants.engine.target import SpecialCasedDependencies, Target

class PackagesField(SpecialCasedDependencies):
    alias = "packages"

class MyTarget(Target):
    alias = "my_tgt"
    core_fields = (..., PackagesField)
```

Then, to resolve the addresses, you can use `UnparsedAddressInputs`:

```python
from pants.engine.addresses import Address, Addresses, UnparsedAddressInputs
from pants.engine.target import Targets
from pants.engine.rules import Get, rule

@rule
async def demo(...) -> Foo:
    addresses = await Get(
        Addresses,
        UnparsedAddressInputs,
        my_tgt[MyField].to_unparsed_address_inputs()
    )
    # Or, use this:
    targets = await Get(
        Targets,
        UnparsedAddressInputs,
        my_tgt[MyField].to_unparsed_address_inputs()
    )
```

Pants will include your special-cased dependencies with `pants dependencies`, `pants dependents`, and `pants --changed-since`, but the dependencies will not show up when using `await Get(Addresses, DependenciesRequest)`.

`SourcesField`
--------------

`SourceField` is an `AsyncField`, which means that you must use the engine to hydrate its values, rather than using `Sources.value` like normal.

Some Pants targets like `python_test` have the field `source: str`, whereas others like `go_package` have the field `sources: list[str]`. These are represented by the fields `SingleSourceField` and `MultipleSourcesField`. When you're defining a new target type, you should choose which of these to subclass. However, when operating over sources generically in your `@rules`, you can use the common base class `SourcesField` so that your rule works with both formats.

```python
from pants.engine.target import HydratedSources, HydrateSourcesRequest, SourcesField
from pants.engine.rules import Get, rule

@rule
async def demo(...) -> Foo:
    ...
    sources = await Get(HydratedSources, HydrateSourcesRequest(target[SourcesField]))
```

`HydrateSourcesRequest` expects a `SourcesField` object. This can be a subclass, such as `PythonSourceField` or `GoPackageSourcesField`.

`HydratedSources` has a field called `snapshot: Snapshot`, which allows you to see what files were resolved by calling `hydrated_sources.snapshot.files` and to use the resulting [`Digest`](doc:rules-api-file-system) in your plugin with `hydrated_sources.snapshot.digest`.

Typically, you will want to use the higher-level `Get(SourceFiles, SourceFilesRequest)` utility instead of `Get(HydrateSources, HydrateSourcesRequest)`. This allows you to ergonomically hydrate multiple `SourcesField`s objects in the same call, resulting in a single merged snapshot of all the input source fields.

```python
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.target import SourcesField
from pants.engine.rules import Get, rule

@rule
async def demo(...) -> Foo:
    ...
    sources = await Get(SourceFiles, SourceFilesRequest([tgt1[SourcesField], tgt2[SourcesField]]))
```

`SourceFilesRequest` expects an iterable of `SourcesField` objects. `SourceFiles` has a field `snapshot: Snapshot` with the merged snapshot of all resolved input sources fields.

### Enabling codegen

If you want your plugin to work with code generation, you must set the argument `enable_codegen=True`, along with `for_sources_types` with the types of `SourcesField` you're expecting.

```python
from pants.backend.python.target_types import PythonSourceField
from pants.core.target_types import ResourceSourceField
from pants.engine.target import HydratedSources, HydrateSourcesRequest, SourcesField
from pants.engine.rules import Get, rule

@rule
async def demo(...) -> Foo:
    ...
    sources = await Get(
        HydratedSources,
        HydrateSourcesRequest(
            target.get(SourcesField),
            enable_codegen=True,
            for_sources_types=(PythonSourceField, ResourceSourceField)
        )
    )
```

If the provided `SourcesField` object is already a subclass of one of the `for_sources_types`—or it can be generated into one of those types—then the sources will be hydrated; otherwise, you'll get back a `HydratedSources` object with an empty snapshot and the field `sources_type=None`.

`SourceFilesRequest` also accepts the `enable_codegen` and `for_source_types` arguments. This will filter out any inputted `Sources` field that are not compatible with `for_sources_type`.

```python
from pants.backend.python.target_types import PythonSourceField
from pants.core.target_types import ResourceSourceField
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.target import SourcesField
from pants.engine.rules import Get, rule

@rule
async def demo(...) -> Foo:
    ...
    sources = await Get(
        SourceFiles,
        SourceFilesRequest(
            [target.get(SourcesField)],
            enable_codegen=True,
            for_sources_types=(PythonSourceField, ResourceSourceField)
        )
    )
```

### Stripping source roots

You may sometimes want to remove source roots from files, i.e. go from `src/python/f.py` to `f.py`. This can make it easier to work with tools that would otherwise be confused by the source root.

To strip source roots, use `Get(StrippedSourceFiles, SourceFiles)`.

```python
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.core.util_rules.stripped_source_files import StrippedSourceFiles
from pants.engine.rules import Get, rule
from pants.engine.target import SourcesField

@rule
async demo(...) -> Foo:
    ...
    unstripped_sources = await Get(SourceFiles, SourceFilesRequest([target.get(SourcesField)]))
    stripped_sources = await Get(StrippedSourceFiles, SourceFiles, unstripped_sources)
```

`StrippedSourceFiles` has a single field `snapshot: Snapshot`.

You can also use `Get(StrippedSourceFiles, SourceFilesRequest)`, and the engine will automatically go from `SourceFilesRequest -> SourceFiles -> StrippedSourceFiles)`.

`FieldSet`s
-----------

A `FieldSet` is a way to specify which Fields your rule needs to use in a typed way that is understood by the engine.

Normally, your rule should simply use `tgt.get()` and `tgt.has_field()` instead of a `FieldSet`. However, for several of the [Common plugin tasks](doc:common-plugin-tasks), you will instead need to create a `FieldSet` so that the combination of fields you use can be represented by a type understood by the engine.

To create a `FieldSet`, create a new dataclass with `@dataclass(frozen=True)`. You will sometimes directly subclass `FieldSet`, but will often subclass something like `BinaryFieldSet` or `TestFieldSet`. Refer to the instructions in [Common plugin tasks](doc:common-plugin-tasks).

List every `Field` that your plugin will use as a field of your dataclass. The type hints you specify will be used by Pants to identify what `Field`s to use, e.g. `PythonSourceField` or `Dependencies`.

Finally, set the class property `required_fields` as a tuple of the `Field`s that your plugin requires. Pants will use this to filter out irrelevant targets that your plugin does not know how to operate on. Often, this will be the same as the `Field`s that you listed as dataclass fields, but it does not need to be. If a target type does not have registered one of the `Field`s that are in the dataclass fields, and it isn't a required `Field`, then Pants will use a default value as if the user left it off from their BUILD file.

```python
from dataclasses import dataclass

from pants.engine.target import Dependencies, FieldSet

@dataclass(frozen=True)
class ShellcheckFieldSet(FieldSet):
    required_fields = (ShellSourceField,)

    source: ShellSourceField
    # Because this is not in `required_fields`, this `FieldSet` will still match target types 
    # that don't have a `Dependencies` field registered. If it's not registered, then a 
    # default value for `Dependencies` will be used as if the user left off the field from
    # their BUILD file.
    dependencies: Dependencies
```

In your rule, you can access your `FieldSet` like a normal dataclass, e.g. `field_set.source` or `field_set.dependencies`. The object also has a field called `address: Address`.
