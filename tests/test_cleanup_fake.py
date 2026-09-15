"""Bulk-cleanup UI testing must use isolated, non-mutating responses."""

import json

import pytest
from flask import Flask

from tests.e2e import cleanup_fake


def test_cleanup_fake_retries_without_running_real_cleanup(tmp_path, monkeypatch):
    root = tmp_path / 'artifacts' / 'run'
    root.mkdir(parents=True)
    monkeypatch.setattr(cleanup_fake, 'ARTIFACTS_ROOT', root.parent)
    app = Flask(__name__)
    app.config.update(E2E_MODE=True, LOCAL_DB_NAME='roastlogger_e2e', E2E_ARTIFACT_ROOT=root)

    def forbidden():
        raise AssertionError('Real cleanup must never execute')

    routes = [('api_clean_test_data', '/api/db/clean-test-data'),
              ('api_clean_local_db', '/api/db/clean-local')]
    for endpoint, url in routes:
        app.add_url_rule(url, endpoint, forbidden, methods=['POST'])
    cleanup_fake.install_cleanup_fake(app)
    client = app.test_client()
    for _, url in routes:
        assert client.post(url).status_code == 503
        response = client.post(url)
        assert response.status_code == 200 and response.json['success']
    events = [json.loads(line) for line in (root / 'cleanup-fake-events.jsonl').read_text().splitlines()]
    assert len(events) == 4
    assert all(event['database_access'] is False for event in events)


@pytest.mark.parametrize('unsafe', [
    {'E2E_MODE': False}, {'LOCAL_DB_NAME': 'roastlogger'}, {'E2E_ARTIFACT_ROOT': '/tmp'},
])
def test_cleanup_fake_rejects_unsafe_runtime(tmp_path, monkeypatch, unsafe):
    monkeypatch.setattr(cleanup_fake, 'ARTIFACTS_ROOT', tmp_path / 'artifacts')
    app = Flask(__name__)
    app.config.update(E2E_MODE=True, LOCAL_DB_NAME='roastlogger_e2e',
                      E2E_ARTIFACT_ROOT=tmp_path / 'artifacts' / 'run')
    app.config.update(unsafe)
    with pytest.raises(ValueError, match='isolated E2E'):
        cleanup_fake.install_cleanup_fake(app)
