# Dev Tunnels 使用指南

## 概述

[Dev Tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/) 是微软提供的一项服务，可以将本地运行的服务通过安全隧道暴露到公网，方便在开发和调试阶段让外部服务（如 Azure AI Search）访问本地的 Azure Functions。

在本项目中，我们使用 Dev Tunnels 将本地运行在 `localhost:7071` 的 Custom Skill Function 暴露出去，供 Azure AI Search Indexer 调用。

## 前置条件

- 已安装 [Visual Studio Code](https://code.visualstudio.com/)
- 已安装 [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- 拥有 Microsoft Entra ID 账号或 GitHub 账号（用于 Dev Tunnels 认证）

## 安装 Dev Tunnels CLI

### macOS

```bash
brew install --cask devtunnel
```

### Windows

```powershell
winget install Microsoft.devtunnel
```

### Linux

```bash
curl -sL https://aka.ms/DevTunnelCliInstall | bash
```

## 使用步骤

### 1. 登录 Dev Tunnels

Dev Tunnels 支持多种认证方式，首次使用需要登录：

#### 方式一：使用 Microsoft Entra ID 账号（默认）

```bash
devtunnel user login
```

会弹出浏览器进行 Microsoft 账号认证。

#### 方式二：使用 GitHub 账号（推荐，避免组织设备管理限制）

```bash
devtunnel user login -g
```

如果你的组织要求设备被 Intune 管理而无法使用 Microsoft 账号登录，可以使用 GitHub 账号作为替代。

#### 方式三：使用设备码流程（无法弹出浏览器时）

```bash
# Microsoft Entra ID + 设备码
devtunnel user login -d

# GitHub + 设备码
devtunnel user login -g -d
```

> **其他高级认证方式**：还支持 Entra Service Principal（`--sp-*` 参数）和 Azure Managed Identity（`--mi-*` 参数），适用于 CI/CD 等自动化场景。详见 `devtunnel user login --help`。

登录成功后终端会显示确认信息。

### 2. 启动本地 Azure Functions

在 `custom_skill` 目录下启动 Azure Functions：

```bash
cd custom_skill
func host start
```

默认会在 `localhost:7071` 上启动服务。确认函数启动成功后，继续下一步。

### 3. 创建并启动隧道

#### 方式一：一键创建临时隧道（推荐用于快速调试）

```bash
devtunnel host -p 7071 --allow-anonymous
```

参数说明：
- `-p 7071`：指定要转发的本地端口
- `--allow-anonymous`：允许匿名访问（Azure AI Search Indexer 不需要额外认证即可调用）

启动后终端会输出类似：

```
Connect via browser: https://zz08bgqx-7071.asse.devtunnels.ms
```

#### 方式二：创建持久隧道（推荐用于反复调试）

```bash
# 创建隧道
devtunnel create --allow-anonymous

# 添加端口映射
devtunnel port create -p 7071

# 启动隧道
devtunnel host
```

持久隧道会保留配置，下次使用只需 `devtunnel host` 即可。

#### 方式三：在 VS Code 中使用（图形化操作）

1. 按 `Cmd+Shift+P`（macOS）/ `Ctrl+Shift+P`（Windows）打开命令面板
2. 搜索 **"Dev Tunnels: Create a Tunnel"**
3. 按提示选择端口 `7071`
4. 选择访问级别为 **Public**（允许匿名访问）
5. 创建完成后，在 **PORTS** 面板查看转发的 URL

### 4. 获取隧道 URL

隧道启动后，你会得到一个公网可访问的 URL，格式如：

```
https://<tunnel-id>-7071.<region>.devtunnels.ms
```

例如：`https://zz08bgqx-7071.asse.devtunnels.ms`

### 5. 测试隧道连通性

使用 VS Code REST Client 插件测试，打开 `test_skill.http` 文件：

1. 将 `@baseUrl` 更新为你的隧道 URL：
   ```
   @baseUrl = https://<your-tunnel-id>-7071.<region>.devtunnels.ms
   ```
2. 点击 `Send Request` 发送测试请求
3. 确认返回 200 状态码和正确的响应数据

或使用 curl 命令测试：

```bash
curl -X POST https://<your-tunnel-id>-7071.<region>.devtunnels.ms/api/page_content_split_http_trigger \
  -H "Content-Type: application/json" \
  -d '{
    "values": [
      {
        "recordId": "r1",
        "data": {
          "page_content": "id:5000\n\nquestion: test\n\nanswer: <Brief>test</Brief>"
        }
      }
    ]
  }'
```

### 6. 配置 Azure AI Search Skillset

将隧道 URL 配置到 Azure AI Search 的 Skillset 中，作为 Custom Web API Skill 的 `uri`：

```json
{
  "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
  "name": "page_content_split_skill",
  "uri": "https://<your-tunnel-id>-7071.<region>.devtunnels.ms/api/page_content_split_http_trigger",
  "httpMethod": "POST",
  "batchSize": 10,
  "context": "/document",
  "inputs": [
    {
      "name": "page_content",
      "source": "/document/page_content"
    }
  ],
  "outputs": [
    {
      "name": "product_id",
      "targetName": "product_id"
    },
    {
      "name": "question",
      "targetName": "question"
    },
    {
      "name": "brief",
      "targetName": "brief"
    },
    {
      "name": "specification",
      "targetName": "specification"
    }
  ]
}
```

## 工作原理

Dev Tunnels 本质是一个**反向隧道代理（Reverse Tunnel Proxy）**：

```
[外部请求] → [微软云端 Relay 服务器] ←长连接← [本地 devtunnel 客户端] → [localhost:7071]
```

**工作流程：**

1. 本地 `devtunnel` 客户端启动后，与微软云端的 Relay 服务建立一个**持久的出站 WebSocket/HTTP2 连接**
2. 云端分配一个公网 URL（如 `https://xxx-7071.asse.devtunnels.ms`）
3. 外部请求到达该 URL 时，Relay 服务通过已建立的长连接将流量转发到本地客户端
4. 本地客户端再将流量转发到指定的本地端口（如 `7071`）

**关键点：** 因为是本地主动发起出站连接，所以不需要公网 IP、不需要配置防火墙或路由器端口转发。所有隧道方案的核心原理相同，区别在于中继点由谁提供、是否需要自建、安全策略如何配置。

## 替代方案

除了 Microsoft Dev Tunnels，还有多种工具可以实现相同的本地服务暴露功能：

### 开源 / 第三方方案

| 工具 | 特点 | 安装 | 使用示例 |
|------|------|------|----------|
| **[ngrok](https://ngrok.com/)** | 最流行的隧道工具，免费版有限制（限速、临时 URL） | `brew install ngrok` | `ngrok http 7071` |
| **[Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)** | 免费、无带宽限制、需 Cloudflare 账号 | `brew install cloudflared` | `cloudflared tunnel --url http://localhost:7071` |
| **[frp](https://github.com/fatedier/frp)** | 纯开源自建方案，需要自己有公网服务器 | GitHub Releases 下载 | 配置 frps（服务端）+ frpc（客户端） |
| **[bore](https://github.com/ekzhang/bore)** | Rust 写的极简隧道，可自建服务端 | `cargo install bore-cli` | `bore local 7071 --to bore.pub` |
| **[localtunnel](https://github.com/localtunnel/localtunnel)** | Node.js 开源方案，零配置 | `npm install -g localtunnel` | `lt --port 7071` |
| **[Tailscale Funnel](https://tailscale.com/kb/1223/funnel)** | 基于 WireGuard 的 mesh VPN + 公网暴露 | `brew install tailscale` | `tailscale funnel 7071` |

### 云厂商方案

| 厂商 | 方案 | 说明 |
|------|------|------|
| **Microsoft** | [Dev Tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/)（本方案） | 与 VS Code / Azure 生态深度集成 |
| **GitHub** | [Codespaces 端口转发](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace) | Codespaces 环境内置，原理相同 |
| **Google Cloud** | [IAP TCP Forwarding](https://cloud.google.com/iap/docs/using-tcp-forwarding) | 用于访问 GCP 内部资源，非公网暴露本地服务；一般需搭配 ngrok/cloudflared |
| **AWS** | [SSM Session Manager 端口转发](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) | 用于访问 EC2 内部端口，非公网暴露本地服务；一般需搭配 ngrok/cloudflared |

### 方案选择建议

| 场景 | 推荐方案 | 理由 |
|------|----------|------|
| 已在微软/GitHub 生态中 | **Dev Tunnels** | 与 VS Code、Azure Functions 无缝集成 |
| 需要稳定、免费的生产级隧道 | **Cloudflare Tunnel** | 无带宽限制、免费、全球 CDN 加速 |
| 快速临时调试（一次性） | **ngrok** | 最简单，一行命令即可 |
| 完全自主控制、数据不经第三方 | **frp** | 开源自建，需自备公网服务器 |
| 团队内网互联（P2P） | **Tailscale** | P2P mesh 网络，数据不经过中继 |
| CI/CD 环境或无浏览器场景 | **bore** | 轻量、支持自建、无需登录 |

> 💡 **提示**：对于本项目（Azure AI Search Custom Skill 开发调试），Dev Tunnels 是首选，因为它与 Azure 生态集成最好且支持 `--allow-anonymous` 满足 Indexer 调用需求。如果遇到组织账号限制，Cloudflare Tunnel 或 ngrok 是最佳替代。

## 常用命令参考

| 命令 | 说明 |
|------|------|
| `devtunnel user login` | 登录 Microsoft Entra ID 账号 |
| `devtunnel user login -g` | 登录 GitHub 账号 |
| `devtunnel user show` | 查看当前登录状态 |
| `devtunnel host -p 7071 --allow-anonymous` | 创建临时隧道并暴露 7071 端口 |
| `devtunnel list` | 列出所有已创建的隧道 |
| `devtunnel delete <tunnel-id>` | 删除指定隧道 |
| `devtunnel delete-all` | 删除所有隧道 |
| `devtunnel host` | 启动已有的隧道 |
| `devtunnel port list` | 查看当前隧道的端口映射 |

## 访问控制选项

| 选项 | 说明 | 适用场景 |
|------|------|----------|
| `--allow-anonymous` | 任何人可访问，无需认证 | Azure AI Search Indexer 调用 |
| 无额外参数（默认） | 需要 Microsoft 账号登录 | 仅自己调试 |
| `--access-control org` | 同组织用户可访问 | 团队协作调试 |

> ⚠️ **注意**：如果用于 Azure AI Search Indexer 调用，必须使用 `--allow-anonymous`，因为 Indexer 不支持 Dev Tunnels 的认证机制。

## 注意事项

1. **隧道生命周期**：临时隧道在 CLI 进程结束后即关闭；持久隧道需手动删除。
2. **URL 变化**：每次创建新的临时隧道，URL 都会变化，需要重新配置 Skillset。
3. **网络延迟**：通过隧道转发会增加一定延迟，仅建议在开发调试阶段使用。
4. **安全性**：使用 `--allow-anonymous` 时，隧道 URL 相当于公网暴露，请勿在隧道中运行含敏感数据的服务。
5. **区域选择**：Dev Tunnels 会自动选择最近的区域（如 `asse` 代表东南亚），无需手动配置。
6. **生产环境**：正式上线时应部署到 Azure Functions，使用 `DEPLOYMENT.md` 中的部署流程。

## 典型工作流

```
┌─────────────────┐       ┌──────────────┐       ┌─────────────────────┐
│  Azure AI Search │──────▶│  Dev Tunnels  │──────▶│  localhost:7071     │
│  (Indexer/       │       │  (公网URL)    │       │  (Azure Functions)  │
│   Skillset)      │◀──────│              │◀──────│                     │
└─────────────────┘       └──────────────┘       └─────────────────────┘
```

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 隧道启动后无法访问 | 确认本地 Functions 已启动且正常响应 `localhost:7071` |
| 返回 403 Forbidden | 检查是否添加了 `--allow-anonymous` 参数 |
| 返回 502 Bad Gateway | 本地服务未启动或端口不匹配，检查 Functions 运行状态 |
| 登录失败 | 运行 `devtunnel user logout` 后重新 `devtunnel user login` |
| URL 过期或不可用 | 重新创建隧道获取新 URL |
| Functions 冷启动超时 | 先手动调用一次本地接口预热，再通过隧道测试 |
