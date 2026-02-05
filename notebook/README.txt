# Azure AI Search - Knowledge Retrieval API 说明文档
# API Version: 2025-11-01-preview
# 参考文档: https://learn.microsoft.com/en-us/rest/api/searchservice/knowledge-retrieval/retrieve

================================================================================
## 1. API 概述
================================================================================

Knowledge Retrieval API 是 Azure AI Search 的 Agentic Retrieval 功能的核心接口。
它允许通过消息驱动的方式从知识库中检索信息，并可选择性地合成答案。

### 请求格式
POST https://<search-service-name>.search.windows.net/knowledgebases('<knowledge-base-name>')/retrieve?api-version=2025-11-01-preview

### 请求头
- Content-Type: application/json
- api-key: <your-admin-api-key>

================================================================================
## 2. 请求体参数详解
================================================================================

### 2.1 messages (必需)
用于指定检索的对话消息列表。

| 参数 | 类型 | 说明 |
|------|------|------|
| role | string | 消息角色: "user" 或 "assistant" |
| content | array | 消息内容数组 |
| content[].type | string | 内容类型: "text" |
| content[].text | string | 实际的文本内容 |

### 2.2 maxRuntimeInSeconds (可选)
| 参数 | 类型 | 默认值 | 范围 | 说明 |
|------|------|--------|------|------|
| maxRuntimeInSeconds | integer | 60 | 1-300 | 检索操作的最大运行时间（秒）|

### 2.3 maxOutputSize (可选)
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| maxOutputSize | integer | 100000 | 返回结果的最大输出大小（字符数）|

### 2.4 retrievalReasoningEffort (可选)
控制检索推理的计算强度。

| 参数 | 类型 | 可选值 | 说明 |
|------|------|--------|------|
| kind | string | "low", "medium", "high" | 推理强度级别 |

- **low**: 最快响应，适用于简单查询
- **medium**: 平衡模式，适用于一般查询
- **high**: 最高质量，适用于复杂查询

### 2.5 includeActivity (可选)
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| includeActivity | boolean | false | 是否在响应中包含活动日志 |

### 2.6 outputMode (可选)
| 参数 | 类型 | 可选值 | 说明 |
|------|------|--------|------|
| outputMode | string | "answerSynthesis", "grounded" | 输出模式 |

- **answerSynthesis**: 合成完整答案
- **grounded**: 返回原始检索结果

================================================================================
## 3. knowledgeSourceParams - 知识源参数详解
================================================================================

这是控制知识源检索行为的关键参数数组。

### 3.1 基本参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| kind | string | 是 | 知识源类型: "searchIndex" |
| knowledgeSourceName | string | 是 | 知识源名称（在知识库中定义的名称）|

### 3.2 过滤参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| filterAddOn | string | null | 附加的 OData 过滤表达式，与知识源定义的过滤器组合使用 |

**filterAddOn 示例:**
- `"category eq 'electronics'"`
- `"price lt 100 and inStock eq true"`
- `"search.ismatch('wireless', 'tags')"`

### 3.3 引用参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| includeReferences | boolean | false | 是否在结果中包含引用信息 |
| includeReferenceSourceData | boolean | false | 是否包含引用的原始源数据 |

### 3.4 检索行为参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| alwaysQuerySource | boolean | false | 是否始终查询此知识源（即使系统判断不需要）|
| rerankerThreshold | number | 无（不过滤） | 重排序分数阈值，低于此分数的结果将被过滤 |

**rerankerThreshold 说明:**
- **默认行为**: 不设置时，不应用任何阈值过滤，返回所有语义重排序后的结果
- **值范围**: 0.0 - 4.0（语义重排序分数范围）
- **分数含义**:
  - 0.0 - 1.0: 相关性较低
  - 1.0 - 2.0: 中等相关性
  - 2.0 - 3.0: 较高相关性
  - 3.0 - 4.0: 高度相关
- **推荐设置**: 
  - 宽松过滤: 1.0 - 1.5（保留更多结果）
  - 中等过滤: 1.5 - 2.0
  - 严格过滤: 2.0+ （只保留高相关性结果）
- **注意**: 在 Azure Portal 上无法直接设置此参数，需要通过 REST API 请求体中指定

================================================================================
## 4. 完整请求示例
================================================================================

### 示例 1: 基本查询
```json
POST https://<service>.search.windows.net/knowledgebases('base-preview-test')/retrieve?api-version=2025-11-01-preview

{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "text": "hello world",
          "type": "text"
        }
      ]
    }
  ]
}
```

### 示例 2: 完整参数查询
```json
POST https://<service>.search.windows.net/knowledgebases('base-preview-test')/retrieve?api-version=2025-11-01-preview

{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "text": "hello world",
          "type": "text"
        }
      ]
    }
  ],
  "maxRuntimeInSeconds": 60,
  "maxOutputSize": 100000,
  "retrievalReasoningEffort": {
    "kind": "low"
  },
  "includeActivity": true,
  "outputMode": "answerSynthesis",
  "knowledgeSourceParams": [
    {
      "kind": "searchIndex",
      "knowledgeSourceName": "ks-preview-test",
      "filterAddOn": "foo eq bar",
      "includeReferences": true,
      "includeReferenceSourceData": true,
      "alwaysQuerySource": false,
      "rerankerThreshold": 2.1
    }
  ]
}
```

### 示例 3: 多知识源查询
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "text": "查找产品规格和用户手册",
          "type": "text"
        }
      ]
    }
  ],
  "maxRuntimeInSeconds": 120,
  "retrievalReasoningEffort": {
    "kind": "high"
  },
  "outputMode": "answerSynthesis",
  "knowledgeSourceParams": [
    {
      "kind": "searchIndex",
      "knowledgeSourceName": "product-specs-ks",
      "includeReferences": true,
      "rerankerThreshold": 2.0
    },
    {
      "kind": "searchIndex",
      "knowledgeSourceName": "user-manuals-ks",
      "includeReferences": true,
      "alwaysQuerySource": true
    }
  ]
}
```

================================================================================
## 5. 响应结构
================================================================================

```json
{
  "response": {
    "message": {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "合成的答案内容..."
        }
      ]
    }
  },
  "references": [
    {
      "docKey": "document-id",
      "sourceData": { ... },
      "chunkId": "chunk-001"
    }
  ],
  "activity": [
    {
      "type": "query",
      "knowledgeSource": "ks-preview-test",
      "query": "执行的查询",
      "resultCount": 5
    }
  ]
}
```

================================================================================
## 6. 错误代码
================================================================================

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 成功 |
| 400 | 请求格式错误或参数无效 |
| 401 | 未授权（API Key 无效）|
| 404 | 知识库或知识源不存在 |
| 408 | 请求超时（超过 maxRuntimeInSeconds）|
| 429 | 请求过多（速率限制）|
| 500 | 服务器内部错误 |

================================================================================
## 7. 最佳实践
================================================================================

1. **合理设置 maxRuntimeInSeconds**: 根据查询复杂度调整，简单查询用 30s，复杂查询用 60-120s
2. **使用 filterAddOn 优化性能**: 通过过滤减少检索范围，提高相关性
3. **调整 rerankerThreshold**: 从 1.5 开始测试，逐步调整到合适的值
4. **多知识源场景**: 使用 alwaysQuerySource 确保关键知识源被查询
5. **调试时启用 includeActivity**: 便于分析检索过程和优化参数

================================================================================
## 8. 注意事项
================================================================================

- 此 API 为 Preview 版本 (2025-11-01-preview)，可能会有变更
- 知识库和知识源需要预先创建和配置
- 确保索引已启用语义排序 (Semantic Ranker) 以获得最佳效果
- API Key 需要有足够的权限访问知识库