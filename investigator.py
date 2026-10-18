from collections import deque

from graph_db import get_graph


def _report_query(graph, report_id):
    result = graph.query("""
        MATCH (r:Report {id: $report_id})
        RETURN r.id, r.title, r.description, r.risk,
               r.scam_type, r.tactics, r.payment_sequence
    """, {"report_id": report_id})

    if not result.result_set:
        return None

    row = result.result_set[0]

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "risk": row[3],
        "scam_type": row[4] or "",
        "tactics": row[5] or "",
        "payment_sequence": row[6] or "",
    }


def _get_neighbors(graph, report_id):
    result = graph.query("""
        MATCH (r:Report {id: $report_id})-[rel]->(e)<-[other_rel]-(other:Report)
        WHERE other.id <> $report_id
        RETURN DISTINCT
            other.id, other.title,
            type(rel), labels(e),
            coalesce(e.value, e.name, 'Unknown'),
            type(other_rel)
    """, {"report_id": report_id})

    neighbors = []

    for row in result.result_set:
        neighbors.append({
            "related_report_id": row[0],
            "related_report_title": row[1],
            "relationship": row[2],
            "entity_type": row[3][0] if row[3] else "Unknown",
            "shared_entity": row[4],
            "other_relationship": row[5],
        })

    return neighbors


def investigate_report(report_id: str) -> dict:
    client, graph = get_graph()

    try:
        report = _report_query(graph, report_id)

        if not report:
            return {
                "found": False,
                "message": f"No report found with ID {report_id}.",
                "report": None,
                "connections": [],
                "related_report_count": 0,
                "evidence_types": [],
                "assessment": "Insufficient evidence",
            }

        connections = _get_neighbors(graph, report_id)
        related_ids = {
            item["related_report_id"] for item in connections
        }
        evidence_types = {
            item["entity_type"] for item in connections
        }

        if len(related_ids) >= 2:
            assessment = "Multiple potentially related reports"
        elif related_ids:
            assessment = "Possible connection found"
        else:
            assessment = "No shared entities found"

        return {
            "found": True,
            "report": report,
            "connections": connections,
            "related_report_count": len(related_ids),
            "evidence_types": sorted(evidence_types),
            "assessment": assessment,
            "disclaimer": (
                "Shared identifiers are investigative leads, not proof "
                "of common ownership or criminal activity."
            ),
        }

    finally:
        client.close()


def find_connection_paths(
    source_report_id: str,
    target_report_id: str,
    max_hops: int = 3,
) -> dict:
    """Find report-to-report paths through shared graph entities.

    One hop means one transition between reports through a shared entity.
    For example, R001 -> R002 -> R003 is two hops.
    """
    if max_hops < 1:
        return {"found": False, "paths": [], "message": "Hops must be at least 1."}

    client, graph = get_graph()

    try:
        source = _report_query(graph, source_report_id)
        target = _report_query(graph, target_report_id)

        if not source or not target:
            return {
                "found": False,
                "paths": [],
                "message": "Source or target report was not found.",
            }

        if source_report_id == target_report_id:
            return {
                "found": True,
                "paths": [{
                    "report_ids": [source_report_id],
                    "steps": [],
                    "hops": 0,
                }],
                "message": "Source and target are the same report.",
            }

        queue = deque([(
            source_report_id,
            [source_report_id],
            [],
        )])
        paths = []

        while queue:
            current_id, report_path, steps = queue.popleft()
            hops = len(steps)

            if hops >= max_hops:
                continue

            for neighbor in _get_neighbors(graph, current_id):
                next_id = neighbor["related_report_id"]

                # Prevent loops within a single candidate path.
                if next_id in report_path:
                    continue

                step = {
                    "from_report": current_id,
                    "to_report": next_id,
                    "entity_type": neighbor["entity_type"],
                    "shared_entity": neighbor["shared_entity"],
                    "relationship": neighbor["relationship"],
                }

                next_report_path = report_path + [next_id]
                next_steps = steps + [step]

                if next_id == target_report_id:
                    paths.append({
                        "report_ids": next_report_path,
                        "steps": next_steps,
                        "hops": len(next_steps),
                    })
                else:
                    queue.append((
                        next_id,
                        next_report_path,
                        next_steps,
                    ))

                # Keep the demo responsive if there are many possible paths.
                if len(paths) >= 20:
                    break

            if len(paths) >= 20:
                break

        paths.sort(key=lambda item: item["hops"])

        return {
            "found": bool(paths),
            "paths": paths,
            "message": (
                f"Found {len(paths)} connection path(s)."
                if paths else
                f"No path found within {max_hops} hop(s)."
            ),
        }

    finally:
        client.close()


def _tokens(value):
    return {
        token.strip().lower()
        for token in (value or "").split(",")
        if token.strip()
    }


def _jaccard(left, right):
    if not left and not right:
        return 0.0

    union = left | right
    return len(left & right) / len(union) if union else 0.0


def find_pattern_matches(report_id: str, min_score: int = 40) -> dict:
    """Rank candidate reports by similarity of structured scam features.

    This is a heuristic similarity score, not a probability of fraud.
    """
    client, graph = get_graph()

    try:
        selected = _report_query(graph, report_id)

        if not selected:
            return {
                "found": False,
                "matches": [],
                "message": f"No report found with ID {report_id}.",
            }

        result = graph.query("""
            MATCH (r:Report)
            RETURN r.id, r.title, r.scam_type,
                   r.tactics, r.payment_sequence
            ORDER BY r.id
        """)

        selected_tactics = _tokens(selected["tactics"])
        selected_sequence = _tokens(selected["payment_sequence"])
        matches = []

        for row in result.result_set:
            candidate_id, title, scam_type, tactics, sequence = row

            if candidate_id == report_id:
                continue

            candidate_tactics = _tokens(tactics)
            candidate_sequence = _tokens(sequence)

            type_score = (
                40 if selected["scam_type"]
                and selected["scam_type"] == (scam_type or "")
                else 0
            )
            tactics_score = 35 * _jaccard(
                selected_tactics, candidate_tactics
            )
            sequence_score = 25 * _jaccard(
                selected_sequence, candidate_sequence
            )

            score = round(type_score + tactics_score + sequence_score)

            if score < min_score:
                continue

            matches.append({
                "report_id": candidate_id,
                "title": title,
                "similarity_score": score,
                "matching_scam_type": bool(
                    selected["scam_type"]
                    and selected["scam_type"] == (scam_type or "")
                ),
                "matching_tactics": sorted(
                    selected_tactics & candidate_tactics
                ),
                "matching_sequence_steps": sorted(
                    selected_sequence & candidate_sequence
                ),
                "interpretation": (
                    "Candidate pattern match; verify independently."
                ),
            })

        matches.sort(
            key=lambda item: item["similarity_score"],
            reverse=True,
        )

        return {
            "found": True,
            "matches": matches,
            "message": (
                "Similarity is based on structured demo features, "
                "not proof that the reports share an offender."
            ),
        }

    finally:
        client.close()


if __name__ == "__main__":
    result = investigate_report("R001")
    print(result)
    print(find_connection_paths("R001", "R003", max_hops=2))
    print(find_pattern_matches("R001"))