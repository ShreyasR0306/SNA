
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_PATH = os.path.join(
    BASE_DIR,
    "outputs",
    "enhanced_influencer_results.csv"
)


def compare_users(user1, user2):

    if not os.path.exists(RESULTS_PATH):
        print("Enhanced results not found.")
        print("Run python enhancements.py first.")
        return

    df = pd.read_csv(RESULTS_PATH)

    df["User_ID"] = df["User_ID"].astype(int)

    selected = df[
        df["User_ID"].isin([user1, user2])
    ]

    if len(selected) != 2:
        print("One or both user IDs were not found.")
        return

    columns = [
        "User_ID",
        "Degree_Centrality",
        "Betweenness_Centrality",
        "Closeness_Centrality",
        "PageRank",
        "Eigenvector_Centrality",
        "Enhanced_Influence_Score",
        "Influencer_Rank",
        "Community"
    ]

    print("\n========== USER COMPARISON ==========")

    print(
        selected[columns].to_string(index=False)
    )

    winner = selected.loc[
        selected["Enhanced_Influence_Score"].idxmax()
    ]

    print("\nHigher enhanced influence score:")
    print("User ID:", winner["User_ID"])
    print(
        "Score:",
        round(winner["Enhanced_Influence_Score"], 4)
    )


if __name__ == "__main__":

    print("FACEBOOK USER COMPARISON")

    first_user = int(
        input("Enter first user ID: ")
    )

    second_user = int(
        input("Enter second user ID: ")
    )

    if first_user == second_user:
        print("Please enter two different user IDs.")

    else:
        compare_users(first_user, second_user)
