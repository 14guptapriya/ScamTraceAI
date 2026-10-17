# ScamTrace AI
**Live Demo:** [Open ScamTrace AI] https://scamtraceai.streamlit.app

### Graph-Based Scam Investigation and Evidence Analysis

ScamTrace AI is a graph-powered investigation tool that identifies potential connections between suspicious reports by analyzing shared phone numbers, URLs, payment handles, and impersonated brands.

Instead of examining each report in isolation, it explores relationships between reports to help uncover patterns that may indicate coordinated scam activity.

**ScamTrace AI focuses on explaining connections and prioritizing investigations rather than simply classifying a message as a scam.**

---

## 1. Problem Statement

Scam reports often contain overlapping information, such as phone numbers, suspicious URLs, payment identifiers, and impersonated organizations. However, these details may be distributed across multiple reports, making it difficult to recognize connections when each incident is investigated independently.

Traditional rule-based detection systems and standalone scam classifiers can flag suspicious messages or identifiers, but they may not explain how multiple reports are connected through shared entities.

This creates a need for an investigation system that can connect scattered evidence, explore relationships, and present understandable explanations to support further verification.

## 2. What Are We Trying to Solve?

ScamTrace AI aims to answer three questions:

- **Are there potentially related reports?** Identify reports connected through shared entities.
- **What evidence connects them?** Show the common identifiers and relationships behind each connection.
- **What should be investigated next?** Summarize findings and prioritize further verification.

The goal is to help investigators move from isolated reports to a connected view of potential scam activity.

## 3. Our Solution

ScamTrace AI represents reports and their associated entities as a graph.

For example, two reports may reference the same phone number, while one of those reports also shares a payment handle with a third report. By traversing these relationships, the system can discover a chain of potentially related incidents.

It then evaluates the discovered connections, generates evidence explanations, and displays the results through an interactive dashboard.

Unlike a basic scam classifier, ScamTrace AI emphasizes **relationship discovery, traceable evidence, and explainable investigation results**.

## 4. How It Works

1. **Report selection:** The user selects a suspicious report from the dashboard.
2. **Graph traversal:** The investigator queries FalkorDB to retrieve other reports connected through shared entities.
3. **Evidence collection:** The system identifies shared phone numbers, URLs, payment handles, and brands.
4. **Evidence evaluation:** A heuristic scoring engine evaluates the available overlaps and assigns an investigation-priority score.
5. **Visualization:** The dashboard displays the selected report, related reports, shared entities, and their connections.
6. **Recommendation:** The system suggests appropriate verification steps based on the available evidence.

### Example Investigation

Suppose the graph contains these synthetic reports:

- **R001:** A suspicious bank-verification message.
- **R002:** A suspected fake bank-support call.
- **R003:** A suspicious payment request.
- **R004:** An unrelated delivery notification.

R001 and R002 share a phone number and URL. R002 and R003 share a payment handle.

ScamTrace AI discovers these connections and presents them as evidence for further investigation. R004 serves as an example of a report without known shared entities.

These relationships suggest possible links, but they do not establish that the reports have the same origin or are definitively fraudulent.

## 5. System Architecture

```text
User
  |
  v
Streamlit Dashboard
  |
  v
Investigation Engine
  |
  v
FalkorDB Graph Database
  |
  v
Connected Reports and Shared Entities
  |
  v
Evidence Evaluation Engine
  |
  v
Investigation Score + Explanations
  |
  v
Interactive Graph and Recommendations
```

### Main Components

| Component | Purpose |
|---|---|
| `app.py` | Provides the interactive dashboard, graph visualization, evidence findings, and recommendations. |
| `graph_db.py` | Establishes the database connection and provides access to the selected graph. |
| `seed_data.py` | Inserts synthetic reports, entities, and relationships for demonstration. |
| `investigator.py` | Retrieves a report and discovers other reports connected through shared entities. |
| `evidence_engine.py` | Evaluates discovered connections and generates a heuristic investigation-priority score. |

## 6. Technologies Used

| Technology | Why We Use It |
|---|---|
| Python | Implements the investigation and evidence-processing logic. |
| FalkorDB | Stores interconnected reports and entities and supports graph queries. |
| Cypher-style graph queries | Traverse relationships and retrieve connected reports. |
| Streamlit | Builds the interactive web dashboard without requiring a separate frontend framework. |
| NetworkX | Creates graph layouts for visualizing relationships. |
| Plotly | Renders the interactive investigation graph. |
| Pandas | Organizes report and evidence data for display. |

## 7. Why Graph Technology?

A conventional table-based approach stores records, but identifying indirect relationships across multiple records can require complex joins and additional logic.

A graph represents reports as nodes, entities as nodes, and their associations as edges. This makes it natural to traverse relationships and discover how multiple reports are connected.

For ScamTrace AI, graph technology supports:

- Discovery of shared identifiers across reports.
- Exploration of multi-step connections.
- Visual explanations of how evidence is linked.
- Extensible modeling of additional entities and relationships.

FalkorDB is used as the graph database, while Python performs investigation and evidence evaluation.

## 8. Results and Current Capabilities

The current prototype successfully demonstrates the core investigation workflow using synthetic data.

- Retrieves reports stored in FalkorDB.
- Identifies reports connected through shared graph entities.
- Extracts evidence explaining the connections.
- Calculates a heuristic investigation-priority score.
- Visualizes relationships through an interactive graph.
- Displays findings and recommendations in a Streamlit dashboard.
- Includes an unrelated report to demonstrate the handling of reports without known shared connections.

The resulting dashboard provides a connected view of potential scam activity instead of presenting every report as an isolated incident.

**Current limitation:** The score is a heuristic for prioritizing investigation, not a calibrated probability of fraud. The prototype uses synthetic demo data and does not yet establish the real-world accuracy of its findings.

## 9. Getting Started

### Prerequisites

- Python 3.10 or later.
- Access to a FalkorDB instance.
- Git, if you want to clone the repository.

### Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/14guptapriya/ScamTraceAI.git
cd ScamTraceAI
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root and configure your FalkorDB connection:

```env
FALKORDB_HOST=your-database-host
FALKORDB_PORT=your-database-port
FALKORDB_USERNAME=your-database-username
FALKORDB_PASSWORD=your-database-password
FALKORDB_SSL=false
FALKORDB_GRAPH=scamtrace
```

Replace the example values with your actual database settings. Set `FALKORDB_SSL` according to your provider's connection requirements.

Never commit `.env` or database credentials to GitHub.

### Seed the Demo Graph

```bash
python seed_data.py
```

### Launch the Dashboard

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal, typically `http://localhost:8501`.

Select a report and click **Investigate report** to explore its connected evidence.

## 10. Future Scope

Potential improvements include:

- Automated extraction of entities from submitted messages and reports.
- Multi-hop graph exploration to uncover indirect connections.
- An agentic investigation loop that selects additional queries based on discovered evidence.
- Integration with trusted threat-intelligence sources.
- Temporal analysis to identify emerging patterns.
- Confidence calibration using verified historical datasets.
- Exportable investigation reports and evidence trails.
- Authentication, access controls, and secure handling of sensitive reports.

## 11. Responsible Use

ScamTrace AI is an investigative support prototype, not an automated fraud-verification authority.

Shared identifiers can occur innocently, and graph relationships alone cannot establish criminal activity or common ownership. Findings should be independently verified before any consequential action is taken.

The included demo uses synthetic reports and identifiers and should not be interpreted as evidence about real people, organizations, or incidents.

---

## Summary

ScamTrace AI transforms isolated suspicious reports into an interconnected investigation graph. By discovering shared entities, explaining relationships, and prioritizing further verification, it demonstrates how graph technology can support more transparent and structured scam investigations.