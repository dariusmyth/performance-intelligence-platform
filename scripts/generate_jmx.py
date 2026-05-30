import json
import yaml
import sys
from pathlib import Path
from lxml import etree

POSTMAN_FILE = "postman/collection.json"
CONFIG_FILE = "config/performance-config.yaml"


# ---------------------------
# Loaders
# ---------------------------

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dir():
    Path("jmx").mkdir(exist_ok=True)


# ---------------------------
# Flatten Postman
# ---------------------------

def extract_requests(items):
    requests = []

    for item in items:
        if "request" in item:
            requests.append(item)

        if "item" in item:
            requests.extend(extract_requests(item["item"]))

    return requests


# ---------------------------
# JMeter helpers
# ---------------------------

def add_hash_tree(parent):
    return etree.SubElement(parent, "hashTree")


def create_test_plan(root):
    tp = etree.SubElement(
        root,
        "TestPlan",
        guiclass="TestPlanGui",
        testclass="TestPlan",
        testname="Performance Test Plan",
        enabled="true"
    )

    etree.SubElement(tp, "stringProp", name="TestPlan.comments")
    etree.SubElement(tp, "boolProp", name="TestPlan.functional_mode").text = "false"
    etree.SubElement(tp, "boolProp", name="TestPlan.serialize_threadgroups").text = "false"

    return tp


def create_thread_group(parent, name, users, ramp, duration):
    tg = etree.SubElement(
        parent,
        "ThreadGroup",
        guiclass="ThreadGroupGui",
        testclass="ThreadGroup",
        testname=name,
        enabled="true"
    )

    etree.SubElement(tg, "stringProp", name="ThreadGroup.num_threads").text = str(users)
    etree.SubElement(tg, "stringProp", name="ThreadGroup.ramp_time").text = str(ramp)

    etree.SubElement(tg, "boolProp", name="ThreadGroup.scheduler").text = "true"
    etree.SubElement(tg, "stringProp", name="ThreadGroup.duration").text = str(duration * 60)

    return tg


def create_http_sampler(parent, req):
    request = req["request"]

    method = request.get("method", "GET")
    url = request.get("url", {})

    protocol = url.get("protocol", "https") if isinstance(url, dict) else "https"
    host = ".".join(url.get("host", [])) if isinstance(url, dict) else ""
    path = "/" + "/".join(url.get("path", [])) if isinstance(url, dict) else "/"

    sampler = etree.SubElement(
        parent,
        "HTTPSamplerProxy",
        guiclass="HttpTestSampleGui",
        testclass="HTTPSamplerProxy",
        testname=req.get("name", "request"),
        enabled="true"
    )

    etree.SubElement(sampler, "stringProp", name="HTTPSampler.protocol").text = protocol
    etree.SubElement(sampler, "stringProp", name="HTTPSampler.domain").text = host
    etree.SubElement(sampler, "stringProp", name="HTTPSampler.path").text = path
    etree.SubElement(sampler, "stringProp", name="HTTPSampler.method").text = method

    return sampler


def create_headers(parent, request):
    headers = request.get("header", [])

    if not headers:
        return

    hm = etree.SubElement(
        parent,
        "HeaderManager",
        guiclass="HeaderPanel",
        testclass="HeaderManager",
        testname="Headers",
        enabled="true"
    )

    coll = etree.SubElement(hm, "collectionProp", name="HeaderManager.headers")

    for h in headers:
        el = etree.SubElement(coll, "elementProp", elementType="Header")
        etree.SubElement(el, "stringProp", name="Header.name").text = h.get("key", "")
        etree.SubElement(el, "stringProp", name="Header.value").text = h.get("value", "")


def create_assertion(parent):
    a = etree.SubElement(
        parent,
        "ResponseAssertion",
        guiclass="AssertionGui",
        testclass="ResponseAssertion",
        testname="Status Check",
        enabled="true"
    )

    etree.SubElement(a, "stringProp", name="Assertion.test_field").text = "Assertion.response_code"
    etree.SubElement(a, "collectionProp", name="Asserion.test_strings")

    return a


def create_timer(parent, ms):
    t = etree.SubElement(
        parent,
        "ConstantTimer",
        guiclass="ConstantTimerGui",
        testclass="ConstantTimer",
        testname="Think Time",
        enabled="true"
    )

    etree.SubElement(t, "stringProp", name="ConstantTimer.delay").text = str(ms)


# ---------------------------
# MAIN
# ---------------------------

def build_jmx():

    ensure_dir()

    if len(sys.argv) < 2:
        raise Exception("RUN_ID required")

    run_id = sys.argv[1]

    output_file = f"jmx/{run_id}_test_plan.jmx"

    postman = load_json(POSTMAN_FILE)
    config = load_yaml(CONFIG_FILE)

    requests = extract_requests(postman.get("item", []))

    root = etree.Element("jmeterTestPlan", version="1.2", jmeter="5.6.3")
    root_ht = add_hash_tree(root)

    create_test_plan(root_ht)
    test_tree = add_hash_tree(root_ht)

    scenarios = config.get("scenarios", {})

    default_duration = config.get("test", {}).get("default_duration_minutes", 10)
    default_ramp = config.get("test", {}).get("default_ramp_up_seconds", 60)
    think_time = config.get("test", {}).get("think_time_ms", 1000)

    for s_name, s in scenarios.items():

        tg = create_thread_group(
            test_tree,
            s_name,
            s.get("users", 10),
            s.get("ramp_up_seconds", default_ramp),
            s.get("duration_minutes", default_duration)
        )

        tg_tree = add_hash_tree(test_tree)

        for req in requests:

            sampler = create_http_sampler(tg_tree, req)
            sampler_tree = add_hash_tree(tg_tree)

            create_headers(sampler_tree, req["request"])
            add_hash_tree(sampler_tree)

            create_assertion(sampler_tree)
            add_hash_tree(sampler_tree)

            create_timer(sampler_tree, think_time)
            add_hash_tree(sampler_tree)

    etree.ElementTree(root).write(
        output_file,
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8"
    )

    print(output_file)


if __name__ == "__main__":
    build_jmx()