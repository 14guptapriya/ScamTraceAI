
from graph_db import get_graph

def seed_graph():
    client, graph = get_graph()

    queries = [
        # Synthetic scam reports
        """
        MERGE (r:Report {id: 'R001'})
        SET r.title = 'Bank account verification SMS',
            r.description = 'Message asks the recipient to verify a bank account',
            r.source = 'Synthetic demo data',
            r.risk = 'High'
        """,
        """
        MERGE (r:Report {id: 'R002'})
        SET r.title = 'Fake bank support call',
            r.description = 'Caller claims to represent bank support',
            r.source = 'Synthetic demo data',
            r.risk = 'High'
        """,
        """
        MERGE (r:Report {id: 'R003'})
        SET r.title = 'Suspicious payment request',
            r.description = 'Message requests payment through an unfamiliar handle',
            r.source = 'Synthetic demo data',
            r.risk = 'Medium'
        """,
        """
        MERGE (r:Report {id: 'R004'})
        SET r.title = 'Unrelated delivery notification',
            r.description = 'Unverified delivery notification with no known links',
            r.source = 'Synthetic demo data',
            r.risk = 'Low'
        """,

        # Entities shared by multiple reports
        "MERGE (:Phone {value: '+910000000101'})",
        "MERGE (:URL {value: 'https://demo-bank.example.test'})",
        "MERGE (:PaymentHandle {value: 'demo-pay-101'})",
        "MERGE (:Brand {name: 'Example Bank'})",

        # Report-to-entity connections
        """
        MATCH (r:Report {id: 'R001'}), (p:Phone {value: '+910000000101'})
        MERGE (r)-[:MENTIONS_PHONE]->(p)
        """,
        """
        MATCH (r:Report {id: 'R002'}), (p:Phone {value: '+910000000101'})
        MERGE (r)-[:MENTIONS_PHONE]->(p)
        """,
        """
        MATCH (r:Report {id: 'R001'}), (u:URL {value: 'https://demo-bank.example.test'})
        MERGE (r)-[:LINKS_TO]->(u)
        """,
        """
        MATCH (r:Report {id: 'R002'}), (u:URL {value: 'https://demo-bank.example.test'})
        MERGE (r)-[:LINKS_TO]->(u)
        """,
        """
        MATCH (r:Report {id: 'R002'}), (p:PaymentHandle {value: 'demo-pay-101'})
        MERGE (r)-[:MENTIONS_PAYMENT]->(p)
        """,
        """
        MATCH (r:Report {id: 'R003'}), (p:PaymentHandle {value: 'demo-pay-101'})
        MERGE (r)-[:MENTIONS_PAYMENT]->(p)
        """,
        """
        MATCH (r:Report {id: 'R001'}), (b:Brand {name: 'Example Bank'})
        MERGE (r)-[:IMPERSONATES]->(b)
        """,
        """
        MATCH (r:Report {id: 'R002'}), (b:Brand {name: 'Example Bank'})
        MERGE (r)-[:IMPERSONATES]->(b)
        """,
        """
        MATCH (r:Report {id: 'R003'}), (b:Brand {name: 'Example Bank'})
        MERGE (r)-[:IMPERSONATES]->(b)
        """,
    ]

    for query in queries:
        graph.query(query)

    result = graph.query("""
        MATCH (n)
        RETURN labels(n) AS labels, count(n) AS total
    """)

    print("ScamTrace AI synthetic graph seeded successfully!")
    print("Node counts:")
    for row in result.result_set:
        print(f"  {row[0]}: {row[1]}")

    print("\nExpected investigation:")
    print("R001 and R002 share a phone number and URL.")
    print("R002 and R003 share a payment handle.")
    print("R004 is an unrelated control example.")

if __name__ == "__main__":
    seed_graph()
