"""Drives Mousepad on a Linux Host through Appium and appium-xa11y-driver.

    OPTICS_E2E_XA11Y_URL=http://127.0.0.1:4723 pytest tests/integration/test_appium_desktop.py
"""

import asyncio
import json
import os
import urllib.error
import urllib.request

import pytest

from optics_framework.helper.execute import run_project
from optics_framework.helper import mcp_server

pytestmark = pytest.mark.black_box

APPIUM_URL = os.environ.get("OPTICS_E2E_XA11Y_URL", "")
EDITOR = "//text_area"

CONFIG = """\
driver_sources:
  - appium:
      enabled: true
      url: "{url}"
      capabilities:
        platformName: Linux
        automationName: Xa11y
        app: mousepad
elements_sources:
  - appium_find_element:
      enabled: true
  - appium_page_source:
      enabled: true
  - appium_screenshot:
      enabled: true
"""


@pytest.fixture(scope="module")
def host():
    if not APPIUM_URL:
        pytest.skip("Set OPTICS_E2E_XA11Y_URL to an Appium server with appium-xa11y-driver on a Linux Host")
    try:
        with urllib.request.urlopen(f"{APPIUM_URL}/status", timeout=3) as response:  # nosec
            json.load(response)
    except OSError as e:
        pytest.skip(f"No Appium server at {APPIUM_URL}: {e}")
    return APPIUM_URL


def _project(tmp_path, url, steps):
    files = {
        "config.yaml": CONFIG.format(url=url),
        "test_cases/test_cases.csv": "test_case,test_step\nEdit,Edit\n",
        "modules/modules.csv": "\n".join(["module_name,module_step,param_1,param_2,param_3",
                                          "Edit,Launch App", *(f"Edit,{step}" for step in steps)]) + "\n",
    }
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return str(tmp_path)


def _junit(tmp_path):
    return (tmp_path / "execution_output" / "junit_output.xml").read_text(encoding="utf-8")


def test_types_into_the_editor_and_edits_with_chords(tmp_path, host):
    project = _project(tmp_path, host, [
        f"Enter Text,{EDITOR},hello",
        "Enter Text Direct,!",
        f"Assert Text,{EDITOR},hello!",
        "Press Keycode,ctrl+a",
        "Enter Text Using Keyboard,<backspace>",
        f"Enter Text,{EDITOR},again",
        f"Enter Text,{EDITOR},<backspace>",
        f"Assert Text,{EDITOR},agai",
    ])

    assert run_project(project, use_printer=False) is True, _junit(tmp_path)


def test_scrolls_the_window_with_the_wheel(tmp_path, host):
    project = _project(tmp_path, host, [
        "Scroll,down",
        "Scroll,up",
        f"Assert Presence,{EDITOR},5",
    ])

    assert run_project(project, use_printer=False) is True, _junit(tmp_path)


def _attach(url, app_name):
    caps = {"platformName": "Linux", "appium:automationName": "Xa11y", "appium:appName": app_name, "appium:launchTimeout": 500}
    body = json.dumps({"capabilities": {"alwaysMatch": caps}}).encode()
    request = urllib.request.Request(f"{url}/session", body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # nosec
            sid = json.load(response)["value"]["sessionId"]
    except urllib.error.HTTPError:
        return False
    urllib.request.urlopen(urllib.request.Request(f"{url}/session/{sid}", method="DELETE"), timeout=30).close()  # nosec
    return True


def test_screen_elements_list_the_editor_as_an_input(tmp_path, host):
    project = _project(tmp_path, host, ["Get Interactive Elements,compact=true"])

    assert run_project(project, use_printer=False) is True, _junit(tmp_path)
    elements = json.loads((tmp_path / "execution_output" / "interactable_elements.json").read_text(encoding="utf-8"))
    assert any("input" in element["act"] for element in elements), elements


def test_an_agent_types_presses_chords_and_switches_apps_over_mcp(host):
    fastmcp = pytest.importorskip("fastmcp")

    async def journey():
        async with fastmcp.Client(mcp_server.build_server()) as client:
            async def call(tool, **args):
                result = await client.call_tool(tool, args, raise_on_error=False)
                text = "\n".join(c.text for c in result.content if getattr(c, "text", None))
                assert not result.is_error, text
                return result.structured_content or {}, text

            caps = {"platformName": "Linux", "automationName": "Xa11y"}
            started, _ = await call("start_session", driver="appium", app="mousepad", url=host, capabilities=caps)
            sid = started["session_id"]
            try:
                _, screen = await call("observe", session_id=sid)
                editor = next(line.split()[0] for line in screen.splitlines() if " text_area " in line)
                typed, _ = await call("type_text", session_id=sid, target=editor, text="from an agent",
                                      expect_present=["from an agent"])
                await call("press_key", session_id=sid, key="ctrl+a")
                cleared, _ = await call("press_key", session_id=sid, key="BackSpace", expect_absent=["from an agent"])
                await call("scroll", session_id=sid, direction="down")
                other, _ = await call("launch_app", session_id=sid, app="gnome-calculator",
                                      expect_present=["Calculate Result"])
                back, _ = await call("launch_app", session_id=sid, app="mousepad", expect_absent=["Calculate Result"])
                await call("run_keyword", session_id=sid, keyword="force_terminate_app",
                           params={"app_name": "gnome-calculator"})
                assert not _attach(host, "gnome-calculator"), "gnome-calculator still runs"
                return [step["verified"] for step in (typed, cleared, other, back)]
            finally:
                await call("terminate_session", session_id=sid)

    assert asyncio.run(journey()) == ["pass"] * 4


def test_an_agent_swipes_a_desktop_window_with_the_wheel(host):
    fastmcp = pytest.importorskip("fastmcp")

    async def swipe():
        async with fastmcp.Client(mcp_server.build_server()) as client:
            async def call(tool, **args):
                result = await client.call_tool(tool, args, raise_on_error=False)
                text = "\n".join(c.text for c in result.content if getattr(c, "text", None))
                assert not result.is_error, text
                return text

            def scrolled(screen):
                return float(next(line for line in screen.splitlines() if " scroll_bar " in line).split('"')[1])

            caps = {"platformName": "Linux", "automationName": "Xa11y"}
            started = await client.call_tool("start_session", {"driver": "appium", "app": "mousepad", "url": host,
                                                                "capabilities": caps})
            sid = started.structured_content["session_id"]
            try:
                screen = await call("observe", session_id=sid)
                editor = next(line.split()[0] for line in screen.splitlines() if " text_area " in line)
                await call("type_text", session_id=sid, target=editor, text="\n".join(f"line {i}" for i in range(120)))
                await call("press_key", session_id=sid, key="ctrl+Home")
                top = scrolled(await call("observe", session_id=sid))
                await call("run_keyword", session_id=sid, keyword="swipe_by_percentage",
                           params={"percent_x": "50", "percent_y": "50", "direction": "up", "swipe_length": "30"})
                down = scrolled(await call("observe", session_id=sid))
                await call("run_keyword", session_id=sid, keyword="swipe_from_element",
                           params={"element": "//text_area", "direction": "down", "swipe_length": "200"})
                return top, down, scrolled(await call("observe", session_id=sid))
            finally:
                await call("terminate_session", session_id=sid)

    top, down, back = asyncio.run(swipe())
    assert top < back < down, (top, down, back)


def test_an_agent_cannot_start_a_desktop_session_without_an_app(host):
    fastmcp = pytest.importorskip("fastmcp")

    async def start():
        async with fastmcp.Client(mcp_server.build_server()) as client:
            caps = {"platformName": "Linux", "automationName": "Xa11y"}
            result = await client.call_tool("start_session", {"driver": "appium", "url": host, "capabilities": caps},
                                            raise_on_error=False)
            return "\n".join(c.text for c in result.content if getattr(c, "text", None))

    assert "appName" in asyncio.run(start())
