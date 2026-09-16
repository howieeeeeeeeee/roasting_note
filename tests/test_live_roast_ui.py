"""Execute the live session against a small DOM/clock fake, without a browser dependency."""
import shutil
import subprocess


def test_live_session_behavior():
    node = shutil.which('node')
    assert node, 'Node is required for the live-roast JavaScript regression check'
    result = subprocess.run([node, '--experimental-default-type=module',
                             'tests/live_roast_ui_check.mjs'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
