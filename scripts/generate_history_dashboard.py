import os
import json
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader("templates"))
template = env.get_template("history.html.j2")

runs = sorted(os.listdir("results"))
runs = [r for r in runs if "_" in r]

data = []
labels = []

for r in runs:
    try:
        with open(f"results/{r}/metrics.json") as f:
            metrics = json.load(f)

        data.append({
            "id": r,
            "metrics": metrics
        })

        labels.append(r)

    except:
        continue

chart = {
    "labels": labels,
    "avg": [r["metrics"]["avg_response_time"] for r in data],
    "p95": [r["metrics"]["p95_response_time"] for r in data],
    "p99": [r["metrics"]["p99_response_time"] for r in data],
}

html = template.render(runs=data, chart=chart)

with open("results/history.html", "w") as f:
    f.write(html)