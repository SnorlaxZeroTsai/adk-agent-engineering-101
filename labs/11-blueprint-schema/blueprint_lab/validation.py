"""Cross-domain semantic validation for executable Blueprints."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .contracts import BlueprintBundle
from .contracts import ValidationIssue
from .contracts import ValidationReport
from .references import collect_local_refs
from .references import validate_catalog_sources
from .references import validate_local_ref
from .references import validate_pinned_entrypoint
from .schema_validation import validate_schema_instance


REQUIRED_COMMON_METRICS = {
    "runtime_success",
    "trajectory_contract",
    "state_contract",
    "output_contract",
}
REQUIRED_PROVENANCE_FIELDS = {
    "document_id",
    "version",
    "chunk_id",
    "uri",
    "acl",
}


def _issue(
    issues: list[ValidationIssue],
    code: str,
    path: str,
    message: str,
) -> None:
    issues.append(ValidationIssue(code=code, path=path, message=message))


def _duplicates(values: list[Any]) -> set[Any]:
    return {
        value
        for value, count in Counter(values).items()
        if value is not None and count > 1
    }


def _catalog_indexes(
    catalog: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    entries: dict[str, dict[str, Any]] = {}
    implementations: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in catalog.get("entries", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            continue
        entries[entry["id"]] = entry
        for implementation in entry.get("implementations", []):
            if isinstance(implementation, dict) and isinstance(
                implementation.get("id"),
                str,
            ):
                implementations[
                    (entry["id"], implementation["id"])
                ] = implementation
    return entries, implementations


def _model_slots(
    blueprint: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> set[str]:
    slots = blueprint.get("runtime", {}).get("model_slots", [])
    ids = [
        item.get("id")
        for item in slots
        if isinstance(item, dict)
    ]
    for duplicate in sorted(_duplicates(ids)):
        _issue(
            issues,
            "model_slot_duplicate",
            f"{path}.runtime.model_slots",
            str(duplicate),
        )
    return {item for item in ids if isinstance(item, str)}


def _validate_approval_and_credentials(
    blueprint: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    policy = blueprint.get("policy", {})
    approval = policy.get("approval", {})
    actions = approval.get("actions", [])
    contract_ref = approval.get("contract_ref")
    replay_key = approval.get("replay_key")
    metrics = set(
        blueprint.get("evaluation", {}).get("blocking_metrics", [])
    )
    if actions:
        if not contract_ref:
            _issue(
                issues,
                "approval_contract_missing",
                f"{path}.policy.approval.contract_ref",
                "consequential actions require a typed approval contract",
            )
        if not replay_key:
            _issue(
                issues,
                "approval_replay_key_missing",
                f"{path}.policy.approval.replay_key",
                "consequential actions require an idempotency key",
            )
        if "policy_safety" not in metrics:
            _issue(
                issues,
                "approval_metric_missing",
                f"{path}.evaluation.blocking_metrics",
                "policy_safety must block an approval regression",
            )
    elif contract_ref is not None or replay_key is not None:
        _issue(
            issues,
            "approval_contract_orphaned",
            f"{path}.policy.approval",
            "empty approval actions must not retain approval state",
        )

    credentials = policy.get("credentials", {})
    mode = credentials.get("mode")
    credential_ref = credentials.get("contract_ref")
    if mode == "none" and credential_ref is not None:
        _issue(
            issues,
            "credential_contract_orphaned",
            f"{path}.policy.credentials.contract_ref",
            "credential-free Blueprint must not retain a credential contract",
        )
    if mode in {"tool-scoped", "delegated"} and not credential_ref:
        _issue(
            issues,
            "credential_contract_missing",
            f"{path}.policy.credentials.contract_ref",
            f"{mode} credentials require an enforcement contract",
        )


def _validate_state_contracts(
    blueprint: dict[str, Any],
    valid_owners: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    contracts = blueprint.get("runtime", {}).get("state_contracts", [])
    keys = [
        item.get("key")
        for item in contracts
        if isinstance(item, dict)
    ]
    for duplicate in sorted(_duplicates(keys)):
        _issue(
            issues,
            "state_key_duplicate",
            f"{path}.runtime.state_contracts",
            str(duplicate),
        )
    for index, contract in enumerate(contracts):
        if not isinstance(contract, dict):
            continue
        owner = contract.get("owner")
        if owner not in valid_owners:
            _issue(
                issues,
                "state_owner_unknown",
                f"{path}.runtime.state_contracts[{index}].owner",
                str(owner),
            )


def _validate_common(
    root: Path,
    blueprint: dict[str, Any],
    valid_owners: set[str],
    path: str,
    issues: list[ValidationIssue],
) -> None:
    _validate_state_contracts(blueprint, valid_owners, path, issues)
    _validate_approval_and_credentials(blueprint, path, issues)
    metrics = set(
        blueprint.get("evaluation", {}).get("blocking_metrics", [])
    )
    missing_metrics = REQUIRED_COMMON_METRICS - metrics
    if missing_metrics:
        _issue(
            issues,
            "blocking_metrics_incomplete",
            f"{path}.evaluation.blocking_metrics",
            ", ".join(sorted(missing_metrics)),
        )
    for ref_path, reference in collect_local_refs(blueprint, path):
        validate_local_ref(
            root,
            reference,
            ref_path,
            issues,
        )


def _validate_single_agent(
    blueprint: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> set[str]:
    architecture = blueprint.get("architecture", {})
    model_slots = _model_slots(blueprint, path, issues)
    slot = architecture.get("model_slot")
    if slot not in model_slots:
        _issue(
            issues,
            "model_slot_unknown",
            f"{path}.architecture.model_slot",
            str(slot),
        )
    tools = architecture.get("tools", [])
    tool_ids = [
        tool.get("id")
        for tool in tools
        if isinstance(tool, dict)
    ]
    for duplicate in sorted(_duplicates(tool_ids)):
        _issue(
            issues,
            "tool_id_duplicate",
            f"{path}.architecture.tools",
            str(duplicate),
        )
    writes = [
        tool.get("id")
        for tool in tools
        if isinstance(tool, dict) and tool.get("effect") == "write"
    ]
    approval = blueprint.get("policy", {}).get("approval", {})
    if writes and not approval.get("actions"):
        _issue(
            issues,
            "approval_required_for_write_tool",
            f"{path}.policy.approval.actions",
            ", ".join(str(item) for item in writes),
        )
    root_agent = architecture.get("root_agent")
    return {
        item
        for item in (blueprint.get("id"), root_agent)
        if isinstance(item, str)
    }


def _reachable_nodes(
    entry: str,
    edges: list[dict[str, Any]],
) -> set[str]:
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        source = edge.get("from")
        target = edge.get("to")
        if isinstance(source, str) and isinstance(target, str):
            adjacency.setdefault(source, set()).add(target)
    visited: set[str] = set()
    pending = [entry]
    while pending:
        node = pending.pop()
        if node in visited:
            continue
        visited.add(node)
        pending.extend(sorted(adjacency.get(node, set()) - visited))
    return visited


def _validate_workflow(
    blueprint: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> set[str]:
    architecture = blueprint.get("architecture", {})
    model_slots = _model_slots(blueprint, path, issues)
    nodes = [
        item
        for item in architecture.get("nodes", [])
        if isinstance(item, dict)
    ]
    node_ids = [node.get("id") for node in nodes]
    node_map = {
        node["id"]: node
        for node in nodes
        if isinstance(node.get("id"), str)
    }
    for duplicate in sorted(_duplicates(node_ids)):
        _issue(
            issues,
            "workflow_node_duplicate",
            f"{path}.architecture.nodes",
            str(duplicate),
        )
    entry = architecture.get("entry_node")
    if entry not in node_map:
        _issue(
            issues,
            "workflow_entry_unknown",
            f"{path}.architecture.entry_node",
            str(entry),
        )
    edges = [
        item
        for item in architecture.get("edges", [])
        if isinstance(item, dict)
    ]
    for index, edge in enumerate(edges):
        for endpoint in ("from", "to"):
            if edge.get(endpoint) not in node_map:
                _issue(
                    issues,
                    f"workflow_edge_{endpoint}_unknown",
                    f"{path}.architecture.edges[{index}].{endpoint}",
                    str(edge.get(endpoint)),
                )
    if isinstance(entry, str):
        unreachable = set(node_map) - _reachable_nodes(entry, edges)
        if unreachable:
            _issue(
                issues,
                "workflow_node_unreachable",
                f"{path}.architecture.nodes",
                ", ".join(sorted(unreachable)),
            )
    terminal_ids = set(architecture.get("terminal_nodes", []))
    for terminal in sorted(terminal_ids):
        if terminal not in node_map:
            _issue(
                issues,
                "workflow_terminal_unknown",
                f"{path}.architecture.terminal_nodes",
                terminal,
            )
        elif node_map[terminal].get("kind") != "terminal":
            _issue(
                issues,
                "workflow_terminal_kind_invalid",
                f"{path}.architecture.terminal_nodes",
                terminal,
            )
    declared_terminals = {
        node["id"]
        for node in nodes
        if node.get("kind") == "terminal" and isinstance(node.get("id"), str)
    }
    if declared_terminals != terminal_ids:
        _issue(
            issues,
            "workflow_terminal_set_mismatch",
            f"{path}.architecture.terminal_nodes",
            str(sorted(declared_terminals ^ terminal_ids)),
        )
    edge_pairs = {
        (edge.get("from"), edge.get("to"))
        for edge in edges
    }
    for index, loop in enumerate(architecture.get("loops", [])):
        if not isinstance(loop, dict):
            continue
        loop_path = f"{path}.architecture.loops[{index}]"
        if (loop.get("from"), loop.get("to")) not in edge_pairs:
            _issue(
                issues,
                "workflow_loop_edge_missing",
                loop_path,
                "loop must name an existing edge",
            )
        exhaustion = loop.get("exhaustion_node")
        if exhaustion not in terminal_ids:
            _issue(
                issues,
                "workflow_loop_exhaustion_unknown",
                f"{loop_path}.exhaustion_node",
                str(exhaustion),
            )
        if (loop.get("from"), exhaustion) not in edge_pairs:
            _issue(
                issues,
                "workflow_loop_exhaustion_route_missing",
                loop_path,
                str(exhaustion),
            )
    retrievals = blueprint.get("runtime", {}).get(
        "retrieval_contracts",
        [],
    )
    retrieval_ids = {
        item.get("id")
        for item in retrievals
        if isinstance(item, dict)
    }
    used_retrievals: set[str] = set()
    for index, node in enumerate(nodes):
        node_path = f"{path}.architecture.nodes[{index}]"
        slot = node.get("model_slot")
        if slot is not None and slot not in model_slots:
            _issue(
                issues,
                "model_slot_unknown",
                f"{node_path}.model_slot",
                str(slot),
            )
        retrieval_id = node.get("retrieval_id")
        if node.get("kind") == "retrieval":
            if retrieval_id not in retrieval_ids:
                _issue(
                    issues,
                    "workflow_retrieval_unknown",
                    f"{node_path}.retrieval_id",
                    str(retrieval_id),
                )
            elif isinstance(retrieval_id, str):
                used_retrievals.add(retrieval_id)
        elif retrieval_id is not None:
            _issue(
                issues,
                "workflow_retrieval_on_wrong_node",
                f"{node_path}.retrieval_id",
                str(retrieval_id),
            )
    unused_retrievals = {
        item for item in retrieval_ids if isinstance(item, str)
    } - used_retrievals
    if unused_retrievals:
        _issue(
            issues,
            "retrieval_contract_unused",
            f"{path}.runtime.retrieval_contracts",
            ", ".join(sorted(unused_retrievals)),
        )
    for index, retrieval in enumerate(retrievals):
        if not isinstance(retrieval, dict):
            continue
        fields = set(retrieval.get("provenance_fields", []))
        missing = REQUIRED_PROVENANCE_FIELDS - fields
        if missing:
            _issue(
                issues,
                "retrieval_provenance_incomplete",
                (
                    f"{path}.runtime.retrieval_contracts[{index}]"
                    ".provenance_fields"
                ),
                ", ".join(sorted(missing)),
            )
    metrics = set(
        blueprint.get("evaluation", {}).get("blocking_metrics", [])
    )
    if retrievals and "retrieval_grounding" not in metrics:
        _issue(
            issues,
            "retrieval_metric_missing",
            f"{path}.evaluation.blocking_metrics",
            "retrieval_grounding must block a retrieval regression",
        )
    valid_owners = set(node_map)
    blueprint_id = blueprint.get("id")
    if isinstance(blueprint_id, str):
        valid_owners.add(blueprint_id)
    return valid_owners


def _validate_multi_agent(
    blueprint: dict[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> set[str]:
    architecture = blueprint.get("architecture", {})
    model_slots = _model_slots(blueprint, path, issues)
    agents = [
        item
        for item in architecture.get("agents", [])
        if isinstance(item, dict)
    ]
    agent_ids = [agent.get("id") for agent in agents]
    agent_map = {
        agent["id"]: agent
        for agent in agents
        if isinstance(agent.get("id"), str)
    }
    for duplicate in sorted(_duplicates(agent_ids)):
        _issue(
            issues,
            "agent_id_duplicate",
            f"{path}.architecture.agents",
            str(duplicate),
        )
    namespaces = [agent.get("state_namespace") for agent in agents]
    for duplicate in sorted(_duplicates(namespaces)):
        _issue(
            issues,
            "state_namespace_duplicate",
            f"{path}.architecture.agents",
            str(duplicate),
        )
    coordinator = architecture.get("coordinator")
    if coordinator not in agent_map:
        _issue(
            issues,
            "coordinator_unknown",
            f"{path}.architecture.coordinator",
            str(coordinator),
        )
    elif agent_map[coordinator].get("mode") != "chat":
        _issue(
            issues,
            "coordinator_mode_invalid",
            f"{path}.architecture.coordinator",
            "coordinator must own a chat lifecycle",
        )
    for index, agent in enumerate(agents):
        agent_path = f"{path}.architecture.agents[{index}]"
        slot = agent.get("model_slot")
        if slot not in model_slots:
            _issue(
                issues,
                "model_slot_unknown",
                f"{agent_path}.model_slot",
                str(slot),
            )
        if agent.get("mode") == "task" and (
            not agent.get("input_schema_ref")
            or not agent.get("output_schema_ref")
        ):
            _issue(
                issues,
                "task_schema_missing",
                agent_path,
                "task specialist requires typed input and output",
            )
    for index, delegation in enumerate(architecture.get("delegations", [])):
        if not isinstance(delegation, dict):
            continue
        delegation_path = f"{path}.architecture.delegations[{index}]"
        source = delegation.get("from")
        target = delegation.get("to")
        if source not in agent_map:
            _issue(
                issues,
                "delegation_source_unknown",
                f"{delegation_path}.from",
                str(source),
            )
        if target not in agent_map:
            _issue(
                issues,
                "delegation_target_unknown",
                f"{delegation_path}.to",
                str(target),
            )
        elif delegation.get("mode") != agent_map[target].get("mode"):
            _issue(
                issues,
                "delegation_mode_mismatch",
                f"{delegation_path}.mode",
                str(target),
            )
    shared = [
        item
        for item in architecture.get("shared_state", [])
        if isinstance(item, dict)
    ]
    shared_keys = [item.get("key") for item in shared]
    for duplicate in sorted(_duplicates(shared_keys)):
        _issue(
            issues,
            "shared_state_key_duplicate",
            f"{path}.architecture.shared_state",
            str(duplicate),
        )
    runtime_states = {
        item.get("key"): item
        for item in blueprint.get("runtime", {}).get("state_contracts", [])
        if isinstance(item, dict)
    }
    for index, state in enumerate(shared):
        state_path = f"{path}.architecture.shared_state[{index}]"
        writer = state.get("writer")
        if writer not in agent_map:
            _issue(
                issues,
                "shared_state_writer_unknown",
                f"{state_path}.writer",
                str(writer),
            )
        runtime_state = runtime_states.get(state.get("key"))
        if runtime_state is None:
            _issue(
                issues,
                "shared_state_contract_missing",
                state_path,
                str(state.get("key")),
            )
        elif runtime_state.get("owner") != writer:
            _issue(
                issues,
                "shared_state_writer_mismatch",
                f"{state_path}.writer",
                str(runtime_state.get("owner")),
            )
    return set(agent_map)


def _validate_blueprint(
    bundle: BlueprintBundle,
    blueprint_id: str,
    blueprint: dict[str, Any],
    entries: dict[str, dict[str, Any]],
    implementations: dict[tuple[str, str], dict[str, Any]],
    issues: list[ValidationIssue],
) -> None:
    path = f"blueprints.{blueprint_id}"
    issues.extend(
        validate_schema_instance(blueprint, bundle.schema, path=path)
    )
    catalog_ref = blueprint.get("catalog_ref", {})
    entry_id = catalog_ref.get("entry_id")
    implementation_id = catalog_ref.get("implementation_id")
    if entry_id not in entries:
        _issue(
            issues,
            "catalog_entry_unknown",
            f"{path}.catalog_ref.entry_id",
            str(entry_id),
        )
        implementation = None
    else:
        if entries[entry_id].get("lifecycle", {}).get("status") != "active":
            _issue(
                issues,
                "catalog_entry_not_active",
                f"{path}.catalog_ref.entry_id",
                str(entry_id),
            )
        implementation = implementations.get(
            (entry_id, implementation_id)
        )
        if implementation is None:
            _issue(
                issues,
                "implementation_unknown",
                f"{path}.catalog_ref.implementation_id",
                str(implementation_id),
            )
        elif implementation.get("status") != "active":
            _issue(
                issues,
                "implementation_not_active",
                f"{path}.catalog_ref.implementation_id",
                str(implementation_id),
            )
    if implementation is not None:
        validate_pinned_entrypoint(
            bundle.root,
            implementation,
            blueprint.get("runtime", {}).get("entrypoint", {}),
            f"{path}.runtime.entrypoint",
            issues,
        )

    kind = blueprint.get("architecture", {}).get("kind")
    if kind == "single-agent":
        valid_owners = _validate_single_agent(blueprint, path, issues)
    elif kind == "workflow":
        valid_owners = _validate_workflow(blueprint, path, issues)
    elif kind == "multi-agent":
        valid_owners = _validate_multi_agent(blueprint, path, issues)
    else:
        _issue(
            issues,
            "architecture_kind_unknown",
            f"{path}.architecture.kind",
            str(kind),
        )
        valid_owners = set()
    _validate_common(
        bundle.root,
        blueprint,
        valid_owners,
        path,
        issues,
    )


def _summary(bundle: BlueprintBundle) -> dict[str, Any]:
    blueprints = list(bundle.blueprints.values())
    architecture_counts = dict(
        sorted(
            Counter(
                item.get("architecture", {}).get("kind")
                for item in blueprints
            ).items()
        )
    )
    local_refs = [
        reference
        for blueprint in blueprints
        for _, reference in collect_local_refs(blueprint)
    ]
    return {
        "blueprint_count": len(blueprints),
        "architecture_counts": architecture_counts,
        "catalog_entry_count": len(bundle.catalog.get("entries", [])),
        "implementation_count": sum(
            len(entry.get("implementations", []))
            for entry in bundle.catalog.get("entries", [])
            if isinstance(entry, dict)
        ),
        "local_ref_count": len(local_refs),
        "unique_local_ref_count": len(set(local_refs)),
        "model_slot_count": sum(
            len(item.get("runtime", {}).get("model_slots", []))
            for item in blueprints
        ),
        "state_contract_count": sum(
            len(item.get("runtime", {}).get("state_contracts", []))
            for item in blueprints
        ),
        "retrieval_contract_count": sum(
            len(item.get("runtime", {}).get("retrieval_contracts", []))
            for item in blueprints
        ),
        "approval_action_count": sum(
            len(item.get("policy", {}).get("approval", {}).get("actions", []))
            for item in blueprints
        ),
        "blocking_metric_count": sum(
            len(item.get("evaluation", {}).get("blocking_metrics", []))
            for item in blueprints
        ),
    }


def validate_blueprint_bundle(bundle: BlueprintBundle) -> ValidationReport:
    """Validate schema shape, references, and cross-domain invariants."""

    issues: list[ValidationIssue] = []
    issues.extend(
        validate_schema_instance(
            bundle.catalog,
            bundle.catalog_schema,
            path="catalog",
        )
    )
    validate_catalog_sources(bundle.root, bundle.catalog, issues)
    entries, implementations = _catalog_indexes(bundle.catalog)
    blueprint_ids = list(bundle.blueprints)
    for duplicate in sorted(_duplicates(blueprint_ids)):
        _issue(
            issues,
            "blueprint_id_duplicate",
            "blueprints",
            str(duplicate),
        )
    for blueprint_id in sorted(bundle.blueprints):
        _validate_blueprint(
            bundle,
            blueprint_id,
            bundle.blueprints[blueprint_id],
            entries,
            implementations,
            issues,
        )
    expected_architectures = {"single-agent", "workflow", "multi-agent"}
    observed_architectures = {
        item.get("architecture", {}).get("kind")
        for item in bundle.blueprints.values()
    }
    if observed_architectures != expected_architectures:
        _issue(
            issues,
            "architecture_coverage_incomplete",
            "blueprints",
            str(sorted(expected_architectures - observed_architectures)),
        )
    ordered = tuple(
        sorted(
            issues,
            key=lambda item: (item.path, item.code, item.message),
        )
    )
    return ValidationReport(
        passed=not ordered,
        issues=ordered,
        summary=_summary(bundle),
    )
