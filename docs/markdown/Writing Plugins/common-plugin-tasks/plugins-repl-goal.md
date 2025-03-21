---
title: "Add a REPL"
slug: "plugins-repl-goal"
excerpt: "How to add a new implementation to the `repl` goal."
hidden: false
createdAt: "2020-08-22T05:58:07.646Z"
updatedAt: "2022-02-14T23:43:47.610Z"
---
The `repl` goal opens up an interactive Read-Eval-Print Loop that runs in the foreground.

Typically, the REPL is loaded with the transitive closure of the files and targets that the user provided, so that users may import their code and resources in the REPL.

1. Install your REPL
--------------------

There are several ways for Pants to install your REPL. See [Installing tools](doc:rules-api-installing-tools).

In this example, we simply find the program `bash` on the user's machine, but often you will want to install a tool like Ammonite or iPython instead.

You may want to also add options for your REPL implementation, such as allowing users to change the version of the tool. See [Options and subsystems](doc:rules-api-subsystems).

2. Set up a subclass of `ReplImplementation`
--------------------------------------------

Subclass `ReplImplementation` and define the class property `name: str` with the name of your REPL, e.g. `"bash"` or `"ipython"`. Users can then set the option `--repl-shell` to this option to choose your REPL implementation.

```python
from pants.core.goals.repl import ReplImplementation

class BashRepl(ReplImplementation):
    name = "bash"
```

Then, register your new `ReplImplementation` with a [`UnionRule`](doc:rules-api-unions) so that Pants knows your REPL implementation exists:

```python
from pants.engine.rules import collect_rules
from pants.engine.unions import UnionRule

...

def rules():
    return [
      	*collect_rules(),
        UnionRule(ReplImplementation, BashRepl),
    ]
```

3. Create a rule for your REPL logic
------------------------------------

Your rule should take as a parameter the `ReplImplementation ` from Step 2, which has a field `targets: Targets` containing the targets specified by the user. It also has a convenience property `addresses: Addresses` with the addresses of what was specified.

Your rule should return `ReplRequest`, which has the fields `digest: Digest`, `args: Iterable[str]`, and `extra_env: Optional[Mapping[str, str]]`. 

The `ReplRequest ` will get converted into an `InteractiveProcess` that will run in the foreground.

The process will run in a temporary directory in the build root, which means that the script/program can access files that would normally need to be declared by adding a `file` / `files` or `resource` / `resources` target to the `dependencies` field.

The process will not be hermetic, meaning that it will inherit the environment variables used by the `pants` process. Any values you set in `extra_env` will add or update the specified environment variables.

```python
from dataclasses import dataclass

from pants.core.goals.repl import ReplRequest
from pants.core.target_types import FileSourceField, ResourceSourceField
from pants.core.util_rules.source_files import SourceFiles, SourceFilesRequest
from pants.engine.rules import Get, rule
from pants.engine.target import SourcesField
from pants.util.logging import LogLevel

...

@rule(level=LogLevel.DEBUG)
async def create_bash_repl_request(repl: BashRepl) -> ReplRequest:
    # First, we find the `bash` program.
    bash_program_paths =  await Get(
        BinaryPaths, BinaryPathRequest(binary_name="bash", search_path=("/bin", "/usr/bin")),
    )
    if not bash_program_paths.first_path:
        raise EnvironmentError("Could not find the `bash` program on /bin or /usr/bin.")
    bash_program = bash_program_paths.first_path

    transitive_targets = await Get(TransitiveTargets, TransitiveTargetsRequest(request.addresses))
    sources = await Get(
        SourceFiles,
        SourceFilesRequest(
            (tgt.get(SourcesField) for tgt in transitive_targets.closure),
            for_sources_types=(BashSourceField, FileSourceField, ResourceSourceField),
        ),
    )
    return ReplRequest(
        digest=sources.snapshot.digest, args=(bash_program.exe,)
    )

```

If you use any relative paths in `args` or `extra_env`, you should call `repl.in_chroot("./example_relative_path")` on the values. This ensures that you run on the correct file in the temporary directory created by Pants.

Finally, update your plugin's `register.py` to activate this file's rules.

```python pants-plugins/bash/register.py
from bash import repl


def rules():
    return [*repl.rules()]
```

Now, when you run `pants repl --shell=bash ::`, your new REPL should be used.
