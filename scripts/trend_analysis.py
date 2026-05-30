import json
import os

def load_runs(limit=5):
    runs = sorted(os.listdir("results"), reverse=True)
    runs = [r for r in runs if "_" in r][:limit]

    data = []
    for r in runs:
        try:
            with open(f"results/{r}/metrics.json") as f:
                data.append((r, json.load(f)))
        except:
            continue

    return data

def build_trend(data):
    trend = {}

    keys = data[0][1].keys()

    for k in keys:
        trend[k] = [d[1][k] for d in data]

    return trend

def compare_latest(trend):
    return {
        k: trend[k][-1] - trend[k][-2] if len(trend[k]) > 1 else 0
        for k in trend
    }