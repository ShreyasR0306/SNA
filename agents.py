
import json
import os
import pandas as pd
from pathlib import Path
from typing import TypedDict
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, START, END

# =========================================
# 1. PROJECT PATHS
# =========================================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

ENHANCED_RESULTS_PATH = (
    OUTPUT_DIR / "enhanced_influencer_results.csv"
)

BRIDGE_USERS_PATH = OUTPUT_DIR / "bridge_users.csv"

REPORT_PATH = OUTPUT_DIR / "agent_report.txt"

SIMULATION_RESULTS_PATH = (
    OUTPUT_DIR / "latest_diffusion_simulation.json"
)


# =========================================
# 2. GROQ API CONFIGURATION
# =========================================

load_dotenv(BASE_DIR / ".env", override=True)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "Groq API key not found. Check your .env file."
    )

client = Groq(api_key=api_key)


# =========================================
# 3. SHARED AGENT STATE
# =========================================

class AgentState(TypedDict, total=False):
    network_summary: str
    top_influencers: str
    community_summary: str
    recommendations: str
    simulation_summary: str
    final_report: str


# =========================================
# 4. LOAD ENHANCED DATA
# =========================================

def load_results():

    if not ENHANCED_RESULTS_PATH.exists():
        raise FileNotFoundError(
            "Enhanced results not found. "
            "Run python enhancements.py first."
        )

    df = pd.read_csv(ENHANCED_RESULTS_PATH)

    required_columns = [
        "User_ID",
        "Community",
        "Enhanced_Influence_Score"
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(
                f"Required column missing: {column}"
            )

    df["User_ID"] = pd.to_numeric(
        df["User_ID"], errors="coerce"
    )

    df["Community"] = pd.to_numeric(
        df["Community"], errors="coerce"
    )

    df = df.dropna(
        subset=["User_ID", "Community"]
    ).copy()

    df["User_ID"] = df["User_ID"].astype(int)
    df["Community"] = df["Community"].astype(int)

    return df


# =========================================
# 5. HELPER FUNCTION
# =========================================

def get_numeric_column(df, column):

    if column in df.columns:
        return pd.to_numeric(
            df[column], errors="coerce"
        ).fillna(0)

    return pd.Series(0.0, index=df.index)


def load_simulation_summary():

    if not SIMULATION_RESULTS_PATH.exists():
        return "No diffusion simulation results are available."

    with SIMULATION_RESULTS_PATH.open(
        "r",
        encoding="utf-8"
    ) as simulation_file:
        results = json.load(simulation_file)

    required_fields = {
        "starting_user",
        "spread_probability",
        "max_rounds",
        "random_seed",
        "total_users",
        "total_influenced",
        "reach_percentage",
        "round_results"
    }

    if not isinstance(results, dict):
        raise ValueError(
            "Saved diffusion simulation results must be a JSON object."
        )

    missing_fields = required_fields.difference(results)

    if missing_fields:
        raise ValueError(
            "Saved diffusion simulation results are missing fields: "
            + ", ".join(sorted(missing_fields))
        )

    if not isinstance(results["round_results"], list):
        raise ValueError(
            "Saved diffusion round results must be a list."
        )

    try:
        starting_user = int(results["starting_user"])
        spread_probability = float(results["spread_probability"])
        max_rounds = int(results["max_rounds"])
        random_seed = int(results["random_seed"])
        total_users = int(results["total_users"])
        total_influenced = int(results["total_influenced"])
        reach_percentage = float(results["reach_percentage"])
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Saved diffusion simulation summary contains invalid values."
        ) from error

    round_lines = []

    for index, row in enumerate(results["round_results"]):
        if not isinstance(row, dict):
            raise ValueError(
                f"Saved diffusion round {index} must be a JSON object."
            )

        try:
            round_number = int(row["Round"])
            newly_influenced = int(row["Newly Influenced"])
            cumulative_influenced = int(row["Total Influenced"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Saved diffusion round {index} has invalid values."
            ) from error

        round_lines.append(
            f"Round {round_number}: {newly_influenced} newly influenced; "
            f"{cumulative_influenced} total influenced"
        )

    return (
        "LATEST INDEPENDENT CASCADE SIMULATION\n"
        f"Starting anonymous user ID: {starting_user}\n"
        f"Spread probability: {spread_probability:.0%}\n"
        f"Configured maximum rounds: {max_rounds}\n"
        f"Random seed: {random_seed}\n"
        f"Network users: {total_users}\n"
        f"Total influenced in this simulation: {total_influenced}\n"
        f"Network reach: {reach_percentage:.2f}%\n"
        "Round-by-round results:\n"
        + "\n".join(round_lines)
    )


# =========================================
# AGENT 1: NETWORK ANALYSIS
# =========================================

def network_analysis_agent(state: AgentState):

    df = load_results()

    degree = get_numeric_column(
        df, "Degree_Centrality"
    )

    betweenness = get_numeric_column(
        df, "Betweenness_Centrality"
    )

    closeness = get_numeric_column(
        df, "Closeness_Centrality"
    )

    summary = (
        "FACEBOOK NETWORK STATISTICS\n"
        "---------------------------\n"
        f"Total users analysed: {len(df)}\n"
        f"Total communities: {df['Community'].nunique()}\n"
        f"Average degree centrality: {degree.mean():.6f}\n"
        f"Average betweenness centrality: "
        f"{betweenness.mean():.6f}\n"
        f"Average closeness centrality: "
        f"{closeness.mean():.6f}\n"
    )

    print("Agent 1: Network Analysis completed.")

    return {"network_summary": summary}


# =========================================
# AGENT 2: INFLUENCER DETECTION
# =========================================

def influencer_detection_agent(state: AgentState):

    df = load_results()

    top = df.nlargest(
        10, "Enhanced_Influence_Score"
    )

    columns = [
        "User_ID",
        "Enhanced_Influence_Score",
        "Community",
        "Degree_Centrality",
        "Betweenness_Centrality"
    ]

    columns = [
        col for col in columns if col in df.columns
    ]

    result = top[columns].to_string(index=False)

    print("Agent 2: Influencer Detection completed.")

    return {"top_influencers": result}


# =========================================
# AGENT 3: COMMUNITY DETECTION
# =========================================

def community_detection_agent(state: AgentState):

    df = load_results()

    sizes = (
        df.groupby("Community")
        .size()
        .sort_values(ascending=False)
    )

    summary = (
        f"Total communities detected: {len(sizes)}\n\n"
        "TOP 10 COMMUNITIES BY SIZE\n"
        "--------------------------\n"
        f"{sizes.head(10).to_string()}\n"
    )

    leaders = (
        df.sort_values(
            "Enhanced_Influence_Score",
            ascending=False
        )
        .groupby("Community")
        .head(1)
    )

    summary += (
        "\nTOP INFLUENCER IN EACH COMMUNITY\n"
        "---------------------------------\n"
    )

    for _, row in leaders.iterrows():
        summary += (
            f"Community {int(row['Community'])}: "
            f"User {int(row['User_ID'])}, "
            f"Score "
            f"{row['Enhanced_Influence_Score']:.5f}\n"
        )

    print("Agent 3: Community Detection completed.")

    return {"community_summary": summary}


# =========================================
# AGENT 4: INTELLIGENT RECOMMENDATIONS
# =========================================

def recommendation_agent(state: AgentState):

    df = load_results()

    recommendations = []

    # TOP INFLUENCERS

    recommendations.append(
        "1. TOP INFLUENTIAL USERS"
    )

    top_users = df.nlargest(
        10, "Enhanced_Influence_Score"
    )

    for _, row in top_users.iterrows():

        recommendations.append(
            f"User {int(row['User_ID'])}: "
            f"Influence score "
            f"{row['Enhanced_Influence_Score']:.5f}, "
            f"Community {int(row['Community'])}"
        )

    # BRIDGE USERS

    recommendations.append(
        "\n2. IMPORTANT BRIDGE USERS"
    )

    if BRIDGE_USERS_PATH.exists():

        bridge_df = pd.read_csv(BRIDGE_USERS_PATH)

        required_bridge_columns = [
            "Cross_Community_Edge_Count",
            "Connected_Communities_Count"
        ]

        if all(
            col in bridge_df.columns
            for col in required_bridge_columns
        ):

            bridge_df = bridge_df.sort_values(
                by=[
                    "Cross_Community_Edge_Count",
                    "Connected_Communities_Count",
                    "Betweenness_Centrality"
                ],
                ascending=[False, False, False]
            )

            for _, row in bridge_df.head(10).iterrows():

                recommendations.append(
                    f"User {int(row['User_ID'])}: "
                    f"{int(row['Cross_Community_Edge_Count'])} "
                    f"cross-community edges, connects to "
                    f"{int(row['Connected_Communities_Count'])} "
                    f"other communities, "
                    f"Betweenness "
                    f"{float(row['Betweenness_Centrality']):.6f}, "
                    f"Community {int(row['Community'])}"
                )

        else:
            recommendations.append(
                "Bridge metrics are outdated. "
                "Run python enhancements.py again."
            )

    else:
        recommendations.append(
            "Bridge-user results are unavailable."
        )

    # COMMUNITY LEADERS

    recommendations.append(
        "\n3. COMMUNITY LEADERS"
    )

    leaders = (
        df.sort_values(
            "Enhanced_Influence_Score",
            ascending=False
        )
        .groupby("Community")
        .head(1)
    )

    for _, row in leaders.iterrows():

        recommendations.append(
            f"Community {int(row['Community'])}: "
            f"Leader User {int(row['User_ID'])}, "
            f"Influence score "
            f"{row['Enhanced_Influence_Score']:.5f}"
        )

    # HIGHLY CONNECTED USERS

    recommendations.append(
        "\n4. HIGHLY CONNECTED USERS"
    )

    degree_users = df.nlargest(
        5, "Degree_Centrality"
    )

    for _, row in degree_users.iterrows():

        recommendations.append(
            f"User {int(row['User_ID'])}: "
            f"Degree centrality "
            f"{row['Degree_Centrality']:.6f}"
        )

    # NETWORK RECOMMENDATIONS

    recommendations.append(
        "\n5. NETWORK-BASED RECOMMENDATIONS"
    )

    recommendations.extend([
        "- Study highly connected users to identify "
        "important network hubs.",

        "- Examine users with high betweenness "
        "centrality to identify potential bridge positions.",

        "- Analyse community leaders to understand "
        "important users within each community.",

        "- Study cross-community edges to understand "
        "connections between different communities.",

        "- Validate structural influence using real "
        "engagement data before making popularity claims."
    ])

    result = "\n".join(recommendations)

    print("Agent 4: Intelligent Recommendations completed.")

    return {"recommendations": result}


# =========================================
# AGENT 5: AI REPORT GENERATION
# =========================================

def report_generation_agent(state: AgentState):

    print(
        "Agent 5: GPT-OSS 120B generating report..."
    )

    prompt = f"""
You are an expert Social Network Analysis assistant.

Prepare a clear academic project report titled:

FACEBOOK SOCIAL NETWORK ANALYSIS
MULTI-AGENT AI REPORT

NETWORK ANALYSIS:
{state.get('network_summary', '')}

TOP INFLUENCERS:
{state.get('top_influencers', '')}

COMMUNITY DETECTION:
{state.get('community_summary', '')}

INTELLIGENT RECOMMENDATIONS:
{state.get('recommendations', '')}

LATEST DIFFUSION SIMULATION:
{load_simulation_summary()}

Organise the report into:

1. Introduction
2. Network Analysis
3. Influencer Detection
4. Community Detection
5. Bridge User Analysis
6. Community Leader Analysis
7. Influence Diffusion Simulation
8. AI-Based Recommendations
9. Conclusion
10. Limitations and Future Scope

Instructions:

- Use simple academic English.
- Explain Degree Centrality and Betweenness Centrality.
- Explain PageRank and Eigenvector Centrality.
- Explain why bridge users are important.
- Include the supplied diffusion settings and round-by-round counts.
- Explain the independent cascade model and identify the seed, selected
  starting user, spread probability and configured round limit.
- Describe simulation results as a probabilistic scenario, not actual
  Facebook sharing or a prediction of real-world behavior.
- If no simulation results are available, say so and do not invent them.
- Preserve all supplied numerical results.
- Do not invent statistics or personal information.
- Do not claim anonymous IDs are real people.
- Explain that structural influence is not the same as
  real-world social media popularity.
- Explain that cross-community edges are actual edges
  between users assigned to different detected communities.
- Mention that sampled betweenness (k=500) is an
  approximation.
"""

    # Only one Groq API call

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Social Network Analysis "
                    "academic report-writing assistant."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=2500
    )

    report = (
        response.choices[0].message.content or ""
    ).strip()

    if not report:
        raise ValueError(
            "Groq returned an empty report."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8"
    ) as file:
        file.write(report)

    print("Agent 5: AI Report Generation completed.")

    return {"final_report": report}


# =========================================
# 6. LANGGRAPH WORKFLOW
# =========================================

workflow = StateGraph(AgentState)

workflow.add_node(
    "network_analysis",
    network_analysis_agent
)

workflow.add_node(
    "influencer_detection",
    influencer_detection_agent
)

workflow.add_node(
    "community_detection",
    community_detection_agent
)

workflow.add_node(
    "recommendation",
    recommendation_agent
)

workflow.add_node(
    "report_generation",
    report_generation_agent
)

workflow.add_edge(
    START,
    "network_analysis"
)

workflow.add_edge(
    "network_analysis",
    "influencer_detection"
)

workflow.add_edge(
    "influencer_detection",
    "community_detection"
)

workflow.add_edge(
    "community_detection",
    "recommendation"
)

workflow.add_edge(
    "recommendation",
    "report_generation"
)

workflow.add_edge(
    "report_generation",
    END
)

app = workflow.compile()


# =========================================
# 7. RUN ALL FIVE AGENTS
# =========================================

if __name__ == "__main__":

    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\nStarting Facebook Multi-Agent Analysis...\n")

    try:

        result = app.invoke({})

        print(
            "\n========== AGENT 4 RECOMMENDATIONS ==========\n"
        )
        print(result["recommendations"])

        print(
            "\n========== FINAL AI REPORT ==========\n"
        )
        print(result["final_report"])

        print("\nAll 5 agents completed successfully!")

        print("Report saved at:", REPORT_PATH)

    except Exception as error:

        print("\nAGENT EXECUTION FAILED:")
        print(error)

        raise
