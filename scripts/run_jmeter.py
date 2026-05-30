import os
import sys
import subprocess


def main():

    if len(sys.argv) < 2:
        raise Exception(
            "Usage: python run_jmeter.py <RUN_ID>"
        )

    run_id = sys.argv[1]

    result_dir = f"results/{run_id}"

    os.makedirs(result_dir, exist_ok=True)

    jtl_file = f"{result_dir}/results.jtl"

    cmd = [
        "jmeter",
        "-n",
        "-t",
        "jmx/test_plan.jmx",
        "-l",
        jtl_file
    ]

    print(
        f"Running JMeter for run {run_id}"
    )

    subprocess.run(
        cmd,
        check=True
    )

    print(
        f"JTL created: {jtl_file}"
    )


if __name__ == "__main__":
    main()