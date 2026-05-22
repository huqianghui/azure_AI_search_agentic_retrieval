# Azure AI Search 智能检索项目

基于 Azure AI Search 构建的 RAG（检索增强生成）解决方案，用于智能问答和文档检索。

## 项目结构

```
├── azure-search-classic-rag/    # 经典 RAG 模式示例和教程
├── custom_skill/                # Azure Functions 自定义技能
├── config/                      # 索引配置文件
│   ├── RAG/                     # RAG 配置（文档分块）
│   ├── non-split-RAG/           # 不分块 RAG 配置
│   └── keywords/                # 关键词检索配置
└── data/                        # 示例数据
```

## 主要功能

### 1. 自定义技能 (Custom Skill)
- **功能**: 页面内容智能分割和字段提取
- **技术**: Azure Functions + Python
- **用途**: 在索引流程中解析和处理文档内容

### 2. 多种检索模式
- **RAG 模式**: 支持文档分块、向量化和语义检索
- **关键词模式**: 传统关键词搜索
- **混合模式**: 结合向量和关键词检索

## 快速开始

### 1. 本地运行自定义技能

```bash
cd custom_skill
pip install -r requirements.txt
func start
```

访问: `http://localhost:7071`

### 2. 本地测试自定义技能

使用 VS Code REST Client 插件打开 `custom_skill/test_skill.http`，发送请求验证函数逻辑是否正确。

### 3. 配置 Azure AI Search

根据需求选择配置文件：
- `config/RAG/` - 用于向量检索和 RAG
- `config/keywords/` - 用于关键词检索
- `config/non-split-RAG/` - 用于不分块的 RAG
- `config/custom-skill-RAG/` - 用于自定义技能 + RAG

### 4. 运行示例 Notebook

```bash
cd azure-search-classic-rag
jupyter notebook
```

---

## 本地联调与发布流程

完整的开发流程为：**本地开发 → Dev Tunnels 联调 → 确认效果 → 部署到 Azure Functions**。

### 第一步：本地开发与单元测试

1. 启动本地 Functions：
   ```bash
   cd custom_skill
   func start
   ```

2. 使用 `test_skill.http` 对函数进行本地测试，确保解析逻辑正确。

### 第二步：使用 Dev Tunnels 暴露本地服务

本地函数通过测试后，需要验证它在 Azure AI Search 索引管道中是否正常工作。由于 Azure AI Search 运行在云端，无法直接调用 `localhost`，因此需要通过 Dev Tunnels 创建公网隧道。

#### 安装 Dev Tunnels CLI

```bash
# macOS
brew install --cask devtunnel

# Windows
winget install Microsoft.devtunnel
```

#### 登录并创建隧道

```bash
# 登录 Microsoft 账号
devtunnel user login

# 创建隧道并暴露 7071 端口（允许匿名访问）
devtunnel host -p 7071 --allow-anonymous
```

> ⚠️ 必须使用 `--allow-anonymous`，否则 Azure AI Search Indexer 无法访问隧道。

启动后会输出公网 URL，例如：
```
https://zz08bgqx-7071.asse.devtunnels.ms
```

> 详细使用说明参见 [custom_skill/DEVTUNNELS_GUIDE.md](custom_skill/DEVTUNNELS_GUIDE.md)

### 第三步：配置 Skillset 指向隧道 URL

将隧道 URL 填入 Skillset 配置的 `uri` 字段。参考 `config/custom-skill-RAG/json-data-rag-custom-skill-demo05-skillset.json`：

```json
{
  "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
  "name": "#1",
  "description": "Custom skill to extract id, question, and answer from page_content",
  "context": "/document",
  "uri": "https://<your-tunnel-id>-7071.<region>.devtunnels.ms/api/page_content_split_http_trigger",
  "httpMethod": "POST",
  "timeout": "PT30S",
  "batchSize": 1,
  "inputs": [
    {
      "name": "page_content",
      "source": "/document/page_content"
    }
  ],
  "outputs": [
    {
      "name": "id",
      "targetName": "extracted_id"
    },
    {
      "name": "question",
      "targetName": "question"
    },
    {
      "name": "answer",
      "targetName": "answer"
    }
  ]
}
```

### 第四步：运行 Indexer 进行联调

通过 Azure Portal 或 REST API 运行 Indexer，触发完整的索引管道：

```bash
# 使用 REST API 运行 Indexer
curl -X POST "https://<your-search-service>.search.windows.net/indexers/json-data-rag-custom-skill-demo05-indexer/run?api-version=2024-07-01" \
  -H "api-key: <your-admin-key>" \
  -H "Content-Type: application/json"
```

或者在 Azure Portal 中：
1. 进入 Azure AI Search 服务
2. 找到 Indexer `json-data-rag-custom-skill-demo05-indexer`
3. 点击 **Run** 手动触发

#### 验证联调结果

- **查看本地终端日志**：观察 Functions 是否收到请求、处理是否正常
- **查看 Indexer 执行状态**：在 Azure Portal 确认 Indexer 是否运行成功
- **检查索引数据**：在 Search Explorer 中验证字段提取结果是否正确

```bash
# 查看 Indexer 状态
curl "https://<your-search-service>.search.windows.net/indexers/json-data-rag-custom-skill-demo05-indexer/status?api-version=2024-07-01" \
  -H "api-key: <your-admin-key>"
```

### 第五步：确认效果后部署到 Azure Functions

联调通过后，将自定义技能部署到 Azure Functions：

```bash
cd custom_skill

# 部署到 Azure（需已创建 Function App）
func azure functionapp publish azure-ai-search-split-custom-skill
```

部署完成后，更新 Skillset 的 `uri` 为 Azure Functions 的正式地址：

```json
"uri": "https://azure-ai-search-split-custom-skill.azurewebsites.net/api/page_content_split_http_trigger?code=<YOUR_FUNCTION_KEY>"
```

> 获取 Function Key 的方法参见 [custom_skill/DEPLOYMENT.md](custom_skill/DEPLOYMENT.md)

### 流程总结

```
┌──────────────┐    ┌───────────────┐    ┌──────────────────┐    ┌────────────────┐
│ 1. 本地开发   │───▶│ 2. Dev Tunnels │───▶│ 3. Indexer 联调   │───▶│ 4. 部署到 Azure │
│ func start   │    │ 暴露到公网     │    │ 验证端到端效果    │    │ func publish   │
│ + 单元测试    │    │               │    │                  │    │ + 更新 Skillset │
└──────────────┘    └───────────────┘    └──────────────────┘    └────────────────┘
```

## 技术栈

- **Azure AI Search**: 核心搜索引擎
- **Azure Functions**: 自定义技能处理
- **Python**: 主要开发语言
- **OpenAI/Azure OpenAI**: 向量嵌入和对话生成

## 配置说明

每个配置目录包含：
- `*-datasource.json`: 数据源配置
- `*-index.json`: 索引定义
- `*-indexer.json`: 索引器配置
- `*-skillset.json`: 技能集定义

## 依赖项

```bash
# 安装自定义技能依赖
cd custom_skill
pip install -r requirements.txt

# 安装 RAG 示例依赖
cd azure-search-classic-rag
pip install -r requirements.txt
```

## 测试

使用提供的测试文件测试自定义技能：

```bash
cd custom_skill
# 查看 test_skill.http 或 test_skill.json
```

## 参考资料

- [Azure AI Search 文档](https://learn.microsoft.com/azure/search/)
- [Agentic Retrieval 概述](https://learn.microsoft.com/azure/search/agentic-retrieval-overview)

## License

MIT
