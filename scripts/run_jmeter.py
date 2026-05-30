import os
import sys
import subprocess


def main():

    run_id = sys.argv[1]

    base = f"results/{run_id}"
    os.makedirs(base, exist_ok=True)

    jmx = f"jmx/{run_id}_test_plan.jmx"
    jtl = f"{base}/results.jtl"

    report_dir = f"{base}/jmeter-report"

    cmd = [
        "jmeter",
        "-n",
        "-t", jmx,
        "-l", jtl,
        "-e",
        "-o", report_dir
    ]

    print("Running JMeter:", jmx)

    result = subprocess.run(cmd)

    if result.returncode != 0:
        raise Exception("JMeter failed")

    if not os.path.exists(jtl) or os.path.getsize(jtl) == 0:
        raise Exception("Empty JTL file")

    print("JMeter completed")


if __name__ == "__main__":
    main()