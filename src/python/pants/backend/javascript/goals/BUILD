# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_sources()

python_tests(
    name="tests",
    # The package.json files are inlined in ./test_integration_tests.py
    overrides={
        "test_integration_test.py": {
            "dependencies": ["./jest_resources", "./mocha_resources"],
            "timeout": 240,
        },
        "export_test.py": {
            "timeout": 240,
            "tags": ["platform_specific_behavior"],
        },
    },
)
