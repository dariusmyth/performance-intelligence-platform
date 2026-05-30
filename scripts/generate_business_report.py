import json
from openai import OpenAI
from trend_analysis import load_runs, build_trend

client = OpenAI()

runs = load_runs()
trend = build_trend(runs)

latest_metrics = runs[0][1]

prompt = f"""
You are a performance engineering analyst.

LATEST METRICS:
{latest_metrics}

TREND (last 5 runs):
{trend}

Generate a business report with:
- Executive summary
- SLA status
- Scenario interpretation
- Endpoint risk analysis
- Business recommendations
"""

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}]
)

run_id = runs[0][0]

with open(f"results/{run_id}/business-report.md", "w") as f:
    f.write(response.choices[0].message.content)