
import os
import networkx as nx
import pandas as pd
from pyvis.network import Network


# =========================================
# PROJECT PATHS
# =========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR, "dataset", "facebook_combined.txt"
)

RESULTS_PATH = os.path.join(
    BASE_DIR, "outputs", "enhanced_influencer_results.csv"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR, "interactive_network.html"
)


# =========================================
# CREATE INTERACTIVE NETWORK
# =========================================

def create_network_graph():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading Facebook dataset...")

    G = nx.read_edgelist(
        DATASET_PATH,
        nodetype=int
    )

    print("Total users:", G.number_of_nodes())
    print("Total connections:", G.number_of_edges())

    # Load enhanced influencer results
    results = pd.read_csv(RESULTS_PATH)

    required_columns = [
        "User_ID",
        "Enhanced_Influence_Score",
        "Community"
    ]

    for column in required_columns:
        if column not in results.columns:
            raise ValueError(
                f"Missing column in enhanced results: {column}"
            )

    results["User_ID"] = results["User_ID"].astype(int)

    # =====================================
    # SELECT TOP 100 INFLUENCERS
    # =====================================

    top_users = results.nlargest(
        100,
        "Enhanced_Influence_Score"
    )["User_ID"].tolist()

    # Keep only users present in the original graph
    selected_users = [
        user for user in top_users if user in G
    ]

    subgraph = G.subgraph(selected_users).copy()

    print("Selected users:", subgraph.number_of_nodes())

    if subgraph.number_of_nodes() == 0:
        raise ValueError("No selected users found in the network.")

    result_lookup = results.set_index("User_ID")

    # =====================================
    # CREATE PYVIS NETWORK
    # =====================================

    net = Network(
        height="750px",
        width="100%",
        bgcolor="#111827",
        font_color="white",
        directed=False,
        notebook=False,
        cdn_resources="in_line"
    )

    # =====================================
    # ADD NODES
    # =====================================

    for user in selected_users:

        row = result_lookup.loc[user]

        score = float(row["Enhanced_Influence_Score"])
        community = int(row["Community"])

        node_size = 12 + score * 35

        net.add_node(
            int(user),
            label=str(user),
            title=(
                f"User ID: {user}\n"
                f"Community: {community}\n"
                f"Influence Score: {score:.5f}"
            ),
            size=node_size,
            group=community
        )

    # =====================================
    # ADD MAXIMUM 1000 EDGES
    # =====================================

    MAX_EDGES = 1000

    edges_added = 0

    for source, target in subgraph.edges():

        if edges_added >= MAX_EDGES:
            break

        net.add_edge(
            int(source),
            int(target)
        )

        edges_added += 1

    # =====================================
    # GRAPH SETTINGS
    # =====================================

    net.set_options("""
    {
      "nodes": {
        "shape": "dot",
        "font": {
          "size": 14,
          "color": "#ffffff"
        },
        "borderWidth": 1
      },
      "edges": {
        "color": {
          "color": "rgba(148,163,184,0.5)",
          "highlight": "#ffffff"
        },
        "width": 1,
        "smooth": false
      },
      "physics": {
        "enabled": true,
        "solver": "barnesHut",
        "stabilization": {
          "enabled": true,
          "iterations": 300,
          "fit": true
        },
        "barnesHut": {
          "gravitationalConstant": -3000,
          "centralGravity": 0.3,
          "springLength": 150,
          "springConstant": 0.02,
          "damping": 0.5,
          "avoidOverlap": 0.2
        }
      },
      "interaction": {
        "hover": true,
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "navigationButtons": true
      }
    }
    """)

    # =====================================
    # GENERATE HTML
    # =====================================

    print("Generating interactive HTML...")

    html_content = net.generate_html()

    if not html_content or len(html_content) < 1000:
        raise RuntimeError("Generated HTML is empty or incomplete.")

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(html_content)

    # =====================================
    # VERIFY HTML FILE
    # =====================================

    file_size = os.path.getsize(OUTPUT_PATH)

    print("\n===================================")
    print("INTERACTIVE GRAPH GENERATED!")
    print("===================================")

    print("HTML location:", OUTPUT_PATH)
    print("HTML file size:", file_size, "bytes")
    print("Users displayed:", len(selected_users))
    print("Connections displayed:", edges_added)

    if file_size > 10000:
        print("HTML verification: SUCCESS")
    else:
        print("WARNING: HTML file is unusually small.")


# =========================================
# MAIN PROGRAM
# =========================================

if __name__ == "__main__":

    if not os.path.exists(DATASET_PATH):
        print("ERROR: Facebook dataset not found.")

    elif not os.path.exists(RESULTS_PATH):
        print("ERROR: Enhanced results not found.")
        print("Run python enhancements.py first.")

    else:
        try:
            create_network_graph()

        except Exception as error:
            print("GRAPH GENERATION FAILED:")
            print(error)
