import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon, ttest_rel
import os

def load_data(filepath):
    df = pd.read_csv(filepath)
    df = df.rename(columns=lambda x: x.strip())
    df["Attempt"] = df["Attempt"].astype(int)
    df["Score"] = df["Score"].astype(float)
    return df

def filter_attempts(df):
    return df[df["Attempt"].isin([1, 2])]

def pivot_attempts(df):
    pivot = df.pivot_table(
        index=["User ID", "Topic"],
        columns="Attempt",
        values="Score",
        aggfunc="mean"
    ).reset_index()
    pivot = pivot.rename(columns={1: "Score_Attempt1", 2: "Score_Attempt2"})
    return pivot

def remove_perfect_first_attempt(df):
    return df[df["Score_Attempt1"] < 100]

def compute_improvement(df):
    df["Improvement"] = df["Score_Attempt2"] - df["Score_Attempt1"]
    return df.dropna(subset=["Score_Attempt2"])

def improvement_metrics(df):
    percent_improved = (df["Improvement"] > 0).mean() * 100
    average_improvement = df["Improvement"].mean()
    median_improvement = df["Improvement"].median()
    normalized_gain = ((df["Score_Attempt2"] - df["Score_Attempt1"]) /
                       (100 - df["Score_Attempt1"])).replace([float("inf"), -float("inf")], 0).mean()
    return {
        "percent_improved": percent_improved,
        "average_improvement": average_improvement,
        "median_improvement": median_improvement,
        "normalized_gain": normalized_gain
    }

def consistency_metrics(df):
    sd_attempt1 = df["Score_Attempt1"].std()
    sd_attempt2 = df["Score_Attempt2"].std()
    variance_reduction = sd_attempt1 - sd_attempt2
    correlation = df["Score_Attempt1"].corr(df["Score_Attempt2"])
    return {
        "sd_attempt1": sd_attempt1,
        "sd_attempt2": sd_attempt2,
        "variance_reduction": variance_reduction,
        "correlation": correlation
    }

def mastery_threshold_metrics(df, threshold=80):
    mastery1 = (df["Score_Attempt1"] >= threshold)
    mastery2 = (df["Score_Attempt2"] >= threshold)
    moved_to_mastery = (~mastery1 & mastery2).mean() * 100
    remained_below = (~mastery1 & ~mastery2).mean() * 100
    remained_mastery = (mastery1 & mastery2).mean() * 100
    return {
        "moved_to_mastery": moved_to_mastery,
        "remained_below": remained_below,
        "remained_mastery": remained_mastery
    }

def run_stats(df):
    w_stat, w_p = wilcoxon(df["Score_Attempt1"], df["Score_Attempt2"])
    t_stat, t_p = ttest_rel(df["Score_Attempt1"], df["Score_Attempt2"])
    return {
        "wilcoxon": {"stat": w_stat, "p": w_p},
        "paired_t": {"stat": t_stat, "p": t_p}
    }

def summarize(df):
    percent_improved = (df["Improvement"] > 0).mean() * 100
    mean_improvement = df["Improvement"].mean()
    mean_attempt1 = df["Score_Attempt1"].mean()
    mean_attempt2 = df["Score_Attempt2"].mean()
    improvement = improvement_metrics(df)
    consistency = consistency_metrics(df)
    mastery = mastery_threshold_metrics(df)
    return {
        "percent_improved": percent_improved,
        "mean_improvement": mean_improvement,
        "mean_attempt1": mean_attempt1,
        "mean_attempt2": mean_attempt2,
        "improvement_metrics": improvement,
        "consistency_metrics": consistency,
        "mastery_threshold_metrics": mastery,
        "sample_size": len(df)
    }

def plot_improvement_hist(df):
    plt.figure(figsize=(8,5))
    plt.hist(df["Improvement"], bins=10)
    plt.axvline(0, color='black', linestyle='--')
    plt.title("Score Improvement from Attempt 1 to Attempt 2")
    plt.xlabel("Improvement")
    plt.ylabel("Number of Users")
    plt.tight_layout()
    os.makedirs("results", exist_ok=True)
    plt.savefig("results/plot_improvement_hist.png")
    plt.close()

def plot_attempt_scatter(df):
    plt.figure(figsize=(8,5))
    plt.scatter(df["Score_Attempt1"], df["Score_Attempt2"])
    plt.plot([0, 100], [0, 100], linestyle='--', color='gray')
    plt.title("Attempt 1 vs Attempt 2 Scores")
    plt.xlabel("Attempt 1 Score")
    plt.ylabel("Attempt 2 Score")
    plt.tight_layout()
    os.makedirs("results", exist_ok=True)
    plt.savefig("results/plot_attempt_scatter.png")
    plt.close()

def main():
    df = load_data("submissions/submissions_google.csv")
    df = filter_attempts(df)
    pivot = pivot_attempts(df)
    filtered = remove_perfect_first_attempt(pivot)
    paired = compute_improvement(filtered)
    stats = run_stats(paired)
    summary = summarize(paired)
    print("\n===== Core Summary =====")
    print(f"Users included in analysis: {summary['sample_size']}")
    print(f"Percent improved: {summary['percent_improved']:.2f}")
    print(f"Mean improvement: {summary['mean_improvement']:.2f}")
    print(f"Mean Attempt 1 Score: {summary['mean_attempt1']:.2f}")
    print(f"Mean Attempt 2 Score: {summary['mean_attempt2']:.2f}")
    print("\n===== Improvement-Based Metrics =====")
    for k, v in summary["improvement_metrics"].items():
        print(f"{k}: {v:.2f}")
    print("\n===== Consistency / Stability Metrics =====")
    for k, v in summary["consistency_metrics"].items():
        print(f"{k}: {v:.2f}")
    print("\n===== Mastery Threshold Metrics =====")
    for k, v in summary["mastery_threshold_metrics"].items():
        print(f"{k}: {v:.2f}")
    print("\n===== Statistical Tests =====")
    print(stats)
    plot_improvement_hist(paired)
    plot_attempt_scatter(paired)
    print("Analysis complete. Plots saved.")

if __name__ == "__main__":
    main()
