# 网络拓扑与架构规划

## 1. 整体架构概述

本方案采用“内网隔离+VPN唯一入口”的安全架构。所有业务服务器仅配置内网 IP，通过 VPN 建立的安全隧道进行管理和访问。公网仅暴露 VPN 端口（UDP）。

## 2. IP 地址规划

采用私有网段 `10.0.0.0/8` 进行规划，避免与常见的家用路由器 `192.168.x.x` 冲突。

| 网段 | 用途 | 说明 |
| :--- | :--- | :--- |
| `10.10.0.0/24` | **核心服务区 (Core)** | 部署核心业务服务器（Web, API） |
| `10.10.10.0/24` | **数据存储区 (Data)** | 部署数据库、缓存、消息队列 (MySQL, Redis) |
| `10.10.20.0/24` | **运维管理区 (Ops)** | 部署堡垒机、监控系统 (Prometheus, Grafana) |
| `10.100.0.0/16` | **VPN 客户端池** | 分配给 VPN 拨入用户的虚拟 IP |

## 3. VLAN 划分

| VLAN ID | 名称 | 描述 | 安全策略 |
| :--- | :--- | :--- | :--- |
| 10 | VLAN_CORE | 核心业务网 | 允许访问 VLAN_DATA；允许被 VLAN_OPS 访问 |
| 20 | VLAN_DATA | 数据存储网 | 仅允许 VLAN_CORE 和 VLAN_OPS (特定端口) 访问；**禁止访问公网** |
| 30 | VLAN_OPS | 运维管理网 | 允许访问所有网段的 SSH/RDP/监控端口 |
| 100 | VLAN_VPN | VPN 接入网 | 仅允许访问 VLAN_CORE 的业务端口；管理端口需经堡垒机 |

## 4. 流量流向图

```mermaid
graph TD
    User[外部用户/管理员] -->|UDP 51820 (WireGuard)| FW[边界防火墙/VPN网关]
    
    subgraph "内部网络 (10.0.0.0/8)"
        FW -->|解密流量| VPN_IP[VPN 虚拟 IP]
        
        VPN_IP -->|HTTP/HTTPS| Web[Web 服务器 (10.10.0.x)]
        VPN_IP -->|SSH (通过堡垒机)| Bastion[堡垒机 (10.10.20.x)]
        
        Web -->|TCP 3306| DB[MySQL 数据库 (10.10.10.x)]
        Web -->|TCP 6379| Redis[Redis 缓存 (10.10.10.y)]
        
        Bastion -->|SSH| Web
        Bastion -->|SSH| DB
        Bastion -->|SSH| Redis
        
        Prometheus[监控服务器 (10.10.20.z)] -->|Pull Metrics| Web
        Prometheus -->|Pull Metrics| DB
    end
    
    classDef deny fill:#f9f,stroke:#333,stroke-width:2px;
    Internet[公网 Internet] -.->|DROP| Web
    Internet -.->|DROP| DB
```

## 5. 关键安全原则

1.  **零信任访问**：默认拒绝所有流量，仅开放白名单流量。
2.  **最小权限**：VPN 用户仅能访问其业务所需的 Web 端口，管理操作必须通过堡垒机。
3.  **数据区隔离**：数据库区域不配置公网网关，物理隔离公网连接。
