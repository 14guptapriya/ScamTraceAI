
from graph_db import get_graph


def find_text_similar_reports(
    report_id: str,
    min_similarity: float = 0.05,
    max_results: int = 10,
) -> dict:
    """
    Rank reports by textual similarity using TF-IDF and
    cosine similarity.

    This identifies text similarity leads, not confirmed fraud,
    fraud probability, or proof of a common offender.

    Args:
        report_id: ID of the report being investigated.
        min_similarity: Minimum cosine similarity from 0 to 1.
        max_results: Maximum number of matches to return.
    """

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # Validate inputs.
    min_similarity = max(0.0, min(1.0, float(min_similarity)))
    max_results = max(1, int(max_results))

    client, graph = get_graph()

    try:
        # Retrieve reports from FalkorDB.
        result = graph.query("""
            MATCH (r:Report)
            RETURN r.id, r.title, r.description
            ORDER BY r.id
        """)

        reports = [
            {
                "id": str(row[0]),
                "title": str(row[1] or ""),
                "description": str(row[2] or ""),
            }
            for row in result.result_set
        ]

        # Find the selected report.
        selected_index = next(
            (
                index
                for index, report in enumerate(reports)
                if report["id"] == str(report_id)
            ),
            None,
        )

        if selected_index is None:
            return {
                "found": False,
                "matches": [],
                "message": f"Report {report_id} was not found.",
            }

        if len(reports) < 2:
            return {
                "found": True,
                "matches": [],
                "message": "At least two reports are required for comparison.",
            }

        # Combine title and description into one document per report.
        documents = [
            f"{report['title']} {report['description']}".strip()
            for report in reports
        ]

        if not any(documents):
            return {
                "found": True,
                "matches": [],
                "message": "No report text is available for comparison.",
            }

        # Convert report text into TF-IDF vectors.
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(documents)
        except ValueError:
            return {
                "found": True,
                "matches": [],
                "message": (
                    "There is not enough meaningful text to compare reports."
                ),
            }

        # Compare the selected report with every report.
        similarity_scores = cosine_similarity(
            tfidf_matrix[selected_index],
            tfidf_matrix,
        ).flatten()

        feature_names = vectorizer.get_feature_names_out()

        selected_vector = tfidf_matrix[selected_index]
        selected_terms = set(selected_vector.indices)

        matches = []

        for index, candidate in enumerate(reports):
            # Do not compare a report against itself.
            if index == selected_index:
                continue

            score = float(similarity_scores[index])

            if score < min_similarity:
                continue

            candidate_vector = tfidf_matrix[index]
            candidate_terms = set(candidate_vector.indices)

            # Find vocabulary terms present in both reports.
            common_terms = selected_terms.intersection(candidate_terms)

            # Rank shared terms by their TF-IDF weight in both reports.
            ranked_terms = sorted(
                common_terms,
                key=lambda term_index: (
                    float(selected_vector[0, term_index])
                    * float(candidate_vector[0, term_index])
                ),
                reverse=True,
            )

            matches.append({
                "report_id": candidate["id"],
                "title": candidate["title"],
                "similarity_percent": round(score * 100, 1),
                "shared_terms": ", ".join(
                    feature_names[term_index]
                    for term_index in ranked_terms[:8]
                ) or "No significant shared terms",
                "interpretation": "Text similarity lead; verify independently",
            })

        # Highest similarity first.
        matches.sort(
            key=lambda item: item["similarity_percent"],
            reverse=True,
        )

        return {
            "found": True,
            "matches": matches[:max_results],
            "message": (
                "TF-IDF measures word and phrase overlap. "
                "Similarity is not a fraud probability and does not prove "
                "that reports share an offender."
            ),
        }

    finally:
        client.close()
