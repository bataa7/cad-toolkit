"""
本地测试服务器
用于测试消息推送和更新系统
"""
from flask import Flask, jsonify, send_file
import json
import os

app = Flask(__name__)

# 启用CORS（跨域资源共享）
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response


@app.route('/')
def index():
    """首页"""
    return """
    <html>
    <head>
        <title>CAD工具包测试服务器</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .endpoint { 
                background: #f5f5f5; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px;
            }
            .endpoint a { 
                color: #1976d2; 
                text-decoration: none;
                font-weight: bold;
            }
            .endpoint a:hover { text-decoration: underline; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🚀 CAD工具包测试服务器</h1>
        <p class="status">✅ 服务器运行中</p>
        
        <h2>可用的API端点：</h2>
        
        <div class="endpoint">
            <strong>通知API：</strong><br>
            <a href="/api/notifications">/api/notifications</a><br>
            <small>获取通知列表</small>
        </div>
        
        <div class="endpoint">
            <strong>更新检查API：</strong><br>
            <a href="/api/check_update">/api/check_update</a><br>
            <small>检查软件更新</small>
        </div>
        
        <div class="endpoint">
            <strong>版本信息API：</strong><br>
            <a href="/api/version">/api/version</a><br>
            <small>获取当前服务器版本信息</small>
        </div>
        
        <h2>配置说明：</h2>
        <p>在 <code>system_config.py</code> 中设置：</p>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px;">
NOTIFICATION_CONFIG = {
    "api_url": "http://localhost:5000/api/notifications",
    "enabled": True,
}

UPDATE_CONFIG = {
    "api_url": "http://localhost:5000/api/check_update",
    "enabled": True,
}
        </pre>
    </body>
    </html>
    """


@app.route('/api/notifications')
def get_notifications():
    """获取通知列表"""
    try:
        # 读取测试通知数据
        if os.path.exists('test_notifications.json'):
            with open('test_notifications.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # 默认通知
            data = {
                "notifications": [
                    {
                        "id": "notif_default",
                        "title": "测试通知",
                        "content": "这是一条测试通知，服务器运行正常！",
                        "level": "info",
                        "date": "2026-03-05"
                    }
                ]
            }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/check_update')
def check_update():
    """检查更新"""
    try:
        # 读取测试更新信息
        if os.path.exists('test_update_info.json'):
            with open('test_update_info.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # 默认更新信息（无更新）
            data = {
                "version": "1.0.0",
                "message": "当前已是最新版本"
            }
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/version')
def get_version():
    """获取版本信息"""
    return jsonify({
        "server_version": "1.0.0",
        "api_version": "1.0",
        "status": "running",
        "endpoints": [
            "/api/notifications",
            "/api/check_update",
            "/api/version"
        ]
    })


@app.route('/api/stats')
def get_stats():
    """获取统计信息（可选）"""
    return jsonify({
        "total_notifications": 5,
        "latest_version": "1.1.0",
        "update_available": True
    })


# 文件下载端点（用于测试更新下载）
@app.route('/downloads/<path:filename>')
def download_file(filename):
    """下载文件"""
    file_path = os.path.join('downloads', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({"error": "File not found"}), 404


def main():
    """启动服务器"""
    print("=" * 60)
    print("🚀 CAD工具包测试服务器")
    print("=" * 60)
    print()
    print("服务器地址: http://localhost:5000")
    print()
    print("可用端点:")
    print("  • 通知API:    http://localhost:5000/api/notifications")
    print("  • 更新API:    http://localhost:5000/api/check_update")
    print("  • 版本信息:   http://localhost:5000/api/version")
    print()
    print("配置说明:")
    print("  在 system_config.py 中设置 api_url 为上述地址")
    print()
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    # 检查测试数据文件
    if not os.path.exists('test_notifications.json'):
        print("⚠️  警告: test_notifications.json 不存在，将使用默认数据")
    else:
        print("✅ 找到 test_notifications.json")
    
    if not os.path.exists('test_update_info.json'):
        print("⚠️  警告: test_update_info.json 不存在，将使用默认数据")
    else:
        print("✅ 找到 test_update_info.json")
    
    print()
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
