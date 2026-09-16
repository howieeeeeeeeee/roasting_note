"""Exercise label canvas typography without a browser."""
import shutil
import subprocess
from pathlib import Path


def test_label_font_size_renderer():
    node = shutil.which('node')
    assert node
    result = subprocess.run([node, 'tests/label_font_size_check.cjs'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_label_font_size_controls_are_grouped_sliders():
    template = Path('templates/beans_detail.html').read_text()
    css = Path('static/css/screens/label-creator.css').read_text()

    assert 'fieldset class="label-size-panel label-form-row-full"' in template
    assert 'type="range"' in template
    assert 'oninput="updateLabelSize(this)"' in template
    assert 'Number(input.value) !== 100' in template
    assert '.label-size-control {' in css
    assert 'white-space: nowrap;' in css
