
import random
import csv
from strategy import detect_signals
from simulator import Portfolio
from exchange import KrakenFuturesAPI
from config import STARTING_CAPITAL, MAX_POSITIONS

class StrategyGene:
    def __init__(self, momentum_threshold):
        self.momentum_threshold = momentum_threshold
        self.fitness = 0.0

    def mutate(self):
        self.momentum_threshold += random.uniform(-1.0, 1.0)
        self.momentum_threshold = max(1.0, min(25.0, self.momentum_threshold))

def evaluate_strategy(gene, tickers, ticks=50):
    portfolio = Portfolio(initial_cash=STARTING_CAPITAL, max_open_positions=MAX_POSITIONS)
    for _ in range(ticks):
        signals = detect_signals(tickers, limit=MAX_POSITIONS, override_threshold=gene.momentum_threshold)
        for symbol, signal in signals.items():
            portfolio.execute_trade(
                symbol=symbol,
                direction=signal["direction"],
                data=tickers[symbol],
                leverage=signal.get("leverage"),
                scalp=signal.get("scalp", False),
                simulate=True
            )
        portfolio.update_positions(tickers)
    total_gain = sum(trade["gain"] for trade in portfolio.trade_history)
    total_capital = sum(trade["capital_used"] for trade in portfolio.trade_history)
    roe = (total_gain / total_capital) if total_capital > 0 else 0
    gene.fitness = roe
    return roe

def evolve(population_size=10, generations=5):
    api = KrakenFuturesAPI()
    tickers = api.get_tickers()

    population = [StrategyGene(random.uniform(5.0, 15.0)) for _ in range(population_size)]

    with open("evolution_results.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Generation", "Gene#", "Momentum_Threshold", "ROE_Fitness"])

        for gen in range(generations):
            print(f"Generation {gen + 1}")
            for i, gene in enumerate(population):
                evaluate_strategy(gene, tickers)
                writer.writerow([gen + 1, i + 1, round(gene.momentum_threshold, 4), round(gene.fitness, 4)])

            population.sort(key=lambda g: g.fitness, reverse=True)
            print("Top 3 thresholds:", [round(g.momentum_threshold, 2) for g in population[:3]])

            # Mutation and replacement
            survivors = population[:population_size // 2]
            new_gen = survivors.copy()
            while len(new_gen) < population_size:
                child = StrategyGene(random.choice(survivors).momentum_threshold)
                child.mutate()
                new_gen.append(child)

            population = new_gen

if __name__ == "__main__":
    evolve()
