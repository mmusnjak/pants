# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from pants.backend.python.subsystems.python_tool_base import LockfileRules, PythonToolBase
from pants.backend.python.target_types import ConsoleScript
from pants.engine.rules import collect_rules
from pants.option.option_types import ArgsListOption
from pants.util.docutil import git_url
from pants.util.strutil import help_text


class PyOxidizer(PythonToolBase):
    options_scope = "pyoxidizer"
    name = "PyOxidizer"
    help = help_text(
        """
        The PyOxidizer utility for packaging Python code in a Rust binary
        (https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer.html).

        Used with the `pyoxidizer_binary` target.
        """
    )

    default_version = "pyoxidizer==0.18.0"
    default_main = ConsoleScript("pyoxidizer")

    register_interpreter_constraints = True
    default_interpreter_constraints = ["CPython>=3.8,<4"]

    register_lockfile = True
    default_lockfile_resource = ("pants.backend.python.packaging.pyoxidizer", "pyoxidizer.lock")
    default_lockfile_path = "src/python/pants/backend/python/packaging/pyoxidizer/pyoxidizer.lock"
    default_lockfile_url = git_url(default_lockfile_path)
    lockfile_rules_type = LockfileRules.SIMPLE

    args = ArgsListOption(example="--release")


def rules():
    return collect_rules()
