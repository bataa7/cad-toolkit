import os
import sys
import json
import threading
import tempfile
import uuid
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)

RESOURCES = ['users', 'tasks', 'documents']
DB_LOCK = threading.RLock()

# Determine paths
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    BASE_DIR = sys._MEIPASS
    STATIC_FOLDER = os.path.join(BASE_DIR, 'todo_dist')
    DEFAULT_DB = os.path.join(BASE_DIR, 'db.json')
else:
    # Running from source
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_FOLDER = os.path.join(BASE_DIR, '共享平台', 'dist')
    DEFAULT_DB = os.path.join(BASE_DIR, '共享平台', 'db.json')

# Use user's home directory for persistent storage
DB_DIR = os.path.join(os.path.expanduser('~'), '.cad_toolkit')
DB_FILE = os.path.join(DB_DIR, 'db.json')
DB_BACKUP_FILE = os.path.join(DB_DIR, 'db.backup.json')

# Ensure db directory exists
os.makedirs(DB_DIR, exist_ok=True)


def _empty_db():
    return {resource: [] for resource in RESOURCES}


def _normalize_db(data):
    normalized = _empty_db()
    if isinstance(data, dict):
        for resource in RESOURCES:
            value = data.get(resource, [])
            normalized[resource] = value if isinstance(value, list) else []
        for key, value in data.items():
            if key not in normalized:
                normalized[key] = value
    return normalized


def _read_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return _normalize_db(json.load(f))


def _atomic_write_json(path, data):
    directory = os.path.dirname(path) or '.'
    os.makedirs(directory, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix='cad_db_', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _load_default_db():
    if os.path.exists(DEFAULT_DB):
        try:
            return _read_json_file(DEFAULT_DB)
        except Exception as e:
            print(f"Error loading default db: {e}")
    return _empty_db()


def read_db():
    with DB_LOCK:
        for path, restore_main in ((DB_FILE, False), (DB_BACKUP_FILE, True)):
            if not os.path.exists(path):
                continue
            try:
                data = _read_json_file(path)
                if restore_main:
                    _atomic_write_json(DB_FILE, data)
                return data
            except Exception as e:
                print(f"Error reading db '{path}': {e}")

        fallback = _load_default_db()
        _atomic_write_json(DB_FILE, fallback)
        _atomic_write_json(DB_BACKUP_FILE, fallback)
        return fallback


def write_db(data):
    payload = _normalize_db(data)
    with DB_LOCK:
        try:
            _atomic_write_json(DB_FILE, payload)
            _atomic_write_json(DB_BACKUP_FILE, payload)
            return True
        except Exception as e:
            print(f"Error writing db: {e}")
            return False


def _ensure_db_exists():
    with DB_LOCK:
        if os.path.exists(DB_FILE) and os.path.exists(DB_BACKUP_FILE):
            return
        initial_data = _load_default_db()
        if not os.path.exists(DB_FILE):
            _atomic_write_json(DB_FILE, initial_data)
        if not os.path.exists(DB_BACKUP_FILE):
            _atomic_write_json(DB_BACKUP_FILE, initial_data)


def _get_request_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return dict(data)


def _generate_resource_id(existing_ids):
    while True:
        candidate = uuid.uuid4().hex
        if candidate not in existing_ids:
            return candidate


_ensure_db_exists()


@app.route('/')
def serve_index():
    if os.path.exists(os.path.join(STATIC_FOLDER, 'index.html')):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    return 'Todo App not found. Please build the frontend first.', 404


@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(STATIC_FOLDER, 'assets'), path)


def create_endpoints(resource_name):
    @app.route(f'/{resource_name}', methods=['GET'], endpoint=f'get_{resource_name}')
    def get_resource():
        db = read_db()
        return jsonify(db.get(resource_name, []))

    @app.route(f'/{resource_name}', methods=['POST'], endpoint=f'create_{resource_name}')
    def create_resource():
        data = _get_request_payload()
        if data is None:
            return jsonify({'error': 'Request body must be a JSON object'}), 400

        db = read_db()
        if resource_name not in db or not isinstance(db[resource_name], list):
            db[resource_name] = []

        existing_ids = {
            str(item.get('id'))
            for item in db[resource_name]
            if isinstance(item, dict) and item.get('id') is not None
        }
        requested_id = str(data.get('id', '')).strip()
        data['id'] = requested_id if requested_id and requested_id not in existing_ids else _generate_resource_id(existing_ids)

        db[resource_name].append(data)
        if not write_db(db):
            return jsonify({'error': 'Failed to persist data'}), 500
        return jsonify(data), 201

    @app.route(f'/{resource_name}/<id>', methods=['GET'], endpoint=f'get_{resource_name}_id')
    def get_resource_id(id):
        db = read_db()
        item = next((item for item in db.get(resource_name, []) if str(item.get('id')) == str(id)), None)
        if item:
            return jsonify(item)
        return jsonify({'error': 'Not found'}), 404

    @app.route(f'/{resource_name}/<id>', methods=['PATCH'], endpoint=f'update_{resource_name}')
    def update_resource(id):
        data = _get_request_payload()
        if data is None:
            return jsonify({'error': 'Request body must be a JSON object'}), 400

        data.pop('id', None)
        db = read_db()
        items = db.get(resource_name, [])
        for i, item in enumerate(items):
            if str(item.get('id')) == str(id):
                items[i].update(data)
                if not write_db(db):
                    return jsonify({'error': 'Failed to persist data'}), 500
                return jsonify(items[i])
        return jsonify({'error': 'Not found'}), 404

    @app.route(f'/{resource_name}/<id>', methods=['DELETE'], endpoint=f'delete_{resource_name}')
    def delete_resource(id):
        db = read_db()
        items = db.get(resource_name, [])
        initial_len = len(items)
        new_items = [item for item in items if str(item.get('id')) != str(id)]
        if len(new_items) < initial_len:
            db[resource_name] = new_items
            if not write_db(db):
                return jsonify({'error': 'Failed to persist data'}), 500
            return jsonify({}), 200
        return jsonify({'error': 'Not found'}), 404


# Register endpoints
for res in RESOURCES:
    create_endpoints(res)


def run_server(port=5173):
    # Disable flask banner
    import logging

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Failed to start server: {e}")


if __name__ == '__main__':
    run_server()
