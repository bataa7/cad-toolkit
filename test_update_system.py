"""
更新系统测试脚本
用于验证更新检查和通知功能是否正常工作
"""
import sys
import json
try:
    import certifi
except Exception:
    certifi = None
from update_manager import UpdateChecker, NotificationFetcher, CURRENT_VERSION, GITHUB_OWNER, GITHUB_REPO
from system_config import NOTIFICATION_CONFIG, UPDATE_CONFIG


def _normalize_urls(urls):
    if isinstance(urls, (list, tuple)):
        return [u for u in urls if u]
    if isinstance(urls, str) and urls:
        return [urls]
    return []


def _resolve_verify(verify_value, ca_bundle):
    if isinstance(ca_bundle, str) and ca_bundle:
        return ca_bundle
    if verify_value is False:
        return False
    if verify_value is True and certifi:
        return certifi.where()
    return True


def test_version_comparison():
    """测试版本号比较功能"""
    print("=" * 60)
    print("测试1: 版本号比较")
    print("=" * 60)
    
    checker = UpdateChecker()
    
    test_cases = [
        ("1.0.0", "1.0.0", 0, "相等"),
        ("1.0.1", "1.0.0", 1, "新版本"),
        ("1.0.0", "1.0.1", -1, "旧版本"),
        ("2.0.0", "1.9.9", 1, "主版本更新"),
        ("1.1.0", "1.0.9", 1, "次版本更新"),
        ("1.0.10", "1.0.9", 1, "修订号更新"),
    ]
    
    all_passed = True
    for v1, v2, expected, desc in test_cases:
        result = checker._compare_versions(v1, v2)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓" if passed else "✗"
        print(f"{status} {desc}: {v1} vs {v2} = {result} (期望: {expected})")
    
    print()
    if all_passed:
        print("✓ 所有版本比较测试通过")
    else:
        print("✗ 部分版本比较测试失败")
    
    return all_passed


def test_github_config():
    """测试GitHub配置"""
    print("\n" + "=" * 60)
    print("测试2: GitHub配置")
    print("=" * 60)
    
    print(f"当前版本: {CURRENT_VERSION}")
    print(f"GitHub用户: {GITHUB_OWNER}")
    print(f"仓库名称: {GITHUB_REPO}")
    
    if GITHUB_OWNER == "your-username":
        print("\n⚠ 警告: GitHub用户名未配置")
        print("  请运行: python setup_github.py")
        return False
    
    print("\n✓ GitHub配置已设置")
    return True


def test_version_json():
    """测试version.json文件"""
    print("\n" + "=" * 60)
    print("测试3: version.json文件")
    print("=" * 60)
    
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        required_fields = ['version', 'description', 'release_date', 'download_url']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"✗ 缺少必需字段: {', '.join(missing_fields)}")
            return False
        
        print(f"✓ version.json格式正确")
        print(f"  版本: {data['version']}")
        print(f"  发布日期: {data['release_date']}")
        return True
        
    except FileNotFoundError:
        print("✗ version.json文件不存在")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ version.json格式错误: {e}")
        return False


def test_notifications_json():
    """测试notifications.json文件"""
    print("\n" + "=" * 60)
    print("测试4: notifications.json文件")
    print("=" * 60)
    
    try:
        with open('notifications.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'notifications' not in data:
            print("✗ 缺少notifications字段")
            return False
        
        notifications = data['notifications']
        print(f"✓ notifications.json格式正确")
        print(f"  通知数量: {len(notifications)}")
        
        for i, notif in enumerate(notifications, 1):
            title = notif.get('title', '无标题')
            date = notif.get('date', '无日期')
            print(f"  {i}. {title} ({date})")
        
        return True
        
    except FileNotFoundError:
        print("✗ notifications.json文件不存在")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ notifications.json格式错误: {e}")
        return False


def test_network_connection():
    """测试网络连接"""
    print("\n" + "=" * 60)
    print("测试5: 网络连接")
    print("=" * 60)
    
    try:
        import requests
        
        notif_verify = _resolve_verify(NOTIFICATION_CONFIG.get("ssl_verify", True), NOTIFICATION_CONFIG.get("ssl_ca_bundle", ""))
        update_verify = _resolve_verify(UPDATE_CONFIG.get("ssl_verify", True), UPDATE_CONFIG.get("ssl_ca_bundle", ""))

        notif_urls = _normalize_urls(NOTIFICATION_CONFIG.get("api_url", []))
        update_urls = _normalize_urls(UPDATE_CONFIG.get("api_url", []))

        print("正在测试通知地址连接...")
        notif_ok = False
        for url in notif_urls:
            try:
                response = requests.get(url, timeout=5, verify=notif_verify)
                if response.status_code == 200:
                    print("✓ 通知地址连接正常")
                    notif_ok = True
                    break
                print(f"✗ 通知地址返回状态码: {response.status_code}")
            except Exception as e:
                print(f"✗ 通知地址连接失败: {e}")

        print("正在测试更新地址连接...")
        update_ok = False
        for url in update_urls:
            try:
                response = requests.get(url, timeout=5, verify=update_verify)
                if response.status_code == 200:
                    print("✓ 更新地址连接正常")
                    update_ok = True
                    break
                print(f"✗ 更新地址返回状态码: {response.status_code}")
            except Exception as e:
                print(f"✗ 更新地址连接失败: {e}")

        return notif_ok and update_ok
            
    except requests.RequestException as e:
        print(f"✗ 网络连接失败: {e}")
        return False
    except ImportError:
        print("✗ requests库未安装")
        print("  运行: pip install requests")
        return False


def test_update_check_live():
    """测试实际的更新检查（需要网络）"""
    print("\n" + "=" * 60)
    print("测试6: 实际更新检查")
    print("=" * 60)
    
    if GITHUB_OWNER == "your-username":
        print("⚠ 跳过: GitHub配置未完成")
        return None
    
    print("正在检查更新...")
    print("(这可能需要几秒钟)")
    
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QEventLoop
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    checker = UpdateChecker(CURRENT_VERSION)
    result = {'success': False, 'message': ''}
    
    def on_update_available(version_info):
        result['success'] = True
        result['message'] = f"发现新版本: {version_info.get('version')}"
    
    def on_no_update():
        result['success'] = True
        result['message'] = "当前已是最新版本"
    
    def on_check_failed(error_msg):
        result['success'] = False
        result['message'] = f"检查失败: {error_msg}"
    
    checker.update_available.connect(on_update_available)
    checker.no_update.connect(on_no_update)
    checker.check_failed.connect(on_check_failed)
    
    checker.start()
    
    # 等待检查完成
    loop = QEventLoop()
    checker.finished.connect(loop.quit)
    loop.exec_()
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")
    
    return result['success']


def test_notification_fetch_live():
    """测试实际的通知获取（需要网络）"""
    print("\n" + "=" * 60)
    print("测试7: 实际通知获取")
    print("=" * 60)
    
    if GITHUB_OWNER == "your-username":
        print("⚠ 跳过: GitHub配置未完成")
        return None
    
    print("正在获取通知...")
    
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QEventLoop
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    fetcher = NotificationFetcher()
    result = {'success': False, 'message': '', 'count': 0}
    
    def on_notifications_received(notifications):
        result['success'] = True
        result['count'] = len(notifications)
        result['message'] = f"成功获取 {len(notifications)} 条通知"
    
    def on_fetch_failed(error_msg):
        result['success'] = False
        result['message'] = f"获取失败: {error_msg}"
    
    fetcher.notifications_received.connect(on_notifications_received)
    fetcher.fetch_failed.connect(on_fetch_failed)
    
    fetcher.start()
    
    # 等待获取完成
    loop = QEventLoop()
    fetcher.finished.connect(loop.quit)
    loop.exec_()
    
    if result['success']:
        print(f"✓ {result['message']}")
    else:
        print(f"✗ {result['message']}")
    
    return result['success']


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "更新系统测试套件" + " " * 25 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # 基础测试（不需要网络）
    results.append(("版本号比较", test_version_comparison()))
    results.append(("GitHub配置", test_github_config()))
    results.append(("version.json", test_version_json()))
    results.append(("notifications.json", test_notifications_json()))
    
    # 网络测试
    network_ok = test_network_connection()
    results.append(("网络连接", network_ok))
    
    if network_ok:
        # 实际功能测试（需要网络和正确配置）
        update_result = test_update_check_live()
        if update_result is not None:
            results.append(("更新检查", update_result))
        
        notif_result = test_notification_fetch_live()
        if notif_result is not None:
            results.append(("通知获取", notif_result))
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)
    
    for name, result in results:
        if result is True:
            status = "✓ 通过"
        elif result is False:
            status = "✗ 失败"
        else:
            status = "⚠ 跳过"
        print(f"{status}: {name}")
    
    print()
    print(f"总计: {total} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"跳过: {skipped} 个")
    
    if failed == 0:
        print("\n✓ 所有测试通过！")
        return True
    else:
        print(f"\n✗ {failed} 个测试失败")
        return False


if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试已中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
