import json
import os
from jinja2 import Environment, FileSystemLoader

RESULTS_DIR = "results"
TEMPLATE_DIR = "templates"


def get_latest_run():
    runs = sorted(
        [r for r in os.listdir(RESULTS_DIR) if "_" in r],
        reverse=True
    )

    if not runs:
        raise Exception("No runs found")

    return runs[0]


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_business_report(run_id):
    path = f"{RESULTS_DIR}/{run_id}/business-report.md"

    if os.path.exists(path):
        with open(path) as f:
            return f.read()

    return "No report generated."


def load_last_runs(limit=5):
    runs = sorted(
        [r for r in os.listdir(RESULTS_DIR) if "_" in r],
        reverse=True
    )[:limit]

    data = []

    for run in runs:
        metrics_path = f"{RESULTS_DIR}/{run}/metrics.json"

        if os.path.exists(metrics_path):
            metrics = load_json(metrics_path)

            data.append({
                "run_id": run,
                "metrics": metrics
            })

    return data[::-1]


def build_trend(last_runs):

    return {
        "labels": [r["run_id"] for r in last_runs],
        "avg": [
            r["metrics"]["avg_response_time"]
            for r in last_runs
        ],
        "p95": [
            r["metrics"]["p95_response_time"]
            for r in last_runs
        ],
        "p99": [
            r["metrics"]["p99_response_time"]
            for r in last_runs
        ],
        "errors": [
            r["metrics"]["error_rate"]
            for r in last_runs
        ]
    }


def determine_status(metrics):

    p95 = metrics["p95_response_time"]
    error_rate = metrics["error_rate"]

    if error_rate > 5:
        return "FAIL"

    if p95 > 2000:
        return "FAIL"

    if p95 > 1000:
        return "WARNING"

    return "PASS"


def build_regression_analysis(last_runs):

    if len(last_runs) < 2:
        return []

    latest = last_runs[-1]["metrics"]
    previous = last_runs[-2]["metrics"]

    findings = []

    for metric in [
        "avg_response_time",
        "p95_response_time",
        "p99_response_time",
        "error_rate"
    ]:

        old = previous[metric]
        new = latest[metric]

        if old == 0:
            continue

        delta = ((new - old) / old) * 100

        findings.append({
            "metric": metric,
            "previous": round(old, 2),
            "current": round(new, 2),
            "change": round(delta, 2)
        })

    return findings


def build_endpoint_chart(metrics):

    endpoints = metrics.get("endpoints", {})

    labels = []
    values = []

    for endpoint, data in endpoints.items():

        labels.append(endpoint)
        values.append(data.get("p99", 0))

    return {
        "labels": labels,
        "values": values
    }


def build_scenario_chart(metrics):

    scenarios = metrics.get("scenarios", {})

    labels = []
    values = []

    for scenario, data in scenarios.items():

        labels.append(scenario)
        values.append(data.get("avg_response_time", 0))

    return {
        "labels": labels,
        "values": values
    }


def build_bottlenecks(metrics):

    endpoints = metrics.get("endpoints", {})

    items = []

    for endpoint, data in endpoints.items():

        items.append({
            "endpoint": endpoint,
            "p99": data.get("p99", 0),
            "errors": data.get("error_rate", 0)
        })

    items = sorted(
        items,
        key=lambda x: x["p99"],
        reverse=True
    )

    return items[:5]


def main():

    latest_run = get_latest_run()

    metrics = load_json(
        f"{RESULTS_DIR}/{latest_run}/metrics.json"
    )

    report = load_business_report(latest_run)

    last_runs = load_last_runs()

    trend = build_trend(last_runs)

    regressions = build_regression_analysis(last_runs)

    endpoint_chart = build_endpoint_chart(metrics)

    scenario_chart = build_scenario_chart(metrics)

    bottlenecks = build_bottlenecks(metrics)

    status = determine_status(metrics)

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR)
    )

    template = env.get_template(
        "dashboard.html.j2"
    )

    html = template.render(
        run_id=latest_run,
        status=status,
        metrics=metrics,
        report=report,
        trend_json=json.dumps(trend),
        endpoint_chart=json.dumps(endpoint_chart),
        scenario_chart=json.dumps(scenario_chart),
        regressions=regressions,
        bottlenecks=bottlenecks
    )

    output_path = (
        f"{RESULTS_DIR}/{latest_run}/dashboard.html"
    )

    with open(output_path, "w") as f:
        f.write(html)

    print(
        f"Dashboard generated: {output_path}"
    )


if __name__ == "__main__":
    main()