import json
import yaml
from pathlib import Path
from lxml import etree

POSTMAN_FILE = "postman/collection.json"
PERF_CONFIG_FILE = "config/performance-config.yaml"

OUTPUT_JMX = "jmx/test_plan.jmx"


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_output_dir():
    Path("jmx").mkdir(exist_ok=True)


# --------------------------------------------------
# Postman Collection Flattening
# --------------------------------------------------

def extract_requests(items):

    requests = []

    for item in items:

        if "request" in item:
            requests.append(item)

        if "item" in item:
            requests.extend(
                extract_requests(item["item"])
            )

    return requests


# --------------------------------------------------
# XML helpers
# --------------------------------------------------

def add_hash_tree(parent):
    return etree.SubElement(parent, "hashTree")


# --------------------------------------------------
# Test Plan
# --------------------------------------------------

def create_test_plan(root):

    test_plan = etree.SubElement(
        root,
        "TestPlan",
        guiclass="TestPlanGui",
        testclass="TestPlan",
        testname="Performance Intelligence Platform",
        enabled="true"
    )

    etree.SubElement(
        test_plan,
        "stringProp",
        name="TestPlan.comments"
    )

    etree.SubElement(
        test_plan,
        "boolProp",
        name="TestPlan.functional_mode"
    ).text = "false"

    etree.SubElement(
        test_plan,
        "boolProp",
        name="TestPlan.serialize_threadgroups"
    ).text = "false"

    return test_plan


# --------------------------------------------------
# Thread Group
# --------------------------------------------------

def create_thread_group(
        parent,
        scenario_name,
        users,
        ramp_up,
        duration
):

    tg = etree.SubElement(
        parent,
        "ThreadGroup",
        guiclass="ThreadGroupGui",
        testclass="ThreadGroup",
        testname=scenario_name,
        enabled="true"
    )

    etree.SubElement(
        tg,
        "stringProp",
        name="ThreadGroup.num_threads"
    ).text = str(users)

    etree.SubElement(
        tg,
        "stringProp",
        name="ThreadGroup.ramp_time"
    ).text = str(ramp_up)

    etree.SubElement(
        tg,
        "boolProp",
        name="ThreadGroup.scheduler"
    ).text = "true"

    etree.SubElement(
        tg,
        "stringProp",
        name="ThreadGroup.duration"
    ).text = str(duration * 60)

    return tg


# --------------------------------------------------
# HTTP Sampler
# --------------------------------------------------

def create_http_sampler(parent, request_item):

    request = request_item["request"]

    sampler_name = request_item.get(
        "name",
        "Unnamed Request"
    )

    method = request.get(
        "method",
        "GET"
    )

    url = request.get("url")

    protocol = "https"
    domain = ""
    path = "/"

    if isinstance(url, dict):

        protocol = url.get(
            "protocol",
            "https"
        )

        host = url.get("host", [])
        path_parts = url.get("path", [])

        domain = ".".join(host)

        if path_parts:
            path = "/" + "/".join(path_parts)

    sampler = etree.SubElement(
        parent,
        "HTTPSamplerProxy",
        guiclass="HttpTestSampleGui",
        testclass="HTTPSamplerProxy",
        testname=sampler_name,
        enabled="true"
    )

    etree.SubElement(
        sampler,
        "stringProp",
        name="HTTPSampler.protocol"
    ).text = protocol

    etree.SubElement(
        sampler,
        "stringProp",
        name="HTTPSampler.domain"
    ).text = domain

    etree.SubElement(
        sampler,
        "stringProp",
        name="HTTPSampler.path"
    ).text = path

    etree.SubElement(
        sampler,
        "stringProp",
        name="HTTPSampler.method"
    ).text = method

    return sampler


# --------------------------------------------------
# Headers
# --------------------------------------------------

def create_headers(parent, request):

    headers = request.get("header", [])

    if not headers:
        return

    manager = etree.SubElement(
        parent,
        "HeaderManager",
        guiclass="HeaderPanel",
        testclass="HeaderManager",
        testname="Headers",
        enabled="true"
    )

    collection = etree.SubElement(
        manager,
        "collectionProp",
        name="HeaderManager.headers"
    )

    for h in headers:

        element = etree.SubElement(
            collection,
            "elementProp",
            elementType="Header"
        )

        etree.SubElement(
            element,
            "stringProp",
            name="Header.name"
        ).text = h.get("key", "")

        etree.SubElement(
            element,
            "stringProp",
            name="Header.value"
        ).text = h.get("value", "")


# --------------------------------------------------
# Assertion
# --------------------------------------------------

def create_assertion(parent):

    assertion = etree.SubElement(
        parent,
        "ResponseAssertion",
        guiclass="AssertionGui",
        testclass="ResponseAssertion",
        testname="Status Code 200",
        enabled="true"
    )

    etree.SubElement(
        assertion,
        "stringProp",
        name="Assertion.test_field"
    ).text = "Assertion.response_code"

    return assertion


# --------------------------------------------------
# Think Time
# --------------------------------------------------

def create_timer(parent, delay_ms):

    timer = etree.SubElement(
        parent,
        "ConstantTimer",
        guiclass="ConstantTimerGui",
        testclass="ConstantTimer",
        testname="Think Time",
        enabled="true"
    )

    etree.SubElement(
        timer,
        "stringProp",
        name="ConstantTimer.delay"
    ).text = str(delay_ms)


# --------------------------------------------------
# Main
# --------------------------------------------------

def build_jmx():

    ensure_output_dir()

    postman = load_json(
        POSTMAN_FILE
    )

    config = load_yaml(
        PERF_CONFIG_FILE
    )

    requests = extract_requests(
        postman.get("item", [])
    )

    root = etree.Element(
        "jmeterTestPlan",
        version="1.2",
        properties="5.0",
        jmeter="5.6.3"
    )

    root_hash = add_hash_tree(root)

    create_test_plan(root_hash)

    test_plan_tree = add_hash_tree(root_hash)

    default_duration = (
        config.get("test", {})
        .get(
            "default_duration_minutes",
            10
        )
    )

    default_ramp = (
        config.get("test", {})
        .get(
            "default_ramp_up_seconds",
            60
        )
    )

    think_time = (
        config.get("test", {})
        .get(
            "think_time_ms",
            1000
        )
    )

    scenarios = config.get(
        "scenarios",
        {}
    )

    for scenario_name, scenario in scenarios.items():

        users = scenario.get(
            "users",
            10
        )

        duration = scenario.get(
            "duration_minutes",
            default_duration
        )

        ramp = scenario.get(
            "ramp_up_seconds",
            default_ramp
        )

        tg = create_thread_group(
            test_plan_tree,
            scenario_name,
            users,
            ramp,
            duration
        )

        tg_tree = add_hash_tree(
            test_plan_tree
        )

        for req in requests:

            sampler = create_http_sampler(
                tg_tree,
                req
            )

            sampler_tree = add_hash_tree(
                tg_tree
            )

            create_headers(
                sampler_tree,
                req["request"]
            )

            create_assertion(
                sampler_tree
            )

            create_timer(
                sampler_tree,
                think_time
            )

    tree = etree.ElementTree(root)

    tree.write(
        OUTPUT_JMX,
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8"
    )

    print(
        f"Generated {OUTPUT_JMX}"
    )


if __name__ == "__main__":
    build_jmx()