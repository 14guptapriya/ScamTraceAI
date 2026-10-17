
import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go

from graph_db import get_graph
from investigator import investigate_report
from evidence_engine import evaluate_evidence


st.set_page_config(
    page_title="ScamTrace AI",
    page_icon="🔎",
    layout="wide",
)

st.title("ScamTrace AI")
st.caption(
    "Graph-powered scam investigation | "
    "Discover connections, inspect evidence, and prioritize verification."
)

st.info(
    "Demo notice: This app uses synthetic reports and identifiers. "
    "Graph connections are investigative leads, not proof of fraud."
)


@st.cache_data(ttl=30)
def load_reports():
    _, graph = get_graph()
    result = graph.query("""
        MATCH (r:Report)
        RETURN r.id, r.title, r.description, r.risk
        ORDER BY r.id
    """)

    return [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "risk": row[3],
        }
        for row in result.result_set
    ]


def create_graph_figure(report_id, connections):
    network = nx.Graph()

    network.add_node(
        report_id,
        label=report_id,
        node_type="Selected report",
    )

    for connection in connections:
        related_id = connection["related_report_id"]
        entity_type = connection["entity_type"]
        entity_value = connection["shared_entity"]

        entity_id = f"{entity_type}:{entity_value}"

        network.add_node(
            related_id,
            label=related_id,
            node_type="Related report",
        )
        network.add_node(
            entity_id,
            label=f"{entity_type}\n{entity_value}",
            node_type=entity_type,
        )

        network.add_edge(report_id, entity_id)
        network.add_edge(entity_id, related_id)

    if network.number_of_nodes() == 1:
        network.nodes[report_id]["label"] = f"{report_id}\nNo connections found"

    positions = nx.spring_layout(network, seed=42)

    edge_x, edge_y = [], []

    for source, target in network.edges():
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1.5, color="#8292A5"),
        hoverinfo="none",
    )

    node_x, node_y, labels, hover_text, colors = [], [], [], [], []

    palette = {
        "Selected report": "#E45756",
        "Related report": "#F2A541",
        "Phone": "#4C78A8",
        "URL": "#54A24B",
        "PaymentHandle": "#B279A2",
        "Brand": "#72B7B2",
    }

    for node, data in network.nodes(data=True):
        x, y = positions[node]
        node_x.append(x)
        node_y.append(y)
        labels.append(data.get("label", str(node)))
        hover_text.append(data.get("node_type", "Entity"))
        colors.append(palette.get(data.get("node_type"), "#9D9DA0"))

    
    node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    text=labels,
    textposition="bottom center",
    hovertext=hover_text,
    hovertemplate="%{hovertext}<br>%{text}<extra></extra>",
    marker=dict(
        size=24,
        color=colors,
        line=dict(width=1, color="white"),
    ),
    )


    figure = go.Figure(data=[edge_trace, node_trace])
    figure.update_layout(
        title="Connected evidence graph",
        showlegend=False,
        height=500,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return figure


with st.sidebar:
    st.header("Investigation")
    st.write("Select a synthetic report to investigate.")

    if st.button("Refresh report list"):
        load_reports.clear()
        st.rerun()

try:
    reports = load_reports()
except Exception as error:
    st.error(f"Could not load reports from FalkorDB: {error}")
    st.stop()

if not reports:
    st.warning("No reports found. Run `python seed_data.py` first.")
    st.stop()

report_options = {
    f"{report['id']} — {report['title']}": report["id"]
    for report in reports
}

with st.sidebar:
    selected_label = st.selectbox(
        "Select report",
        list(report_options.keys()),
    )
    selected_id = report_options[selected_label]

    run_investigation = st.button(
        "Investigate report",
        type="primary",
        width="stretch",
    )

if "investigation" not in st.session_state:
    st.session_state.investigation = None

if run_investigation:
    with st.spinner("Tracing connected reports and evaluating evidence..."):
        st.session_state.investigation = investigate_report(selected_id)
        st.session_state.selected_id = selected_id

if st.session_state.investigation is None:
    st.subheader("Welcome to your investigation workspace")
    st.write(
        "Select a report from the sidebar and click **Investigate report** "
        "to explore related reports, shared entities, and evidence."
    )

    st.subheader("Available demo reports")
    st.dataframe(
        pd.DataFrame(reports),
        width="stretch",
        hide_index=True,
    )
    st.stop()

result = st.session_state.investigation

if not result.get("found"):
    st.error(result.get("message", "Report not found."))
    st.stop()

report = result["report"]
evidence = evaluate_evidence(result)

st.subheader(f"{report['id']} — {report['title']}")
st.write(report["description"])

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Related reports", result.get("related_report_count", 0))

with col2:
    st.metric("Evidence entities", len(evidence["findings"]))

with col3:
    st.metric("Investigation score", f"{evidence['score']}/100")

st.warning(
    f"Priority: {evidence['level']}. "
    "This is a heuristic investigation score, not a probability of fraud."
)

left, right = st.columns([1.4, 1])

with left:
    st.subheader("Graph visualization")
    st.plotly_chart(
        create_graph_figure(report["id"], result["connections"]),
        width="stretch",
    )

with right:
    st.subheader("Evidence findings")

    if evidence["findings"]:
        for finding in evidence["findings"]:
            with st.expander(
                f"{finding['entity_type']}: {finding['entity']}",
                expanded=True,
            ):
                st.write(finding["explanation"])
                st.caption(
                    f"Heuristic score contribution: "
                    f"{finding['score_contribution']}"
                )
    else:
        st.write("No shared entities found in the current graph.")

    st.subheader("Recommended next step")
    st.write(evidence["recommendation"])

st.subheader("Related reports")

if result["connections"]:
    related_df = pd.DataFrame(result["connections"])
    st.dataframe(
        related_df[
            [
                "related_report_id",
                "related_report_title",
                "entity_type",
                "shared_entity",
            ]
        ],
        width="stretch",
        hide_index=True,
    )
else:
    st.write("No related reports were discovered.")

with st.expander("Investigation methodology"):
    st.write(
        "ScamTrace AI finds reports connected through shared graph entities. "
        "It then summarizes those overlaps and applies a transparent heuristic "
        "to prioritize further investigation."
    )
    st.write(
        "A shared identifier may be reused, spoofed, or unrelated. "
        "Verify evidence independently before taking action."
    )
  