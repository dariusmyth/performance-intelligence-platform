import pandas as pd
import json
import sys

run_id = sys.argv[1]
path = f"results/{run_id}/results.jtl"

df = pd.read_csv(path)

metrics = {
    "avg_response_time": float(df["elapsed"].mean()),
    "p95_response_time": float(df["elapsed"].quantile(0.95)),
    "p99_response_time": float(df["elapsed"].quantile(0.99)),
    "error_rate": float((df["success"] == False).mean() * 100),
    "throughput": float(len(df) / ((df["timeStamp"].max() - df["timeStamp"].min()) / 1000))
}

with open(f"results/{run_id}/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)