"""Static assertions on the Kubernetes manifests.

These guard the hardening posture in-repo: a regression that weakens the pod
securityContext, drops a probe, or unpins the container UID fails CI before it
can ever reach a cluster. They parse the YAML directly (no cluster required).
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE = REPO_ROOT / "k8s" / "base"


def _load(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def deployment() -> dict:
    return _load(BASE / "deployment.yaml")


def test_pod_runs_as_non_root_uid_10001(deployment: dict) -> None:
    pod_sc = deployment["spec"]["template"]["spec"]["securityContext"]
    assert pod_sc["runAsNonRoot"] is True
    assert pod_sc["runAsUser"] == 10001  # must match Dockerfile USER 10001
    assert pod_sc["seccompProfile"]["type"] == "RuntimeDefault"


def test_container_security_context_hardened(deployment: dict) -> None:
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    sc = container["securityContext"]
    assert sc["allowPrivilegeEscalation"] is False
    assert sc["readOnlyRootFilesystem"] is True
    assert sc["capabilities"]["drop"] == ["ALL"]


def test_dockerfile_uid_matches_deployment(deployment: dict) -> None:
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    pod_uid = deployment["spec"]["template"]["spec"]["securityContext"]["runAsUser"]
    assert f"--uid {pod_uid}" in dockerfile
    assert f"USER {pod_uid}" in dockerfile


def test_all_three_probes_present(deployment: dict) -> None:
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["startupProbe"]["httpGet"]["path"] == "/health"
    assert container["livenessProbe"]["httpGet"]["path"] == "/health"
    assert container["readinessProbe"]["httpGet"]["path"] == "/ready"


def test_resources_requests_and_limits_set(deployment: dict) -> None:
    resources = deployment["spec"]["template"]["spec"]["containers"][0]["resources"]
    assert resources["requests"]["cpu"] and resources["requests"]["memory"]
    assert resources["limits"]["cpu"] and resources["limits"]["memory"]


def test_deployment_uses_dedicated_service_account(deployment: dict) -> None:
    spec = deployment["spec"]["template"]["spec"]
    assert spec["serviceAccountName"] == "d4-sample"
    # Token automounting is disabled — the app calls no Kubernetes API.
    assert spec["automountServiceAccountToken"] is False


def test_container_port_is_8000(deployment: dict) -> None:
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    assert container["ports"][0]["containerPort"] == 8000
