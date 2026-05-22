# Dev Tunnels 使用指南

## 概述

[Dev Tunnels](https://learn.microsoft.com/azure/developer/dev-tunnels/) 是微软提供的一项服务，可以将本地运行的服务通过安全隧道暴露到公网，方便在开发和调试阶段让外部服务（如 Azure AI Search）访问本地的 Azure Functions。

在本项目中，我们使用 Dev Tunnels 将本地运行在 `localhost:7071` 的 Custom Skill Function 暴露出去，供 Azure AI Search Indexer 调用。

## 前置条件

- 已安装 [Visual Studio Code](https://code.visualstudio.com/)
- 已安装 [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- 拥有 Microsoft 账号（用于 Dev Tunnels 认证）

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

首次使用需要登录 Microsoft 账号：

```bash
devtunnel user login
```

会弹出浏览器进行 Microsoft 账号认证。登录成功后终端会显示确认信息。

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

## 常用命令参考

| 命令 | 说明 |
|------|------|
| `devtunnel user login` | 登录 Microsoft 账号 |
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
