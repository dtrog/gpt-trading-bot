
import pandas as pd
import matplotlib.pyplot as plt

def plot_evolution(csv_file="evolution_results.csv"):
    df = pd.read_csv(csv_file)
    plt.figure(figsize=(10, 6))

    # Compute metrics
    avg_roe = df.groupby("Generation")["ROE_Fitness"].mean()
    max_roe = df.groupby("Generation")["ROE_Fitness"].max()

    # Plotting
    plt.plot(avg_roe, label="Avg ROE%", marker='o')
    plt.plot(max_roe, label="Max ROE%", linestyle='--', marker='x')

    # Annotate best thresholds
    for gen in df["Generation"].unique():
        gen_data = df[df["Generation"] == gen]
        best = gen_data.loc[gen_data["ROE_Fitness"].idxmax()]
        plt.annotate(f'{best["Momentum_Threshold"]:.1f}', 
                     (gen - 1, best["ROE_Fitness"]),
                     textcoords="offset points",
                     xytext=(0, 6),
                     ha='center',
                     fontsize=8,
                     color='blue')

    plt.title("Evolution of Strategy Fitness (ROE%) with Threshold Annotations")
    plt.xlabel("Generation")
    plt.ylabel("ROE (Return on Equity %)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("evolution_plot.png")
    plt.show()

if __name__ == "__main__":
    plot_evolution()
