import os
import sys
import subprocess


def main():

    if len(sys.argv) < 2:
        raise Exception("RUN_ID required")

    run_id = sys.argv[1]

    base = f"results/{run_id}"
    os.makedirs(base, exist_ok=True)

    jtl_file = f"{base}/results.jtl"

    jmx_file = f"jmx/{run_id}_test_plan.jmx"

    print(f"Running JMeter for {run_id}")

    cmd = [
        "jmeter",
        "-n",
        "-t",
        jmx_file,
        "-l",
        jtl_file
    ]

    subprocess.run(cmd, check=True)

    print(jtl_file)


if __name__ == "__main__":
    main()