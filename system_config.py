"""
系统配置文件
包含消息推送和更新系统的配置
"""

# 应用版本
APP_VERSION = "3.8"

# 消息推送配置
NOTIFICATION_CONFIG = {
    # API地址 - 从服务器获取通知列表
    "api_url": [
        "https://raw.githubusercontent.com/bataa7/cad-toolkit/main/notifications.json",
        "https://cdn.jsdelivr.net/gh/bataa7/cad-toolkit@main/notifications.json",
    ],
    
    # 缓存文件路径
    "cache_file": "notifications_cache.json",
    
    # 检查间隔（秒）
    "check_interval": 300,  # 5分钟
    
    # 是否启用
    "enabled": True,  # 启用通知功能
    "ssl_verify": False,
    "ssl_ca_bundle": "",
}

# 更新系统配置
UPDATE_CONFIG = {
    # API地址 - 检查更新
    "api_url": [
        "https://raw.githubusercontent.com/bataa7/cad-toolkit/main/version.json",
        "https://cdn.jsdelivr.net/gh/bataa7/cad-toolkit@main/version.json",
    ],
    
    # 配置文件路径
    "config_file": "update_config.json",
    
    # 启动时检查更新
    "check_on_startup": False,  # 默认禁用，避免启动时网络请求
    
    # 自动检查间隔（秒）
    "auto_check_interval": 3600,  # 1小时
    
    # 是否启用
    "enabled": True,
    "ssl_verify": False,
    "ssl_ca_bundle": "",
}

# 开发模式配置（用于测试）
DEV_MODE = {
    # 使用本地测试数据
    "use_local_data": False,

    
    # 本地通知数据文件
    "local_notifications": "test_notifications.json",
    
    # 本地更新数据文件
    "local_update_info": "test_update_info.json",
}
