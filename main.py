
import networkx as nx
import pandas as pd
import os
import matplotlib.pyplot as plt

# Dataset location
DATASET_PATH = "dataset/facebook_combined.txt"

# Create output folder
os.makedirs("outputs", exist_ok=True)

print("Loading Facebook Social Network Dataset...")

# Load Facebook friendship network
G = nx.read_edgelist(
    DATASET_PATH,
    nodetype=int,
    create_using=nx.Graph()
)

# Display network information
print("\n===== FACEBOOK NETWORK ANALYSIS =====")
print("Total Users:", G.number_of_nodes())
print("Total Friend Connections:", G.number_of_edges())
print("Is Network Connected:", nx.is_connected(G))

print("\nCalculating centrality measures...")

# Calculate SNA metrics
degree = nx.degree_centrality(G)
betweenness = nx.betweenness_centrality(G, k=500, seed=42)
closeness = nx.closeness_centrality(G)
pagerank = nx.pagerank(G)

# Create results table
df = pd.DataFrame({
    "User_ID": list(G.nodes()),
    "Degree": [degree[n] for n in G.nodes()],
    "Betweenness": [betweenness[n] for n in G.nodes()],
    "Closeness": [closeness[n] for n in G.nodes()],
    "PageRank": [pagerank[n] for n in G.nodes()]
})

# Normalize values
for col in ["Degree", "Betweenness", "Closeness", "PageRank"]:
    maximum = df[col].max()
    if maximum > 0:
        df[col] = df[col] / maximum

# Calculate influence score
df["Influence_Score"] = (
    0.30 * df["Degree"] +
    0.25 * df["Betweenness"] +
    0.20 * df["Closeness"] +
    0.25 * df["PageRank"]
)

# Rank users
df = df.sort_values(
    by="Influence_Score",
    ascending=False
)

df["Rank"] = range(1, len(df) + 1)

# Save results
df.to_csv("outputs/influencer_results.csv", index=False)

print("\n===== TOP 10 INFLUENTIAL USERS =====")
print(
    df[["Rank", "User_ID", "Influence_Score"]]
    .head(10)
    .to_string(index=False)
)

print("\nAnalysis completed successfully!")
print("Results saved in outputs/influencer_results.csv")

import community as community_louvain

print("\nDetecting Facebook communities...")

# Apply Louvain community detection
partition = community_louvain.best_partition(
    G,
    random_state=42
)

# Add community information to the results
df["Community"] = df["User_ID"].map(partition)

# Save updated results
df.to_csv("outputs/influencer_results.csv", index=False)

# Count communities
total_communities = len(set(partition.values()))

print("\n===== COMMUNITY DETECTION RESULTS =====")
print("Total Communities Found:", total_communities)

print("\nTop 10 Community Sizes:")
community_sizes = pd.Series(partition).value_counts().head(10)
print(community_sizes.to_string())

print("\nCommunity detection completed!")

print("\nCreating network visualisation...")

# Find the largest community
largest_community_id = max(
    set(partition.values()),
    key=lambda c: list(partition.values()).count(c)
)

# Extract users belonging to that community
community_nodes = [
    node for node in G.nodes()
    if partition[node] == largest_community_id
]

# Create a smaller graph
subgraph = G.subgraph(community_nodes).copy()

# Calculate node positions
pos = nx.spring_layout(
    subgraph,
    seed=42,
    iterations=30
)

# Draw the graph
plt.figure(figsize=(14, 10))

nx.draw_networkx_edges(
    subgraph,
    pos,
    alpha=0.15,
    edge_color="gray",
    width=0.5
)

nx.draw_networkx_nodes(
    subgraph,
    pos,
    node_size=20,
    node_color=[
        subgraph.degree(node)
        for node in subgraph.nodes()
    ],
    cmap=plt.cm.viridis
)

plt.title(
    f"Largest Facebook Community - Community {largest_community_id}"
)

plt.axis("off")

# Save the graph
plt.savefig(
    "outputs/largest_community.png",
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("Network visualisation saved successfully!")
