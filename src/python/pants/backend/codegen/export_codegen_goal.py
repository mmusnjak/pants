# Copyright 2020 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import logging

from pants.core.util_rules.distdir import DistDir
from pants.engine.fs import MergeDigests, Workspace
from pants.engine.goal import Goal, GoalSubsystem
from pants.engine.internals.graph import hydrate_sources
from pants.engine.intrinsics import merge_digests
from pants.engine.rules import collect_rules, concurrently, goal_rule, implicitly
from pants.engine.target import (
    FilteredTargets,
    GenerateSourcesRequest,
    HydrateSourcesRequest,
    RegisteredTargetTypes,
    SourcesField,
)
from pants.engine.unions import UnionMembership
from pants.util.strutil import softwrap

logger = logging.getLogger(__name__)


class ExportCodegenSubsystem(GoalSubsystem):
    name = "export-codegen"
    help = "Write generated files to `dist/codegen` for use outside of Pants."

    @classmethod
    def activated(cls, union_membership: UnionMembership) -> bool:
        return GenerateSourcesRequest in union_membership


class ExportCodegen(Goal):
    subsystem_cls = ExportCodegenSubsystem
    environment_behavior = Goal.EnvironmentBehavior.LOCAL_ONLY  # TODO(#17129) — Migrate this.


@goal_rule
async def export_codegen(
    targets: FilteredTargets,
    union_membership: UnionMembership,
    workspace: Workspace,
    dist_dir: DistDir,
    registered_target_types: RegisteredTargetTypes,
) -> ExportCodegen:
    # We run all possible code generators. Running codegen requires specifying the expected
    # output_type, so we must inspect what is possible to generate.
    all_generate_request_types = union_membership.get(GenerateSourcesRequest)
    inputs_to_outputs = [
        (req.input, req.output) for req in all_generate_request_types if req.exportable
    ]
    codegen_sources_fields_with_output = []
    for tgt in targets:
        if not tgt.has_field(SourcesField):
            continue
        sources = tgt[SourcesField]
        for input_type, output_type in inputs_to_outputs:
            if isinstance(sources, input_type):
                codegen_sources_fields_with_output.append((sources, output_type))

    if not codegen_sources_fields_with_output:
        codegen_targets = sorted(
            {
                tgt_type.alias
                for tgt_type in registered_target_types.types
                for input_source in {input_source for input_source, _ in inputs_to_outputs}
                if tgt_type.class_has_field(input_source, union_membership=union_membership)
            }
        )
        logger.warning(
            softwrap(
                f"""
                No codegen files/targets matched. All codegen target types:
                {", ".join(codegen_targets)}
                """
            )
        )
        return ExportCodegen(exit_code=0)

    all_hydrated_sources = await concurrently(
        hydrate_sources(
            HydrateSourcesRequest(
                sources,
                for_sources_types=(output_type,),
                enable_codegen=True,
            ),
            **implicitly(),
        )
        for sources, output_type in codegen_sources_fields_with_output
    )

    merged_digest = await merge_digests(
        MergeDigests(hydrated_sources.snapshot.digest for hydrated_sources in all_hydrated_sources)
    )

    dest = str(dist_dir.relpath / "codegen")
    logger.info(f"Writing generated files to {dest}")
    workspace.write_digest(merged_digest, path_prefix=dest)
    return ExportCodegen(exit_code=0)


def rules():
    return collect_rules()
