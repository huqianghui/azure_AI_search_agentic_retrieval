# Non-Split RAG 配置部署指南

## 概述

此配置使用自定义技能从 `page_content` 字段中提取结构化信息（question 和 answer），然后对原始内容进行向量化。

## 配置文件说明

### 1. 索引 (json-data-rag-non-split-demo05.json)
定义了以下字段：
- `id`: 文档唯一标识（主键）
- `page_content`: 原始内容
- `page_content_vector`: 内容向量（3072维）
- **`question`**: 从 page_content 提取的问题 ✨ 新增
- **`answer`**: 从 page_content 提取的答案 ✨ 新增
- `metadata`: 元数据复杂类型

### 2. 技能集 (json-data-rag-non-split-demo05-skillset.json)
包含两个技能：

#### 技能 #1: 自定义内容提取技能
- **类型**: WebApiSkill
- **端点**: `https://azure-ai-search-split-custom-skill.azurewebsites.net/api/page_content_split_http_trigger`
- **输入**: `page_content`
- **输出**: 
  - `extracted_id` (可选)
  - `question`
  - `answer`

#### 技能 #2: Azure OpenAI 嵌入技能
- **模型**: text-embedding-3-large
- **维度**: 3072
- **输入**: `page_content`
- **输出**: `page_content_vector`

### 3. 索引器 (json-data-rag-non-split-demo05-indexer.json)
字段映射：
- **输入映射**: `AzureSearch_DocumentKey` → `id` (base64编码)
- **输出映射**:
  - `/document/page_content_vector` → `page_content_vector`
  - `/document/question` → `question` ✨ 新增
  - `/document/answer` → `answer` ✨ 新增

## 部署步骤

### 1. 更新或创建索引

```bash
# 使用 Azure Portal 或 REST API
PUT https://[service-name].search.windows.net/indexes/json-data-rag-non-split-demo05?api-version=2024-07-01
Content-Type: application/json
api-key: [admin-key]

[json-data-rag-non-split-demo05.json 文件内容]
```

### 2. 更新或创建技能集

**重要：配置认证密钥**

在部署技能集之前，需要获取并配置以下密钥：

1. **Azure Function Key**（自定义技能认证）
   - 登录 [Azure Portal](https://portal.azure.com)
   - 找到 Function App: `azure-ai-search-split-custom-skill`
   - 进入 **Functions** → `page_content_split_http_trigger`
   - 点击 **Function Keys** → 复制 `default` key
   - 替换 skillset 配置中的 `<YOUR_FUNCTION_KEY>`

2. **Azure OpenAI API Key**（Embedding 技能认证）
   - 在 Azure Portal 找到你的 OpenAI 资源
   - 进入 **Keys and Endpoint**
   - 复制 Key 1 或 Key 2
   - 替换 skillset 配置中的 `<redacted>`

然后创建或更新技能集：

```bash
PUT https://[service-name].search.windows.net/skillsets/json-data-rag-non-split-demo05-skillset?api-version=2024-07-01
Content-Type: application/json
api-key: [admin-key]

[json-data-rag-non-split-demo05-skillset.json 文件内容]
```

**需要替换的占位符：**
- `<YOUR_FUNCTION_KEY>`: Azure Function 的访问密钥
- `<redacted>`: Azure OpenAI API Key

### 3. 更新或创建索引器

```bash
PUT https://[service-name].search.windows.net/indexers/json-data-rag-non-split-demo05-indexer?api-version=2024-07-01
Content-Type: application/json
api-key: [admin-key]

[json-data-rag-non-split-demo05-indexer.json 文件内容]
```

### 4. 运行索引器

```bash
POST https://[service-name].search.windows.net/indexers/json-data-rag-non-split-demo05-indexer/run?api-version=2024-07-01
api-key: [admin-key]
```

### 5. 检查索引器状态

```bash
GET https://[service-name].search.windows.net/indexers/json-data-rag-non-split-demo05-indexer/status?api-version=2024-07-01
api-key: [admin-key]
```

## 自定义技能验证

在更新配置之前，验证自定义技能是否正常工作：

```bash
curl -X POST https://azure-ai-search-split-custom-skill.azurewebsites.net/api/page_content_split_http_trigger \
  -H "Content-Type: application/json" \
  -d '{
    "values": [
      {
        "recordId": "test1",
        "data": {
          "page_content": "id: 123\n\nquestion: 如何配置路由器？\n\nanswer: 请按照以下步骤配置路由器..."
        }
      }
    ]
  }'
```

预期响应：
```json
{
  "values": [
    {
      "recordId": "test1",
      "data": {
        "id": "123",
        "question": "如何配置路由器？",
        "answer": "请按照以下步骤配置路由器..."
      },
      "errors": [],
      "warnings": []
    }
  ]
}
```

## 数据格式要求

源数据中的 `page_content` 字段应遵循以下格式：

```
id: [可选ID]

question: [问题内容]

answer: [答案内容]
```

示例：
```
id: product_q1

question: Omada SDN 控制器支持哪些功能？

answer: Omada SDN 控制器支持集中管理、零配置部署、实时监控等功能...
```

## 查询示例

### 向量搜索（语义相似度）
```json
{
  "vectorQueries": [
    {
      "kind": "vector",
      "vector": [0.1, 0.2, ...], // 问题的向量表示
      "fields": "page_content_vector",
      "k": 5
    }
  ],
  "select": "id,question,answer,page_content"
}
```

### 关键词搜索
```json
{
  "search": "路由器配置",
  "select": "id,question,answer",
  "top": 10
}
```

### 混合搜索
```json
{
  "search": "路由器",
  "vectorQueries": [
    {
      "kind": "vector",
      "vector": [0.1, 0.2, ...],
      "fields": "page_content_vector",
      "k": 50
    }
  ],
  "select": "id,question,answer,page_content",
  "top": 10
}
```

## 故障排查

### 1. 自定义技能超时
- 检查 Azure Function 是否正常运行
- 查看 Function App 日志
- 考虑增加 skillset 中的 `timeout` 值

### 2. 字段未被提取
- 验证 `page_content` 格式是否正确
- 检查自定义技能的警告信息
- 查看索引器执行历史记录

### 3. 向量化失败
- 确认 Azure OpenAI API Key 正确
- 检查 OpenAI 部署是否可用
- 查看配额限制

## 性能优化建议

1. **批处理大小**: 根据文档大小调整 indexer 的 `batchSize`
2. **并行度**: 自定义技能的 `degreeOfParallelism` 可以根据 Function 性能调整
3. **缓存**: 启用索引器缓存以提高增量索引性能

## 相关文档

- [Azure AI Search Custom Skills](https://learn.microsoft.com/azure/search/cognitive-search-custom-skill-web-api)
- [Azure Functions HTTP Trigger](https://learn.microsoft.com/azure/azure-functions/functions-bindings-http-webhook-trigger)
- [Vector Search in Azure AI Search](https://learn.microsoft.com/azure/search/vector-search-overview)
