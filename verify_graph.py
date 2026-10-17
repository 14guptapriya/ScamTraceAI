
from graph_db import get_graph

client, graph = get_graph()

result = graph.query("""
    MATCH (a:Report)-[rel]->(e)<-[rel2]-(b:Report)
    WHERE a.id < b.id
    RETURN a.id, type(rel), labels(e), b.id
""")

print("Shared connections found:")
for row in result.result_set:
    print(row)

if not result.result_set:
    print("No shared connections found. Run python seed_data.py first.")
