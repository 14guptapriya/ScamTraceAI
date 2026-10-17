
from graph_db import get_graph


def investigate_report(report_id: str) -> dict:
    """
    Investigate a report by finding other reports connected
    through shared entities in the FalkorDB graph.
    """

    client, graph = get_graph()

    try:
        # 1. Fetch the selected report
        report_result = graph.query(
            """
            MATCH (r:Report {id: $report_id})
            RETURN r.id, r.title, r.description, r.risk
            """,
            {"report_id": report_id},
        )

        if not report_result.result_set:
            return {
                "found": False,
                "message": f"No report found with ID {report_id}.",
                "report": None,
                "connections": [],
                "assessment": "Insufficient evidence",
            }

        row = report_result.result_set[0]

        report = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "risk": row[3],
        }

        # 2. Find other reports sharing graph entities
        connection_result = graph.query(
            """
            MATCH (r:Report {id: $report_id})-[rel]->(e)<-[other_rel]-(other:Report)
            WHERE other.id <> $report_id
            RETURN DISTINCT
                other.id,
                other.title,
                type(rel),
                labels(e),
                coalesce(e.value, e.name, 'Unknown'),
                type(other_rel)
            """,
            {"report_id": report_id},
        )

        connections = []

        for item in connection_result.result_set:
            connections.append({
                "related_report_id": item[0],
                "related_report_title": item[1],
                "relationship": item[2],
                "entity_type": item[3][0] if item[3] else "Unknown",
                "shared_entity": item[4],
                "other_relationship": item[5],
            })

        # 3. Count distinct connected reports and evidence types
        related_ids = {
            connection["related_report_id"]
            for connection in connections
        }

        evidence_types = {
            connection["entity_type"]
            for connection in connections
        }

        # 4. Make a conservative preliminary assessment
        if len(related_ids) >= 2 and len(evidence_types) >= 2:
            assessment = "Multiple potentially related reports"
        elif len(related_ids) >= 1:
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
                "Graph connections are investigative leads, "
                "not proof of fraud or common ownership."
            ),
        }

    finally:
        # Close the connection only if supported by this client version.
        pool = getattr(client, "connection_pool", None)
        if pool is not None and hasattr(pool, "disconnect"):
            pool.disconnect()


if __name__ == "__main__":
    result = investigate_report("R001")

    print("\n=== SCAMTRACE AI INVESTIGATION ===")

    if not result["found"]:
        print(result["message"])
    else:
        print("\nSelected report:")
        print(result["report"])

        print("\nAssessment:")
        print(result["assessment"])

        print("\nConnected reports and evidence:")
        for connection in result["connections"]:
            print(
                f"- {connection['related_report_id']}: "
                f"{connection['related_report_title']}"
            )
            print(
                f"  Shared {connection['entity_type']}: "
                f"{connection['shared_entity']}"
            )

        print("\nDisclaimer:")
        print(result["disclaimer"])
