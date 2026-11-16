"""Container integration checks; run with: python3 tests/smoke.py IMAGE."""

from contextlib import contextmanager
from pathlib import Path
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid


IMAGE = sys.argv[1] if len(sys.argv) > 1 else "docsify-server:smoke-test"
TEMPLATE = Path(__file__).resolve().parents[1] / "template"
VERSION = sys.argv[2] if len(sys.argv) > 2 else None
CLI_VERSION = sys.argv[3] if len(sys.argv) > 3 else None
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True, timeout=60).strip()


def address(container):
    state = json.loads(docker("inspect", container))[0]
    port = state["NetworkSettings"]["Ports"]["3000/tcp"][0]["HostPort"]
    return f"http://127.0.0.1:{port}"


@contextmanager
def site(seed=None, *, readonly=False, auto_init=True):
    volume = f"docsify-test-{uuid.uuid4().hex}"
    container = None
    docker("volume", "create", volume)
    try:
        mount = f"type=volume,src={volume},dst=/docs"
        if seed:
            docker("run", "--rm", "--mount", mount, "--entrypoint", "sh", IMAGE, "-ec", seed)
        if readonly:
            mount += ",readonly"
        container = docker(
            "run", "-d", "--mount", mount, "-p", "127.0.0.1::3000",
            "-e", f"DOCSIFY_AUTO_INIT={str(auto_init).lower()}", IMAGE,
        )
        yield container, address(container)
    except BaseException:
        if container:
            print(docker("logs", container), file=sys.stderr)
        raise
    finally:
        if container:
            docker("rm", "-f", container)
        docker("volume", "rm", volume)


def fetch(base, path="/", *, wait=False):
    deadline = time.monotonic() + (20 if wait else 0)
    while True:
        try:
            with HTTP.open(base + path, timeout=2) as response:
                return response.read()
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.5)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


with site() as (container, base):
    index = fetch(base, wait=True)
    check(index == (TEMPLATE / "index.html").read_bytes(), "Starter index differs")
    check(fetch(base, "/README.md") == (TEMPLATE / "README.md").read_bytes(), "Starter README differs")
    for asset in re.findall(r'(?:src|href)="(assets/[^"]+)"', index.decode()):
        check(fetch(base, "/" + asset) == (TEMPLATE / asset).read_bytes(), f"Missing or changed asset: {asset}")
    actual_version = docker("exec", container, "cat", "/opt/docsify-server/VERSION")
    check(re.fullmatch(r"\d+\.\d+\.\d+", actual_version), "Image version was not resolved")
    if VERSION:
        check(actual_version == VERSION, "Image version differs from CI")
    actual_cli = docker("exec", container, "cat", "/opt/docsify-server/DOCSIFY_CLI_VERSION")
    check(re.fullmatch(r"\d+\.\d+\.\d+", actual_cli), "CLI version was not resolved")
    if CLI_VERSION:
        check(actual_cli == CLI_VERSION, "Installed CLI differs from the resolved CI version")
    print("PASS: empty volume initializes and all offline assets are reachable", flush=True)

with site("mkdir -p /docs/assets; printf 'user docs' > /docs/README.md; "
          "printf '/* user theme */' > /docs/assets/vue.css") as (container, base):
    fetch(base, wait=True)
    check(fetch(base, "/README.md") == b"user docs", "User README overwritten")
    check(fetch(base, "/assets/vue.css") == b"/* user theme */", "User theme overwritten")
    check(fetch(base, "/assets/docsify.min.js") == (TEMPLATE / "assets/docsify.min.js").read_bytes(),
          "Existing assets directory was not completed")
    docker("restart", container)
    base = address(container)
    fetch(base, wait=True)
    check(fetch(base, "/README.md") == b"user docs", "Restart overwrote user README")
    check(fetch(base, "/assets/vue.css") == b"/* user theme */", "Restart overwrote user theme")
    print("PASS: partial assets are completed and user files survive restart", flush=True)

for readonly in (False, True):
    with site("printf '<h1>custom site</h1>' > /docs/index.html", readonly=readonly) as (container, base):
        check(fetch(base, wait=True) == b"<h1>custom site</h1>", "Custom index overwritten")
        check(docker("exec", container, "ls", "-A", "/docs") == "index.html", "Custom site modified")
        print(f"PASS: custom site is served unchanged (readonly={readonly})", flush=True)

with site(auto_init=False) as (container, _):
    subprocess.run(["docker", "wait", container], check=True, timeout=20, capture_output=True)
    check("No docs found" in docker("logs", container), "Expected missing-docs diagnostic")
    # Stopped containers can still be copied from; inspect the shared volume with a fresh helper.
    state = json.loads(docker("inspect", container))[0]
    volume = state["Mounts"][0]["Name"]
    check(docker("run", "--rm", "--mount", f"type=volume,src={volume},dst=/docs,readonly",
                 "--entrypoint", "ls", IMAGE, "-A", "/docs") == "", "Disabled init wrote files")
    print("PASS: disabled initialization leaves an empty volume untouched", flush=True)
