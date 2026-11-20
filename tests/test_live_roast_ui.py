"""Exercise the live session and both chart renderers with Node."""
import shutil
import subprocess

import pytest


@pytest.mark.parametrize("script", ["live_roast_ui_check.mjs", "roast_chart_markers_check.mjs"])
def test_live_session_behavior(script):
    node = shutil.which('node')
    assert node, 'Node is required for the live-roast JavaScript regression check'
    result = subprocess.run([node, '--experimental-default-type=module',
                             f'tests/{script}'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
