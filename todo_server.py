import os
import sys
import json
import threading
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)

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

# Ensure db directory exists
os.makedirs(DB_DIR, exist_ok=True)

# Initialize db if not exists
if not os.path.exists(DB_FILE):
    if os.path.exists(DEFAULT_DB):
        try:
            with open(DEFAULT_DB, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error copying default db: {e}")
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump({"users": [], "tasks": [], "documents": []}, f)
    else:
        # Create empty structure
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump({"users": [], "tasks": [], "documents": []}, f)

def read_db():
    if not os.path.exists(DB_FILE):
        return {"users": [], "tasks": [], "documents": []}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"users": [], "tasks": [], "documents": []}

def write_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing db: {e}")

@app.route('/')
def serve_index():
    if os.path.exists(os.path.join(STATIC_FOLDER, 'index.html')):
        return send_from_directory(STATIC_FOLDER, 'index.html')
    return "Todo App not found. Please build the frontend first.", 404

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(STATIC_FOLDER, 'assets'), path)

# Define resources
RESOURCES = ['users', 'tasks', 'documents']

def create_endpoints(resource_name):
    @app.route(f'/{resource_name}', methods=['GET'], endpoint=f'get_{resource_name}')
    def get_resource():
        db = read_db()
        return jsonify(db.get(resource_name, []))

    @app.route(f'/{resource_name}', methods=['POST'], endpoint=f'create_{resource_name}')
    def create_resource():
        data = request.json
        db = read_db()
        if resource_name not in db: db[resource_name] = []
        # Generate ID if not present
        if 'id' not in data:
            import time
            data['id'] = str(int(time.time() * 1000))
        
        db[resource_name].append(data)
        write_db(db)
        return jsonify(data), 201

    @app.route(f'/{resource_name}/<id>', methods=['GET'], endpoint=f'get_{resource_name}_id')
    def get_resource_id(id):
        db = read_db()
        item = next((item for item in db.get(resource_name, []) if str(item.get('id')) == str(id)), None)
        if item: return jsonify(item)
        return jsonify({'error': 'Not found'}), 404

    @app.route(f'/{resource_name}/<id>', methods=['PATCH'], endpoint=f'update_{resource_name}')
    def update_resource(id):
        data = request.json
        db = read_db()
        items = db.get(resource_name, [])
        for i, item in enumerate(items):
            if str(item.get('id')) == str(id):
                items[i].update(data)
                write_db(db)
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
            write_db(db)
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
