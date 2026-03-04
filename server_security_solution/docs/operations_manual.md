# 服务器安全运维与应急手册

## 1. 日常巡检清单

| 频率 | 检查项 | 操作命令/工具 | 正常标准 |
| :--- | :--- | :--- | :--- |
| 每日 | 系统负载与资源 | `uptime`, `top`, `htop` | Load Avg < CPU核数，内存使用率 < 80% |
| 每日 | 磁盘空间 | `df -h` | 各分区使用率 < 85% |
| 每日 | 登录日志审计 | `last -a`, `grep 'Failed' /var/log/secure` | 无异常 IP 登录失败记录 |
| 每周 | 防火墙规则状态 | `iptables -L -n -v` | 规则生效，DROP 计数合理增长 |
| 每周 | 关键服务状态 | `systemctl status nginx mysql redis wireguard` | Active (running) |
| 每周 | 备份验证 | 检查 `/backup/` 目录文件大小与时间 | 备份文件按计划生成，大小正常 |
| 每月 | 系统安全更新 | `apt update && apt upgrade` (Ubuntu) | 系统补丁及时安装，重启生效 |

## 2. 故障排查步骤

### 2.1 VPN 连接失败
1.  **检查客户端状态**: 确认客户端公钥是否在服务端配置中 (`wg show`)。
2.  **检查服务端端口**: `netstat -ulnp | grep 51820` 确认监听正常。
3.  **检查防火墙**: 确认 UDP 51820 端口开放 (`iptables -L -n | grep 51820`)。
4.  **检查日志**: `journalctl -u wg-quick@wg0` 查看 WireGuard 启动日志。
5.  **时间同步**: 确保客户端与服务端时间同步 (`date`)，偏差过大导致握手失败。

### 2.2 无法访问内网服务
1.  **检查路由**: 确认客户端路由表是否包含内网网段 (`route print` 或 `ip route`)。
2.  **检查转发**: 服务端是否开启 IP 转发 (`sysctl net.ipv4.ip_forward`)。
3.  **检查 NAT**: `iptables -t nat -L -n` 确认 POSTROUTING 规则存在。
4.  **检查服务绑定**: 确认目标服务监听 IP 是否为内网 IP (`netstat -tlnp`)。

## 3. 应急封禁流程

当检测到异常访问或攻击行为时：

### 3.1 立即封禁恶意 IP
使用 `iptables` 快速封禁源 IP：
```bash
# 封禁单个 IP
iptables -I INPUT -s <Attacker_IP> -j DROP
# 封禁 IP 段
iptables -I INPUT -s <Attacker_Subnet>/24 -j DROP
```

### 3.2 暂停 VPN 访问
若怀疑 VPN 凭证泄露：
1.  立即停止 WireGuard 服务：`systemctl stop wg-quick@wg0`。
2.  移除涉事用户公钥配置 (`/etc/wireguard/wg0.conf`)。
3.  重启 VPN 服务：`systemctl start wg-quick@wg0`。

### 3.3 强制断开 SSH 会话
查找并杀掉异常用户的 SSH 进程：
```bash
ps -ef | grep sshd
kill -9 <PID>
pkill -u <Suspicious_User>
```

## 4. 账号管理规范

1.  **添加新用户**: 必须指定 SSH 密钥，禁止密码登录。
2.  **离职处理**: 
    - 禁用系统账号: `usermod -L <username>`
    - 移除 VPN 公钥配置。
    - 强制注销当前会话。
3.  **定期轮换**: 管理员密码每 90 天强制修改，SSH 密钥每 180 天建议轮换。
