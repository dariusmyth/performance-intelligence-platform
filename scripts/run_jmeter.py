import os
import sys
import subprocess


def main():

    if len(sys.argv) < 2:
        raise Exception("RUN_ID required")

    run_id = sys.argv[1]

    base = f"results/{run_id}"
    os.makedirs(base, exist_ok=True)

    jmx_file = f"jmx/{run_id}_test_plan.jmx"
    jtl_file = f"{base}/results.jtl"

    print(f"Running JMeter: {jmx_file}")

    cmd = [
        "jmeter",
        "-n",
        "-t", jmx_file,
        "-l", jtl_file,
        "-e",
        "-o", f"{base}/jmeter-report"
    ]

    # IMPORTANT: fail pipeline if JMeter fails
    result = subprocess.run(cmd)

    if result.returncode != 0:
        raise Exception("JMeter execution failed")

    # Validate JTL exists and is not empty
    if not os.path.exists(jtl_file) or os.path.getsize(jtl_file) == 0:
        raise Exception("JTL file missing or empty")

    print(f"JMeter completed: {jtl_file}")


if __name__ == "__main__":
    main()