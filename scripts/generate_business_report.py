import os
import json
from openai import OpenAI


# -----------------------------
# Validate API Key
# -----------------------------

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise Exception(
        "OPENAI_API_KEY is missing. "
        "Check GitHub Secrets or environment variables."
    )

if api_key.strip() == "":
    raise Exception(
        "OPENAI_API_KEY is empty."
    )


# -----------------------------
# Init OpenAI client
# -----------------------------

client = OpenAI(
    api_key=api_key
)


# -----------------------------
# Load latest metrics (example)
# -----------------------------

def load_metrics():
    # You can replace this later with real JTL parsing output
    return {
        "summary": {
            "avg_response_time": 420,
            "p95": 890,
            "p99": 1200,
            "error_rate": 0.2
        },
        "scenarios": [
            {
                "name": "happy_path",
                "users": 50,
                "status": "PASS"
            },
            {
                "name": "peak_load",
                "users": 300,
                "status": "FAIL"
            }
        ]
    }


metrics = load_metrics()


# -----------------------------
# Build prompt
# -----------------------------

prompt = f"""
You are a performance engineering analyst.

Convert the following load test results into a BUSINESS REPORT.

Focus on:
- user experience impact
- system bottlenecks
- SLA breaches
- executive summary

DATA:
{json.dumps(metrics, indent=2)}

Output format:
- Executive Summary
- Key Findings
- Scenario Analysis
- Recommendations
"""


# -----------------------------
# Call OpenAI
# -----------------------------

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You write performance test reports."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3
)


# -----------------------------
# Save report
# -----------------------------

os.makedirs("results", exist_ok=True)

with open("results/business_report.md", "w") as f:
    f.write(response.choices[0].message.content)


print("Business report generated: results/business_report.md")