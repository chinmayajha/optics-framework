"""Desktop apps through Appium and appium-xa11y-driver, on the Host that ``OPTICS_E2E_XA11Y_URL`` names.

    OPTICS_E2E_XA11Y_URL=http://127.0.0.1:4723 OPTICS_E2E_XA11Y_PLATFORM=Linux pytest tests/integration/desktop
"""

import json
import urllib.request

import pytest

from optics_framework import Optics
from tests.integration.desktop.support import (
    APPIUM_URL,
    DESKTOPS,
    PLATFORM,
    driver_config,
)


@pytest.fixture(scope="session")
def host():
    if not APPIUM_URL:
        pytest.skip("Set OPTICS_E2E_XA11Y_URL to an Appium server with appium-xa11y-driver")
    try:
        with urllib.request.urlopen(f"{APPIUM_URL}/status", timeout=3) as response:  # nosec
            json.load(response)
    except OSError as e:
        pytest.fail(f"No Appium server at {APPIUM_URL}: {e}")
    return APPIUM_URL


@pytest.fixture(scope="session")
def desktop():
    return DESKTOPS[PLATFORM]


@pytest.fixture(autouse=True)
def no_restored_documents(request):
    """TextEdit reopens the unsaved documents of its last run, so each Mac test starts with every window emptied and closed."""
    if PLATFORM != "Mac" or "host" not in request.fixturenames:
        return
    host, desktop = request.getfixturevalue("host"), request.getfixturevalue("desktop")
    optics = Optics()
    optics.setup(config=driver_config(host, desktop.editor))
    optics.launch_app()
    try:
        for _ in range(5):
            if not optics.validate_screen(desktop.field, "1"):
                break
            optics.press_keycode(desktop.select_all)
            optics.enter_text_using_keyboard("<backspace>")
            optics.press_keycode("cmd+w")
    finally:
        optics.force_terminate_app(desktop.editor)
        optics.quit()
