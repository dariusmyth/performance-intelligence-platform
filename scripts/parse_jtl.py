import sys
import os
import pandas as pd
import numpy as np
import json


def main():

    run_id = sys.argv[1]

    jtl_path = f"results/{run_id}/results.jtl"
    output_path = f"results/{run_id}/metrics.json"
    jmx_path = f"jmx/{run_id}_test_plan.jmx"

    # -----------------------------
    # Validate file exists
    # -----------------------------
    if not os.path.exists(jtl_path):
        raise Exception(f"JTL missing: {jtl_path}")

    df = pd.read_csv(jtl_path)

    # -----------------------------
    # DEBUG MODE (IMPORTANT)
    # -----------------------------
    if df is None or df.empty:
        print("❌ EMPTY JTL DETECTED")
        print(f"JTL file: {jtl_path}")
        print(f"JMX file: {jmx_path}")

        print("\n👉 Possible causes:")
        print("- JMeter test did not execute any requests")
        print("- Invalid JMX structure (very likely)")
        print("- Thread group duration/ramp misconfigured")
        print("- Samplers not attached to ThreadGroup properly")

        # DO NOT silently pass → but fail with context
        raise Exception("Empty JTL - no samples collected")

    # -----------------------------
    # Safe numeric conversion
    # -----------------------------
    df["elapsed"] = pd.to_numeric(df["elapsed"], errors="coerce")
    df = df.dropna(subset=["elapsed"])

    if df.empty:
        raise Exception("No valid response times in JTL")

    # -----------------------------
    # Metrics calculation
    # -----------------------------
    avg = df["elapsed"].mean()
    p95 = df["elapsed"].quantile(0.95)
    p99 = df["elapsed"].quantile(0.99)

    total = len(df)
    failures = len(df[df["success"] != True])

    error_rate = (failures / total) * 100 if total > 0 else 0
    throughput = total / (df["elapsed"].sum() / 1000) if df["elapsed"].sum() > 0 else 0

    def safe(v):
        return float(v) if not (pd.isna(v) or np.isinf(v)) else 0.0

    metrics = {
        "avg_response_time_ms": safe(avg),
        "p95_ms": safe(p95),
        "p99_ms": safe(p99),
        "error_rate_percent": safe(error_rate),
        "throughput_req_per_sec": safe(throughput),
        "sample_count": int(total)
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Metrics written:", output_path)


if __name__ == "__main__":
    main()