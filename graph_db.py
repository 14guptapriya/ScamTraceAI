import os
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

def get_setting(name, default=None):
    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def get_graph():
    host = get_setting("FALKORDB_HOST")
    password = get_setting("FALKORDB_PASSWORD")
    port = int(get_setting("FALKORDB_PORT", "6379"))
    username = get_setting("FALKORDB_USERNAME", "default")
    use_ssl = str(get_setting("FALKORDB_SSL", "false")).lower() == "true"
    graph_name = get_setting("FALKORDB_GRAPH", "scamtrace")


    if not host or not password:
        raise ValueError(
            "Set FALKORDB_HOST and FALKORDB_PASSWORD in .env"
        )

    # Cleaned up keyword constraints to match official driver capabilities
    client = FalkorDB(
        host=host,
        port=port,
        username=username,
        password=password,
        socket_timeout=10,
    )

    return client, client.select_graph(graph_name)


def test_connection():
    # Attempt connection and fetch returned graph instance
    client, graph = get_graph()

    try:
        # 1. Write connection test node
        graph.query("""
            CREATE (:ScamTraceConnectionTest {
                id: 'connection_test',
                status: 'connected'
            })
        """)

        # 2. Read back written node property values
        result = graph.query("""
            MATCH (n:ScamTraceConnectionTest {
                id: 'connection_test'
            })
            RETURN n.status
            LIMIT 1
        """)
        
        rows = result.result_set

        if not rows:
            raise RuntimeError("Could not read back the test node.")

        print("SUCCESS: Connected to FalkorDB!")
        print("Graph:", os.getenv("FALKORDB_GRAPH", "scamtrace"))
        # rows[0][0] targets the first index data item within the list rows matrix
        print("Test result:", rows[0][0])

        # 3. Clean up the placeholder node from the graph
        graph.query("""
            MATCH (n:ScamTraceConnectionTest {
                id: 'connection_test'
            })
            DELETE n
        """)

    except Exception as e:
        print(f"FAILED: Connection or execution issue encountered:\n{e}")
        raise e
    finally:
        client.close()


if __name__ == "__main__":
    test_connection()
