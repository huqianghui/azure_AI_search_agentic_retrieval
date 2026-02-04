# Azure Function 部署成功！

## 部署信息

✅ **Function App名称**: `azure-ai-search-split-custom-skill`
✅ **函数名称**: `page_content_split_http_trigger`
✅ **部署状态**: 成功

## 获取Function Key（重要）

### 方法1: 使用Azure CLI

```bash
az functionapp function keys list \
  --name azure-ai-search-split-custom-skill \
  --function-name page_content_split_http_trigger \
  --resource-group <your-resource-group-name> \
  --query "default" -o tsv
```

### 方法2: 在Azure Portal中获取

1. 访问 [Azure Portal](https://portal.azure.com)
2. 找到你的Function App: `azure-ai-search-split-custom-skill`
3. 点击左侧菜单 **Functions** → **page_content_split_http_trigger**
4. 点击 **Function Keys**
5. 复制 **default** key的值

### 方法3: 在VS Code中获取

1. 打开VS Code的Azure扩展
2. 找到 **Function App** → `azure-ai-search-split-custom-skill`
3. 展开 **Functions** → `page_content_split_http_trigger`
4. 右键点击 → **Copy Function Url**（包含key）

## Function URL格式

```
https://azure-ai-search-split-custom-skill.azurewebsites.net/api/page_content_split_http_trigger?code=YOUR_FUNCTION_KEY
```

## 测试云端函数

### 使用test_skill_azure.http文件

1. 打开 `test_skill_azure.http` 文件
2. 替换文件中的 `YOUR_FUNCTION_KEY` 为你获取的实际Function Key
3. 点击 **Send Request** 进行测试

### 使用curl命令

```bash
curl -X POST \
  "https://azure-ai-search-split-custom-skill.azurewebsites.net/api/page_content_split_http_trigger?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "values": [
      {
        "recordId": "r1",
        "data": {
          "page_content": "id:5000\n\nquestion: Test\n\nanswer: Test answer"
        }
      }
    ]
  }'
```

## 在Azure AI Search Skillset中配置

在你的skillset中添加custom skill：

```json
{
  "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
  "name": "page_content_split",
  "description": "Split page_content into id, question, and answer",
  "context": "/document",
  "uri": "https://azure-ai-search-split-custom-skill.azurewebsites.net/api/page_content_split_http_trigger?code=YOUR_FUNCTION_KEY",
  "httpMethod": "POST",
  "timeout": "PT30S",
  "batchSize": 10,
  "degreeOfParallelism": null,
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
      "targetName": "extracted_question"
    },
    {
      "name": "answer",
      "targetName": "extracted_answer"
    }
  ],
  "httpHeaders": {}
}
```

## 监控和日志

### 查看实时日志

```bash
func azure functionapp logstream azure-ai-search-split-custom-skill
```

### 在Azure Portal查看日志

1. 进入Function App
2. 点击 **Monitor** → **Logs**
3. 或使用 **Application Insights** 查看详细的性能和错误日志

## 下一步

1. ✅ 获取Function Key
2. ✅ 使用 `test_skill_azure.http` 测试云端函数
3. ✅ 将custom skill添加到你的Azure AI Search skillset
4. ✅ 更新indexer以使用新的skillset
5. ✅ 运行indexer并验证结果

## 故障排除

### 如果遇到401错误
- 检查Function Key是否正确
- 确保URL中包含 `?code=YOUR_FUNCTION_KEY`

### 如果遇到500错误
- 查看Function App的日志
- 检查函数代码是否有错误
- 验证输入数据格式是否正确

### 查看详细错误
```bash
# 查看最近的日志
az webapp log tail --name azure-ai-search-split-custom-skill --resource-group <your-rg>
```
