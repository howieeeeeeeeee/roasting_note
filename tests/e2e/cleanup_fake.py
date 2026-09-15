"""Test-entrypoint-only cleanup responses; never delete or access database data."""

import json
from collections import Counter
from pathlib import Path

from flask import jsonify, request

ARTIFACTS_ROOT = Path(__file__).parent / 'artifacts'


def install_cleanup_fake(app):
    root = Path(app.config['E2E_ARTIFACT_ROOT']).resolve()
    if (not app.config.get('E2E_MODE')
            or app.config.get('LOCAL_DB_NAME') != 'roastlogger_e2e'
            or not root.is_relative_to(ARTIFACTS_ROOT.resolve())
            or root == ARTIFACTS_ROOT.resolve()):
        raise ValueError('Cleanup fake requires isolated E2E mode and a run artifact directory')
    attempts = Counter()

    def response():
        attempts[request.path] += 1
        attempt = attempts[request.path]
        with (root / 'cleanup-fake-events.jsonl').open('a') as output:
            output.write(json.dumps({'path': request.path, 'attempt': attempt,
                                     'database_access': False}) + '\n')
        if attempt == 1:
            return jsonify(success=False, error='Simulated cleanup failure; retry is safe.'), 503
        return jsonify(success=True, beans_deleted=2, roasts_deleted=3, temp_logs_deleted=0)

    app.view_functions['api_clean_test_data'] = response
    app.view_functions['api_clean_local_db'] = response
