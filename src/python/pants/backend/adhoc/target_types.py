# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

from pants.core.util_rules.environments import EnvironmentField
from pants.engine.target import (
    COMMON_TARGET_FIELDS,
    BoolField,
    Dependencies,
    IntField,
    MultipleSourcesField,
    SpecialCasedDependencies,
    StringField,
    StringSequenceField,
    Target,
    ValidNumbers,
)
from pants.util.strutil import help_text


class AdhocToolDependenciesField(Dependencies):
    pass


class AdhocToolRunnableField(StringField):
    alias = "runnable"
    required = True
    help = help_text(
        lambda: f"""
        Address to a target that can be invoked by the `run` goal (and does not set
        `run_in_sandbox_behavior=NOT_SUPPORTED`). This will be executed along with any arguments
        specified by `{AdhocToolArgumentsField.alias}`, in a sandbox with that target's transitive
        dependencies, along with the transitive dependencies specified by
        `{AdhocToolExecutionDependenciesField.alias}`.
        """
    )


class AdhocToolOutputFilesField(StringSequenceField):
    alias = "output_files"
    required = False
    default = ()
    help = help_text(
        lambda: f"""
        Specify the output files to capture, relative to the value of
        `{AdhocToolWorkdirField.alias}`.

        For directories, use `{AdhocToolOutputDirectoriesField.alias}`. At least one of
        `{AdhocToolOutputFilesField.alias}` and`{AdhocToolOutputDirectoriesField.alias}` must be
        specified.

        Relative paths (including `..`) may be used, as long as the path does not ascend further
        than the build root.
        """
    )


class AdhocToolOutputDirectoriesField(StringSequenceField):
    alias = "output_directories"
    required = False
    default = ()
    help = help_text(
        lambda: f"""
        Specify full directories (including recursive descendants) of output to capture, relative
        to the value of `{AdhocToolWorkdirField.alias}`.

        For individual files, use `{AdhocToolOutputFilesField.alias}`. At least one of
        `{AdhocToolOutputFilesField.alias}` and`{AdhocToolOutputDirectoriesField.alias}` must be
        specified.

        Relative paths (including `..`) may be used, as long as the path does not ascend further
        than the build root.
        """
    )


class AdhocToolOutputDependenciesField(AdhocToolDependenciesField):
    supports_transitive_excludes = True
    alias = "output_dependencies"
    deprecated_alias = "dependencies"
    deprecated_alias_removal_version = "2.17.0.dev0"

    help = help_text(
        lambda: f"""
        Any dependencies that the output artifacts require in order to be effectively consumed.

        To enable legacy use cases, if `{AdhocToolExecutionDependenciesField.alias}` is `None`,
        these dependencies will be materialized in the execution sandbox. This behavior is
        deprecated, and will be removed in version 2.17.0.dev0.
        """
    )


class AdhocToolExecutionDependenciesField(SpecialCasedDependencies):
    alias = "execution_dependencies"
    required = False
    default = None

    help = help_text(
        lambda: f"""
        The execution dependencies for this command.

        Dependencies specified here are those required to make the command complete successfully
        (e.g. file inputs, packages compiled from other targets, etc), but NOT required to make
        the output side-effects useful. Dependencies that are required to use the side-effects
        produced by this command should be specified using the
        `{AdhocToolOutputDependenciesField.alias}` field.

        If this field is specified, dependencies from `{AdhocToolOutputDependenciesField.alias}`
        will not be added to the execution sandbox.
        """
    )


class AdhocToolRunnableDependenciesField(SpecialCasedDependencies):
    alias = "runnable_dependencies"
    required = False
    default = None

    help = help_text(
        lambda: f"""
        The execution dependencies for this command.

        Dependencies specified here are those required to exist on the `PATH` to make the command
        complete successfully (interpreters specified in a `#!` command, etc). Note that these
        dependencies will be made available on the `PATH` with the name of the target.

        See also `{AdhocToolOutputDependenciesField.alias}` and
        `{AdhocToolExecutionDependenciesField.alias}.
        """
    )


class AdhocToolSourcesField(MultipleSourcesField):
    # We solely register this field for codegen to work.
    alias = "_sources"
    uses_source_roots = False
    expected_num_files = 0


class AdhocToolArgumentsField(StringSequenceField):
    alias = "args"
    default = ()
    help = help_text(
        lambda: f"Extra arguments to pass into the `{AdhocToolRunnableField.alias}` field."
    )


class AdhocToolStdoutFilenameField(StringField):
    alias = "stdout"
    default = None
    help = help_text(
        lambda: f"""
        A filename to capture the contents of `stdout` to, relative to the value of
        `{AdhocToolWorkdirField.alias}`.
        """
    )


class AdhocToolStderrFilenameField(StringField):
    alias = "stderr"
    default = None
    help = help_text(
        lambda: f"""
        A filename to capture the contents of `stderr` to, relative to the value of
        `{AdhocToolWorkdirField.alias}`
        """
    )


class AdhocToolTimeoutField(IntField):
    alias = "timeout"
    default = 30
    help = "Command execution timeout (in seconds)."
    valid_numbers = ValidNumbers.positive_only


class AdhocToolExtraEnvVarsField(StringSequenceField):
    alias = "extra_env_vars"
    help = help_text(
        """
        Additional environment variables to provide to the process.

        Entries are strings in the form `ENV_VAR=value` to use explicitly; or just
        `ENV_VAR` to copy the value of a variable in Pants's own environment.
        """
    )


class AdhocToolLogOutputField(BoolField):
    alias = "log_output"
    default = False
    help = "Set to true if you want the output logged to the console."


class AdhocToolWorkdirField(StringField):
    alias = "workdir"
    default = "."
    help = help_text(
        """
        Sets the working directory for the process.

        Values are relative to the build root, except in the following cases:

        * `.` specifies the location of the `BUILD` file.
        * Values beginning with `./` are relative to the location of the `BUILD` file.
        * `/` or the empty string specifies the build root.
        * Values beginning with `/` are also relative to the build root.
        """
    )


class AdhocToolOutputRootDirField(StringField):
    alias = "root_output_directory"
    default = "/"
    help = help_text(
        """Adjusts the location of files output by this target, when consumed as a dependency.

        Values are relative to the build root, except in the following cases:

        * `.` specifies the location of the `BUILD` file.
        * Values beginning with `./` are relative to the location of the `BUILD` file.
        * `/` or the empty string specifies the build root.
        * Values beginning with `/` are also relative to the build root.
        """
    )


class AdhocToolTarget(Target):
    alias = "adhoc_tool"
    deprecated_alias = "experimental_run_in_sandbox"
    deprecated_alias_removal_version = "2.17.0.dev0"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        AdhocToolRunnableField,
        AdhocToolArgumentsField,
        AdhocToolExecutionDependenciesField,
        AdhocToolOutputDependenciesField,
        AdhocToolRunnableDependenciesField,
        AdhocToolLogOutputField,
        AdhocToolOutputFilesField,
        AdhocToolOutputDirectoriesField,
        AdhocToolSourcesField,
        AdhocToolTimeoutField,
        AdhocToolExtraEnvVarsField,
        AdhocToolWorkdirField,
        AdhocToolOutputRootDirField,
        AdhocToolStdoutFilenameField,
        AdhocToolStderrFilenameField,
        EnvironmentField,
    )
    help = help_text(
        lambda: f"""
        Execute any runnable target for its side effects.

        Example BUILD file:

            {AdhocToolTarget.alias}(
                {AdhocToolRunnableField.alias}=":python_source",
                {AdhocToolArgumentsField.alias}=[""],
                {AdhocToolExecutionDependenciesField.alias}=[":scripts"],
                {AdhocToolOutputDirectoriesField.alias}=["logs/my-script.log"],
                {AdhocToolOutputFilesField.alias}=["results/"],
            )

            shell_sources(name="scripts")
        """
    )


# ---
# `system_binary` target
# ---


class SystemBinaryNameField(StringField):
    alias = "binary_name"
    required = True
    help = "The name of the binary to find."


class SystemBinaryExtraSearchPathsField(StringSequenceField):
    alias = "extra_search_paths"
    default = ()
    help = help_text(
        """
        Extra search paths to look for the binary. These take priority over Pants' default
        search paths.
        """
    )


class SystemBinaryFingerprintPattern(StringField):
    alias = "fingerprint"
    required = False
    default = None
    help = help_text(
        """
        A regular expression which will be used to match the fingerprint outputs from
        candidate binaries found during the search process.
        """
    )


class SystemBinaryFingerprintArgsField(StringSequenceField):
    alias = "fingerprint_args"
    default = ()
    help = help_text(
        "Specifies arguments that will be used to run the binary during the search process."
    )


class SystemBinaryFingerprintDependenciesField(AdhocToolRunnableDependenciesField):
    alias = "fingerprint_dependencies"
    help = help_text(
        """
        Specifies any runnable dependencies that need to be available on the `PATH` when the binary
        is run, so that the search process may complete successfully. The name of the target must
        be the name of the runnable dependency that is called by this binary.
        """
    )


class SystemBinaryTarget(Target):
    alias = "system_binary"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        SystemBinaryNameField,
        SystemBinaryExtraSearchPathsField,
        SystemBinaryFingerprintPattern,
        SystemBinaryFingerprintArgsField,
        SystemBinaryFingerprintDependenciesField,
    )
    help = help_text(
        lambda: f"""
        A system binary that can be run with `pants run` or consumed by `{AdhocToolTarget.alias}`.

        Pants will search for binaries with name `{SystemBinaryNameField.alias}` in the search
        paths provided, as well as default search paths. If
        `{SystemBinaryFingerprintPattern.alias}` is specified, each binary that is located will be
        executed with the arguments from `{SystemBinaryFingerprintArgsField.alias}`. Any binaries
        whose output does not match the pattern will be excluded.

        The first non-excluded binary will be the one that is resolved.
        """
    )
