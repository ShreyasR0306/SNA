
import os
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

# =========================================
# 1. PROJECT PATHS
# =========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(
    BASE_DIR, "dataset", "facebook_combined.txt"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================================
# 2. MIN-MAX NORMALIZATION
# =========================================

def min_max_normalize(series):
    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return series * 0

    return (series - minimum) / (maximum - minimum)


# =========================================
# 3. MAIN ENHANCED ANALYSIS
# =========================================

def run_enhanced_analysis():

    print("\nLoading Facebook network...")

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    G = nx.read_edgelist(
        DATASET_PATH,
        nodetype=int
    )

    print("Total users:", G.number_of_nodes())
    print("Total connections:", G.number_of_edges())

    # =====================================
    # 4. DEGREE CENTRALITY
    # =====================================

    print("\nCalculating Degree Centrality...")
    degree = nx.degree_centrality(G)

    # =====================================
    # 5. BETWEENNESS CENTRALITY
    # =====================================

    print("Calculating Betweenness Centrality...")

    betweenness = nx.betweenness_centrality(
        G,
        k=500,
        seed=42
    )

    # =====================================
    # 6. CLOSENESS CENTRALITY
    # =====================================

    print("Calculating Closeness Centrality...")
    closeness = nx.closeness_centrality(G)

    # =====================================
    # 7. PAGERANK
    # =====================================

    print("Calculating PageRank...")
    pagerank = nx.pagerank(G)

    # =====================================
    # 8. EIGENVECTOR CENTRALITY
    # =====================================

    print("Calculating Eigenvector Centrality...")

    eigenvector = nx.eigenvector_centrality(
        G,
        max_iter=1000,
        tol=1e-06
    )

    # =====================================
    # 9. LOUVAIN COMMUNITY DETECTION
    # =====================================

    print("Detecting communities using Louvain...")

    communities = nx.community.louvain_communities(
        G,
        seed=42
    )

    community_map = {}

    for community_id, members in enumerate(communities):
        for node in members:
            community_map[node] = community_id

    print("Total communities detected:", len(communities))

    # =====================================
    # 10. BUILD RESULTS DATAFRAME
    # =====================================

    print("Preparing user analysis results...")

    results = pd.DataFrame({
        "User_ID": list(G.nodes()),

        "Degree_Centrality": [
            degree[node] for node in G.nodes()
        ],

        "Betweenness_Centrality": [
            betweenness[node] for node in G.nodes()
        ],

        "Closeness_Centrality": [
            closeness[node] for node in G.nodes()
        ],

        "PageRank": [
            pagerank[node] for node in G.nodes()
        ],

        "Eigenvector_Centrality": [
            eigenvector[node] for node in G.nodes()
        ],

        "Community": [
            community_map[node] for node in G.nodes()
        ]
    })

    # =====================================
    # 11. COMMUNITY DEGREE
    # =====================================

    results["Community_Degree"] = (
        results.groupby("Community")[
            "Degree_Centrality"
        ].transform("max")
    )

    # =====================================
    # 12. NORMALIZE CENTRALITY MEASURES
    # =====================================

    print("Normalizing centrality measures...")

    score_columns = [
        "Degree_Centrality",
        "Betweenness_Centrality",
        "Closeness_Centrality",
        "PageRank",
        "Eigenvector_Centrality"
    ]

    for column in score_columns:
        results[column + "_Normalized"] = (
            min_max_normalize(results[column])
        )

    # =====================================
    # 13. ENHANCED INFLUENCE SCORE
    # =====================================

    print("Calculating Enhanced Influence Score...")

    results["Enhanced_Influence_Score"] = (
        0.25 * results["Degree_Centrality_Normalized"]
        + 0.20 * results["Betweenness_Centrality_Normalized"]
        + 0.15 * results["Closeness_Centrality_Normalized"]
        + 0.20 * results["PageRank_Normalized"]
        + 0.20 * results["Eigenvector_Centrality_Normalized"]
    )

    # =====================================
    # 14. CROSS-COMMUNITY BRIDGE DETECTION
    # =====================================

    print("\nDetecting cross-community connections...")

    cross_community_edges = {
        node: 0 for node in G.nodes()
    }

    connected_communities = {
        node: set() for node in G.nodes()
    }

    cross_edge_rows = []

    # Examine every actual edge in the network

    for u, v in G.edges():

        community_u = community_map[u]
        community_v = community_map[v]

        if community_u != community_v:

            cross_community_edges[u] += 1
            cross_community_edges[v] += 1

            connected_communities[u].add(community_v)
            connected_communities[v].add(community_u)

            cross_edge_rows.append({
                "User_1": u,
                "User_2": v,
                "Community_1": community_u,
                "Community_2": community_v
            })

    # Save actual cross-community edges

    cross_edges_df = pd.DataFrame(
        cross_edge_rows,
        columns=[
            "User_1",
            "User_2",
            "Community_1",
            "Community_2"
        ]
    )

    cross_edges_df.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "cross_community_edges.csv"
        ),
        index=False
    )

    # Add bridge measurements to results

    results["Cross_Community_Edge_Count"] = (
        results["User_ID"].map(cross_community_edges)
    )

    results["Connected_Communities_Count"] = (
        results["User_ID"].map(
            lambda user: len(connected_communities[user])
        )
    )

    print("Cross-community analysis completed!")

    # =====================================
    # 15. INFLUENCER RANKING
    # =====================================

    results = results.sort_values(
        "Enhanced_Influence_Score",
        ascending=False
    ).copy()

    results["Influencer_Rank"] = range(
        1, len(results) + 1
    )

    # =====================================
    # 16. SAVE ENHANCED RESULTS
    # =====================================

    results.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "enhanced_influencer_results.csv"
        ),
        index=False
    )

    print("Enhanced influencer results saved.")

    # =====================================
    # 17. TOP INFLUENCERS IN EACH COMMUNITY
    # =====================================

    community_top = (
        results.sort_values(
            "Enhanced_Influence_Score",
            ascending=False
        )
        .groupby("Community")
        .head(5)
    )

    community_top.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "community_top_influencers.csv"
        ),
        index=False
    )

    # =====================================
    # 18. IMPROVED BRIDGE USER RANKING
    # =====================================

    print("\nRanking bridge users...")

    bridge_users = results.sort_values(
        by=[
            "Cross_Community_Edge_Count",
            "Connected_Communities_Count",
            "Betweenness_Centrality"
        ],
        ascending=[False, False, False]
    ).head(20).copy()

    bridge_users.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "bridge_users.csv"
        ),
        index=False
    )

    # =====================================
    # 19. COMMUNITY SIZE ANALYSIS
    # =====================================

    community_sizes = (
        results.groupby("Community")
        .size()
        .reset_index(name="Number_of_Users")
        .sort_values(
            "Number_of_Users",
            ascending=False
        )
    )

    community_sizes.to_csv(
        os.path.join(
            OUTPUT_DIR,
            "community_sizes.csv"
        ),
        index=False
    )

    # =====================================
    # 20. COMMUNITY SIZE VISUALIZATION
    # =====================================

    print("\nGenerating community chart...")

    plt.figure(figsize=(12, 6))

    plt.bar(
        community_sizes["Community"].astype(str),
        community_sizes["Number_of_Users"]
    )

    plt.xlabel("Community ID")
    plt.ylabel("Number of Users")
    plt.title("Facebook Network Community Sizes")

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            OUTPUT_DIR,
            "community_sizes.png"
        ),
        dpi=300
    )

    plt.close()

    # =====================================
    # 21. DISPLAY TOP 10 INFLUENCERS
    # =====================================

    print("\n========== TOP 10 INFLUENCERS ==========")

    print(
        results[
            [
                "User_ID",
                "Enhanced_Influence_Score",
                "Community"
            ]
        ].head(10).to_string(index=False)
    )

    # =====================================
    # 22. DISPLAY TOP 10 BRIDGE CANDIDATES
    # =====================================

    print("\n========== TOP 10 BRIDGE CANDIDATES ==========")

    print(
        bridge_users[
            [
                "User_ID",
                "Community",
                "Cross_Community_Edge_Count",
                "Connected_Communities_Count",
                "Betweenness_Centrality"
            ]
        ].head(10).to_string(index=False)
    )

    # =====================================
    # 23. FINAL OUTPUT
    # =====================================

    print("\n======================================")
    print("ENHANCED ANALYSIS COMPLETED SUCCESSFULLY!")
    print("======================================")

    print("\nGenerated files in outputs folder:")

    print("1. enhanced_influencer_results.csv")
    print("2. community_top_influencers.csv")
    print("3. bridge_users.csv")
    print("4. community_sizes.csv")
    print("5. community_sizes.png")
    print("6. cross_community_edges.csv")

    print("\nTotal users:", G.number_of_nodes())
    print("Total connections:", G.number_of_edges())
    print("Total communities:", len(communities))


# =========================================
# 24. RUN PROJECT
# =========================================

if __name__ == "__main__":
    run_enhanced_analysis()
