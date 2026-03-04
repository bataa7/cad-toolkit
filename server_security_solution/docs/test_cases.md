# 网络安全与访问控制测试用例

## 1. 测试目的
验证网络隔离策略、防火墙规则及VPN访问控制的有效性，确保仅授权用户能通过VPN访问指定内网资源。

## 2. 测试环境
- **公网测试机**: 模拟外部攻击者 (IP: Public_IP_A)
- **VPN 客户端**: 模拟合法远程办公用户 (IP: Public_IP_B -> VPN IP: 10.100.0.x)
- **内网跳板机**: 模拟已入侵或内部运维操作 (IP: 10.10.20.x)

## 3. 测试用例清单

### 3.1 端口扫描与连通性测试 (公网视角)

| 用例ID | 测试项 | 操作步骤 | 预期结果 | 实际结果 |
| :--- | :--- | :--- | :--- | :--- |
| TC-NET-01 | Web端口公网访问 | `curl -I http://<Web_Public_IP>` | **连接超时 (Timeout)** 或 拒绝连接 | |
| TC-NET-02 | SSH端口公网访问 | `ssh user@<Bastion_Public_IP>` | **连接超时 (Timeout)** 或 拒绝连接 | |
| TC-NET-03 | 数据库端口公网访问 | `telnet <DB_Public_IP> 3306` | **连接超时 (Timeout)** | |
| TC-NET-04 | VPN端口可用性 | `nc -u -z -v <VPN_Public_IP> 51820` | **成功 (Succeeded)** | |
| TC-NET-05 | 全端口扫描 (Nmap) | `nmap -Pn -p- <Target_Public_IP>` | 仅 51820/UDP 开放，其余全部过滤 (Filtered) | |

### 3.2 VPN 访问控制测试 (VPN 客户端视角)

| 用例ID | 测试项 | 操作步骤 | 预期结果 | 实际结果 |
| :--- | :--- | :--- | :--- | :--- |
| TC-VPN-01 | VPN 连接建立 | 启动 WireGuard 客户端连接 | 握手成功，获取 10.100.x.x IP | |
| TC-VPN-02 | 访问内部 Web 服务 | 浏览器访问 `http://10.10.0.x` | 页面正常加载 | |
| TC-VPN-03 | 直接访问数据库 | `mysql -h 10.10.10.x -u user -p` | **连接拒绝 (Refused)** 或 超时 (根据防火墙策略) | |
| TC-VPN-04 | 访问堡垒机 SSH | `ssh user@10.10.20.x` | 提示输入密码/密钥，登录成功 | |

### 3.3 内网横向移动测试 (内网跳板机视角)

| 用例ID | 测试项 | 操作步骤 | 预期结果 | 实际结果 |
| :--- | :--- | :--- | :--- | :--- |
| TC-INT-01 | 数据库访问 | `mysql -h 10.10.10.x -u app_user -p` | **登录成功** | |
| TC-INT-02 | 跨 VLAN 访问限制 | 从 Web 服务器 ping 数据库服务器 | 根据 VLAN 策略 (允许/禁止) | |
| TC-INT-03 | 外网访问能力 | `curl https://www.google.com` | 若无 NAT 网关配置，应无法访问 | |

## 4. 测试脚本示例

### 4.1 自动扫描脚本 (scan_check.sh)

```bash
#!/bin/bash
TARGET_IP=$1
echo "Checking $TARGET_IP..."

# Check Web Ports
for PORT in 80 443 8080; do
    nc -z -w 2 $TARGET_IP $PORT && echo "PORT $PORT OPEN (FAIL)" || echo "PORT $PORT CLOSED (PASS)"
done

# Check SSH
nc -z -w 2 $TARGET_IP 22 && echo "SSH OPEN (FAIL)" || echo "SSH CLOSED (PASS)"

# Check DB
nc -z -w 2 $TARGET_IP 3306 && echo "MySQL OPEN (FAIL)" || echo "MySQL CLOSED (PASS)"
```

## 5. 验收标准
1.  所有“公网视角”测试必须全部通过（即无法访问除 VPN 外的任何服务）。
2.  VPN 用户必须能且仅能访问授权的内部资源。
3.  数据库等核心资产必须无法从互联网直接触达。
