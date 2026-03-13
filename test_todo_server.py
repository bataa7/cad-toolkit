import importlib
import json

import pytest


@pytest.fixture
def todo_server_module(monkeypatch, tmp_path):
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('USERPROFILE', str(tmp_path))

    import todo_server

    module = importlib.reload(todo_server)
    module.app.config['TESTING'] = True
    return module


def test_create_resource_rejects_non_object_payload(todo_server_module):
    client = todo_server_module.app.test_client()

    response = client.post('/tasks', json=['not', 'an', 'object'])

    assert response.status_code == 400
    assert response.get_json()['error'] == 'Request body must be a JSON object'


def test_create_resource_regenerates_duplicate_ids(todo_server_module):
    client = todo_server_module.app.test_client()

    first = client.post('/tasks', json={'id': 'fixed-id', 'title': 'first'})
    second = client.post('/tasks', json={'id': 'fixed-id', 'title': 'second'})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.get_json()['id'] == 'fixed-id'
    assert second.get_json()['id'] != 'fixed-id'
    assert second.get_json()['id'] != first.get_json()['id']


def test_update_resource_keeps_existing_id(todo_server_module):
    client = todo_server_module.app.test_client()

    created = client.post('/users', json={'name': 'Alice'}).get_json()
    updated = client.patch(
        f"/users/{created['id']}",
        json={'id': 'new-id', 'name': 'Alice Updated'},
    )

    assert updated.status_code == 200
    payload = updated.get_json()
    assert payload['id'] == created['id']
    assert payload['name'] == 'Alice Updated'


def test_read_db_recovers_from_backup(todo_server_module):
    original = {
        'users': [{'id': 'u1', 'name': 'Backup User'}],
        'tasks': [],
        'documents': [],
    }
    assert todo_server_module.write_db(original) is True

    with open(todo_server_module.DB_FILE, 'w', encoding='utf-8') as f:
        f.write('{broken json')

    recovered = todo_server_module.read_db()

    assert recovered['users'][0]['id'] == 'u1'
    with open(todo_server_module.DB_FILE, 'r', encoding='utf-8') as f:
        restored = json.load(f)
    assert restored['users'][0]['name'] == 'Backup User'
