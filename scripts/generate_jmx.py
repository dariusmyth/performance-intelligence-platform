import json
import yaml
import uuid
from lxml import etree


POSTMAN_FILE = "postman/collection.json"
PERFORMANCE_CONFIG = "config/performance-config.yaml"


def load_postman():
    with open(POSTMAN_FILE) as f:
        return json.load(f)


def load_config():
    with open(PERFORMANCE_CONFIG) as f:
        return yaml.safe_load(f)


def guid():
    return str(uuid.uuid4())


def create_test_plan(root):
    test_plan = etree.SubElement(
        root,
        "TestPlan",
        guiclass="TestPlanGui",
        testclass="TestPlan",
        testname="Performance Intelligence Test Plan",
        enabled="true"
    )

    etree.SubElement(test_plan, "stringProp", name="TestPlan.comments")
    etree.SubElement(test_plan, "boolProp", name="TestPlan.functional_mode").text = "false"
    etree.SubElement(test_plan, "boolProp", name="TestPlan.serialize_threadgroups").text = "false"

    return test_plan


def create_thread_group(parent, name, users, duration, ramp_up):

    tg = etree.SubElement(
        parent,
        "ThreadGroup",
        guiclass="ThreadGroupGui",
        testclass="ThreadGroup",
        testname=name,
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
        "stringProp",
        name="ThreadGroup.duration"
    ).text = str(duration * 60)

    etree.SubElement(
        tg,
        "boolProp",
        name="ThreadGroup.scheduler"
    ).text = "true"

    return tg


def create_transaction_controller(parent, name):

    controller = etree.SubElement(
        parent,
        "TransactionController",
        guiclass="TransactionControllerGui",
        testclass="TransactionController",
        testname=name,
        enabled="true"
    )

    etree.SubElement(
        controller,
        "boolProp",
        name="TransactionController.parent"
    ).text = "true"

    return controller


def create_http_sampler(parent, item):

    request = item["request"]

    method = request["method"]

    url = request["url"]

    if isinstance(url, dict):
        protocol = url.get("protocol", "https")
        host = ".".join(url.get("host", []))
        path = "/".join(url.get("path", []))
    else:
        protocol = "https"
        host = ""
        path = ""

    sampler = etree.SubElement(
        parent,
        "HTTPSamplerProxy",
        guiclass="HttpTestSampleGui",
        testclass="HTTPSamplerProxy",
        testname=item["name"],
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
    ).text = host

    etree.SubElement(
        sampler,
        "stringProp",
        name="HTTPSampler.path"
    ).text = "/" + path

    etree.SubElement(
        sampler,
        "stringProp",
        name="HTTPSampler.method"
    ).text = method

    return sampler


def create_headers(parent, request):

    if "header" not in request:
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

    for header in request["header"]:

        element = etree.SubElement(
            collection,
            "elementProp",
            name=header["key"],
            elementType="Header"
        )

        etree.SubElement(
            element,
            "stringProp",
            name="Header.name"
        ).text = header["key"]

        etree.SubElement(
            element,
            "stringProp",
            name="Header.value"
        ).text = header["value"]


def create_assertions(parent):

    assertion = etree.SubElement(
        parent,
        "ResponseAssertion",
        guiclass="AssertionGui",
        testclass="ResponseAssertion",
        testname="Status Code Assertion",
        enabled="true"
    )

    etree.SubElement(
        assertion,
        "stringProp",
        name="Assertion.test_field"
    ).text = "Assertion.response_code"

    etree.SubElement(
        assertion,
        "intProp",
        name="Assertion.test_type"
    ).text = "8"

    collection = etree.SubElement(
        assertion,
        "collectionProp",
        name="Asserion.test_strings"
    )

    etree.SubElement(
        collection,
        "stringProp",
        name="200"
    ).text = "200"


def create_think_time(parent, milliseconds):

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
    ).text = str(milliseconds)


def build_jmx():

    postman = load_postman()
    config = load_config()

    root = etree.Element(
        "jmeterTestPlan",
        version="1.2",
        properties="5.0",
        jmeter="5.6.3"
    )

    hash_tree = etree.SubElement(root, "hashTree")

    test_plan = create_test_plan(hash_tree)

    test_plan_tree = etree.SubElement(hash_tree, "hashTree")

    scenarios = config["scenarios"]

    think_time = (
        config["test"]
        .get("think_time_ms", 1000)
    )

    for scenario_name, scenario in scenarios.items():

        tg = create_thread_group(
            test_plan_tree,
            scenario_name,
            scenario["users"],
            scenario["duration_minutes"],
            scenario.get(
                "ramp_up_seconds",
                config["test"]
                .get(
                    "default_ramp_up_seconds",
                    60
                )
            )
        )

        tg_tree = etree.SubElement(
            test_plan_tree,
            "hashTree"
        )

        controller = create_transaction_controller(
            tg_tree,
            scenario_name
        )

        controller_tree = etree.SubElement(
            tg_tree,
            "hashTree"
        )

        for item in postman["item"]:

            sampler = create_http_sampler(
                controller_tree,
                item
            )

            sampler_tree = etree.SubElement(
                controller_tree,
                "hashTree"
            )

            create_headers(
                sampler_tree,
                item["request"]
            )

            create_assertions(
                sampler_tree
            )

            create_think_time(
                sampler_tree,
                think_time
            )

    tree = etree.ElementTree(root)

    tree.write(
        "jmx/test_plan.jmx",
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8"
    )

    print(
        "Generated jmx/test_plan.jmx"
    )


if __name__ == "__main__":
    build_jmx()