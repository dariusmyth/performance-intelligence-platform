import os
import sys
import subprocess


def main():

    if len(sys.argv) < 2:
        raise Exception("RUN_ID required")

    run_id = sys.argv[1]

    base = f"results/{run_id}"
    os.makedirs(base, exist_ok=True)

    jtl_path = f"{base}/results.jtl"

    print(f"Starting JMeter run: {run_id}")

    cmd = [
        "jmeter",
        "-n",
        "-t",
        "jmx/test_plan.jmx",
        "-l",
        jtl_path
    ]

    subprocess.run(cmd, check=True)

    print(f"Completed JMeter run: {run_id}")
    print(f"Results: {jtl_path}")


if __name__ == "__main__":
    main()