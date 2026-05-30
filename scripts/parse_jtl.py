import sys
import os
import pandas as pd
import numpy as np
import json


def main():

    run_id = sys.argv[1]

    jtl = f"results/{run_id}/results.jtl"
    out = f"results/{run_id}/metrics.json"

    df = pd.read_csv(jtl)

    if df.empty:
        raise Exception("Empty JTL")

    df["elapsed"] = pd.to_numeric(df["elapsed"], errors="coerce")
    df = df.dropna(subset=["elapsed"])

    avg = df["elapsed"].mean()
    p95 = df["elapsed"].quantile(0.95)
    p99 = df["elapsed"].quantile(0.99)

    total = len(df)
    errors = len(df[df["success"] != True])

    error_rate = (errors / total) * 100 if total else 0
    throughput = total / (df["elapsed"].sum() / 1000) if df["elapsed"].sum() else 0

    def safe(x):
        return float(x) if not (pd.isna(x) or np.isinf(x)) else 0.0

    metrics = {
        "avg_response_time_ms": safe(avg),
        "p95_ms": safe(p95),
        "p99_ms": safe(p99),
        "error_rate_percent": safe(error_rate),
        "throughput_req_per_sec": safe(throughput)
    }

    os.makedirs(os.path.dirname(out), exist_ok=True)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(out)


if __name__ == "__main__":
    main()