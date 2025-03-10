---
title: "Command line help"
slug: "command-line-help"
excerpt: "How to dynamically get more information on Pants's internals."
hidden: false
createdAt: "2020-02-27T01:32:45.818Z"
updatedAt: "2021-11-09T20:48:14.737Z"
---
Run `pants help` to get basic help, including a list of commands you can run to get more specific help:

```text Shell
❯ pants help
Pants 2.14.0

Usage:

  pants [options] [goals] [inputs]          Attempt the specified goals on the specified inputs.
  pants help                               Display this usage message.
  pants help goals                         List all installed goals.
  pants help targets                       List all installed target types.
  pants help subsystems                    List all configurable subsystems.
  pants help tools                         List all external tools.
  pants help api-types                     List all plugin API types.
  pants help global                        Help for global options.
  pants help-advanced global               Help for global advanced options.
  pants help [name]                        Help for a target type, goal, subsystem, plugin API type or rule.
  pants help-advanced [goal/subsystem]     Help for a goal or subsystem's advanced options.
  pants help-all                           Print a JSON object containing all help info.

  [inputs] can be:
     A file, e.g. path/to/file.ext
     A path glob, e.g. '**/*.ext' (in quotes to prevent premature shell expansion)
     A directory, e.g. path/to/dir
     A directory ending in `::` to include all subdirectories, e.g. path/to/dir::
     A target address, e.g. path/to/dir:target_name.
     Any of the above with a `-` prefix to ignore the value, e.g. -path/to/ignore_me::

Documentation at https://www.pantsbuild.org
Download at https://pypi.org/pypi/pantsbuild.pants/2.14.0
```

For example, to get help on the `test` goal:

```text Shell
$ pants help test

`test` goal options
-------------------

Run tests.

Config section: [test]

  --[no-]test-debug
  PANTS_TEST_DEBUG
  debug
      default: False
      current value: False
      Run tests sequentially in an interactive process. This is necessary, for example, when you add
      breakpoints to your code.

  --[no-]test-force
  PANTS_TEST_FORCE
  force
      default: False
      current value: False
      Force the tests to run, even if they could be satisfied from cache.
...

Related subsystems: coverage-py, download-pex-bin, pants-releases, pex, pex-binary-defaults, pytest, python-infer, python-native-code, python-repos, python-setup, setup-py-generation, setuptools, source, subprocess-environment
```

Note that when you run `pants help <goal>`, it outputs all related subsystems, such as `pytest`. You can then run `pants help pytest` to get more information.

You can also run `pants help goals` and `pants help subsystems` to get a list of all activated options scopes.

To get help on the `python_tests` target:

```text Shell
❯ pants help python_test

`python_test` target
--------------------

A single Python test file, written in either Pytest style or unittest style.

All test util code, including `conftest.py`, should go into a dedicated `python_source` target and then be included in the
`dependencies` field. (You can use the `python_test_utils` target to generate these `python_source` targets.)

See https://www.pantsbuild.org/v2.8/docs/python-test-goal

Valid fields:

timeout
    type: int | None
    default: None
    A timeout (in seconds) used by each test file belonging to this target.

    This only applies if the option `--pytest-timeouts` is set to True.

...
```

Advanced Help
-------------

Many options are classified as _advanced_, meaning they are primarily intended to be used by admins, not by regular users.  

Use `help-advanced`, e.g. `pants help-advanced global` or `pants help-advanced pytest`.
