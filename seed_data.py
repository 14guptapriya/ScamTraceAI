from graph_db import get_graph


def seed_graph():
    client, graph = get_graph()

    reports = [
        {
            "id": "R001",
            "title": "Bank account verification SMS",
            "description": "SMS requests bank account verification through a suspicious link.",
            "risk": "High",
            "scam_type": "bank_impersonation",
            "tactics": "urgency,credential_theft,brand_impersonation",
            "payment_sequence": "sms,verification_link,credential_request",
            "phone": "+910000000101",
            "url": "https://demo-bank.example.test",
            "payment": None,
            "brand": "Example Bank",
        },
        {
            "id": "R002",
            "title": "Fake bank support call",
            "description": "Caller claims to be bank support and asks the victim to verify account details.",
            "risk": "High",
            "scam_type": "bank_impersonation",
            "tactics": "urgency,credential_theft,brand_impersonation",
            "payment_sequence": "phone_call,verification_request,payment_demand",
            "phone": "+910000000101",
            "url": "https://demo-bank.example.test",
            "payment": "demo-pay-101",
            "brand": "Example Bank",
        },
        {
            "id": "R003",
            "title": "Suspicious payment request",
            "description": "A message asks the recipient to transfer money to an unfamiliar payment handle.",
            "risk": "Medium",
            "scam_type": "payment_scam",
            "tactics": "payment_pressure,unknown_recipient",
            "payment_sequence": "message,payment_request,transfer",
            "phone": None,
            "url": None,
            "payment": "demo-pay-101",
            "brand": "Wallet Services",
        },
        {
            "id": "R004",
            "title": "Unrelated delivery notification",
            "description": "A delivery notification with no verified link to the other reports.",
            "risk": "Low",
            "scam_type": "delivery_scam",
            "tactics": "delivery_impersonation,tracking_link",
            "payment_sequence": "delivery_message,tracking_request",
            "phone": None,
            "url": None,
            "payment": None,
            "brand": "Delivery Services",
        },
        {
            "id": "R005",
            "title": "Urgent account security alert",
            "description": "A different sender warns of account suspension and requests credentials through another link.",
            "risk": "High",
            "scam_type": "bank_impersonation",
            "tactics": "urgency,credential_theft,brand_impersonation",
            "payment_sequence": "security_message,verification_link,credential_request",
            "phone": "+910000000505",
            "url": "https://account-check.example.test",
            "payment": "demo-pay-505",
            "brand": "Secure Finance",
        },
        {
            "id": "R006",
            "title": "Unrelated prize notification",
            "description": "A prize notification uses a phone number that also appears in another report; the remaining details differ.",
            "risk": "Medium",
            "scam_type": "prize_scam",
            "tactics": "prize_claim,advance_fee",
            "payment_sequence": "prize_message,fee_request,transfer",
            "phone": "+910000000101",
            "url": None,
            "payment": "demo-prize-606",
            "brand": "Prize Centre",
        },
    ]

    # Remove old demo report-to-brand relationships so stale
    # relationships from earlier seed runs do not distort the demo.
    graph.query("""
        MATCH (r:Report)-[rel:IMPERSONATES]->(:Brand)
        WHERE r.id IN ['R001', 'R002', 'R003', 'R004', 'R005', 'R006']
        DELETE rel
    """)

    for item in reports:
        graph.query("""
            MERGE (r:Report {id: $id})
            SET r.title = $title,
                r.description = $description,
                r.source = 'Synthetic demo data',
                r.risk = $risk,
                r.scam_type = $scam_type,
                r.tactics = $tactics,
                r.payment_sequence = $payment_sequence
        """, {
            key: item[key]
            for key in [
                "id", "title", "description", "risk",
                "scam_type", "tactics", "payment_sequence"
            ]
        })

        # Remove old optional identifier relationships for these reports,
        # then recreate them from this seed configuration.
        graph.query("""
            MATCH (r:Report {id: $id})-[rel]->(e)
            WHERE type(rel) IN [
                'MENTIONS_PHONE', 'LINKS_TO', 'MENTIONS_PAYMENT'
            ]
            DELETE rel
        """, {"id": item["id"]})

        if item["phone"]:
            graph.query("""
                MERGE (e:Phone {value: $value})
                WITH e
                MATCH (r:Report {id: $id})
                MERGE (r)-[:MENTIONS_PHONE]->(e)
            """, {"id": item["id"], "value": item["phone"]})

        if item["url"]:
            graph.query("""
                MERGE (e:URL {value: $value})
                WITH e
                MATCH (r:Report {id: $id})
                MERGE (r)-[:LINKS_TO]->(e)
            """, {"id": item["id"], "value": item["url"]})

        if item["payment"]:
            graph.query("""
                MERGE (e:PaymentHandle {value: $value})
                WITH e
                MATCH (r:Report {id: $id})
                MERGE (r)-[:MENTIONS_PAYMENT]->(e)
            """, {"id": item["id"], "value": item["payment"]})

        graph.query("""
            MERGE (b:Brand {name: $brand})
            WITH b
            MATCH (r:Report {id: $id})
            MERGE (r)-[:IMPERSONATES]->(b)
        """, {"id": item["id"], "brand": item["brand"]})

    print("ScamTrace AI demo data seeded.")
    print("R001-R002: direct phone and URL overlap")
    print("R001-R003: indirect connection through R002")
    print("R001-R005: similar tactics, different identifiers")
    print("R001-R006: shared phone, different scam pattern")
    print("R004: unrelated control report")

    client.close()


if __name__ == "__main__":
    seed_graph()