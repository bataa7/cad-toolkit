#!/bin/bash

# ==============================================================================
# Linux 服务器通用 iptables 安全加固脚本
# ==============================================================================
# 警告：执行此脚本可能会导致当前 SSH 连接中断，建议配合 crontab 定时任务恢复默认策略，
# 或者在本地/控制台（Console）环境下操作。
#
# 功能说明：
# 1. 清空现有规则
# 2. 设置默认策略为 DROP (INPUT/FORWARD)
# 3. 允许回环接口通信
# 4. 允许已建立的连接 (ESTABLISHED, RELATED)
# 5. 仅允许内网网段访问特定端口
# ==============================================================================

# 定义内网网段
INTERNAL_NET="10.0.0.0/8"
VPN_NET="10.100.0.0/16"

# 定义允许开放的端口 (根据服务器角色修改)
# SSH (建议修改默认 22 端口)
SSH_PORT=22
# Web 服务
WEB_PORTS="80,443"
# 数据库/缓存 (仅允许内网)
DB_PORTS="3306,6379"
# VPN 监听端口 (仅允许公网 UDP)
VPN_PORT=51820

# 1. 清空所有规则
echo "Flushing existing rules..."
iptables -F
iptables -X
iptables -Z

# 2. 设置默认策略
echo "Setting default policies..."
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 3. 允许本地回环接口 (Loopback)
echo "Allowing loopback..."
iptables -A INPUT -i lo -j ACCEPT

# 4. 允许已建立的连接和相关连接
echo "Allowing established connections..."
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 5. 允许 ICMP (Ping) - 限制速率防止洪泛
echo "Allowing ICMP (Ping)..."
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# 6. 允许 SSH 访问
# 策略：仅允许内网或 VPN IP 访问 SSH
echo "Allowing SSH from Internal Networks..."
iptables -A INPUT -p tcp -s $INTERNAL_NET --dport $SSH_PORT -j ACCEPT
iptables -A INPUT -p tcp -s $VPN_NET --dport $SSH_PORT -j ACCEPT
# 如果必须允许公网 SSH (强烈不建议，建议使用 VPN)，请取消注释下行并限制特定 IP
# iptables -A INPUT -p tcp -s <YOUR_ADMIN_IP> --dport $SSH_PORT -j ACCEPT

# 7. 允许 Web 服务 (仅允许内网/VPN，因为有前置负载均衡或 VPN 入口)
# 如果这台机器是直接面向公网的 VPN 网关，则需要开放 VPN 端口
echo "Allowing VPN port (UDP)..."
iptables -A INPUT -p udp --dport $VPN_PORT -j ACCEPT

# 业务端口开放给内网
echo "Allowing Business Ports from Internal Networks..."
iptables -A INPUT -p tcp -s $INTERNAL_NET -m multiport --dports $WEB_PORTS -j ACCEPT
iptables -A INPUT -p tcp -s $VPN_NET -m multiport --dports $WEB_PORTS -j ACCEPT

# 8. 允许数据库/缓存服务 (严格限制仅内网)
echo "Allowing Database Ports from Internal Networks ONLY..."
iptables -A INPUT -p tcp -s $INTERNAL_NET -m multiport --dports $DB_PORTS -j ACCEPT

# 9. 记录被丢弃的数据包 (可选，用于调试)
# iptables -A INPUT -j LOG --log-prefix "IPTables-Dropped: "

# 10. 保存规则 (适用于 CentOS/RHEL, Debian/Ubuntu 需使用 iptables-save > /etc/iptables/rules.v4)
echo "Rules applied."
echo "Please verify connectivity. If locked out, reboot server (if rules not saved)."

# 显示当前规则
iptables -L -n -v
