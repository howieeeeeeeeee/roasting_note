"""Exercise label canvas typography without a browser."""
import shutil
import subprocess


def test_label_font_size_renderer():
    node = shutil.which('node')
    assert node
    result = subprocess.run([node, 'tests/label_font_size_check.cjs'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
