
def evaluate_evidence(investigation: dict) -> dict:
    """
    Evaluate graph evidence from ScamTrace AI.
    The score is a heuristic for investigation prioritization,
    NOT a probability that a report is fraudulent.
    """

    if not investigation.get("found"):
        return {
            "score": 0,
            "level": "Insufficient evidence",
            "findings": [],
            "recommendation": "Verify the report details before investigating.",
        }

    connections = investigation.get("connections", [])

    # Weights indicate investigative relevance, not statistical probability.
    weights = {
        "Phone": 25,
        "URL": 25,
        "PaymentHandle": 30,
        "Brand": 10,
    }

    # Deduplicate evidence by entity type and entity value.
    unique_entities = {}

    for connection in connections:
        entity_type = connection.get("entity_type", "Unknown")
        entity_value = connection.get("shared_entity", "Unknown")
        key = (entity_type, entity_value)

        if key not in unique_entities:
            unique_entities[key] = {
                "type": entity_type,
                "value": entity_value,
                "related_reports": set(),
            }

        unique_entities[key]["related_reports"].add(
            connection.get("related_report_id")
        )

    findings = []
    raw_score = 0

    for entity in unique_entities.values():
        entity_type = entity["type"]
        value = entity["value"]
        related_count = len(entity["related_reports"])
        weight = weights.get(entity_type, 5)

        # A shared entity connecting more reports adds context,
        # but does not prove those reports share an operator.
        contribution = min(weight + (related_count - 1) * 5, weight + 10)
        raw_score += contribution

        findings.append({
            "entity_type": entity_type,
            "entity": value,
            "related_report_count": related_count,
            "heuristic_weight": weight,
            "score_contribution": contribution,
            "explanation": (
                f"This {entity_type} appears in the selected report "
                f"and {related_count} other report(s). "
                "This overlap may warrant further investigation."
            ),
        })

    # Cap the prioritization score at 100.
    score = min(raw_score, 100)

    if not findings:
        level = "Insufficient evidence"
        recommendation = (
            "Collect more verifiable details. No shared graph entities "
            "were found in the current dataset."
        )
    elif score >= 60:
        level = "High investigation priority"
        recommendation = (
            "Review the shared entities and verify them through trusted "
            "sources before drawing conclusions or taking action."
        )
    elif score >= 30:
        level = "Moderate investigation priority"
        recommendation = (
            "Check the shared identifiers and gather independent "
            "corroborating evidence."
        )
    else:
        level = "Low investigation priority"
        recommendation = (
            "Treat the connection as preliminary and seek additional "
            "evidence before escalating."
        )

    return {
        "score": score,
        "level": level,
        "findings": findings,
        "recommendation": recommendation,
        "score_note": (
            "Heuristic prioritization score, not a fraud probability "
            "or a verified measure of malicious activity."
        ),
    }


if __name__ == "__main__":
    from investigator import investigate_report

    result = investigate_report("R001")
    evidence = evaluate_evidence(result)

    print("\n=== SCAMTRACE AI EVIDENCE REPORT ===")
    print("Score:", evidence["score"], "/ 100")
    print("Priority:", evidence["level"])

    print("\nFindings:")
    for finding in evidence["findings"]:
        print(
            f"- {finding['entity_type']}: {finding['entity']}"
        )
        print(" ", finding["explanation"])

    print("\nRecommendation:")
    print(evidence["recommendation"])

    print("\nNote:")
    print(evidence["score_note"])
