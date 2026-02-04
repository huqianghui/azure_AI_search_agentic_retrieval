# Azure AI Search Custom Skill - Page Content Split

这是一个用于Azure AI Search的自定义技能（Custom Skill），基于Azure Functions实现。

## 功能说明

此技能接收Azure AI Search的标准请求格式，处理每条记录，并返回符合Azure AI Search要求的响应格式。

## 本地测试

### 1. 启动函数

```bash
func start
```

函数将在 `http://localhost:7071` 启动。

### 2. 测试请求

使用curl测试：

```bash
curl -X POST http://localhost:7071/api/page_content_split_http_trigger \
  -H "Content-Type: application/json" \
  -d @test_skill.json
```

或者使用Python测试：

```python
import requests
import json

url = "http://localhost:7071/api/page_content_split_http_trigger"

payload = {
    "values": [
        {
            "recordId": "r1",
            "data": {
                "name": "World"
            }
        }
    ]
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### 3. 期望的响应格式

```json
{
  "values": [
    {
      "recordId": "r1",
      "data": {
        "greeting": "Hello, World"
      },
      "errors": [],
      "warnings": []
    }
  ]
}
```

## 在Azure AI Search中集成

### Skillset定义示例

```json
{
    "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
    "description": "Page content split custom skill",
    "uri": "https://[your-function-app].azurewebsites.net/api/page_content_split_http_trigger?code=[your-function-key]",
    "batchSize": 10,
    "context": "/document",
    "inputs": [
        {
            "name": "name",
            "source": "/document/content"
        }
    ],
    "outputs": [
        {
            "name": "greeting",
            "targetName": "processedContent"
        }
    ]
}
```

## 自定义处理逻辑

在 `function_app.py` 中的 `process_record()` 函数里实现你的自定义逻辑：

```python
def process_record(record: Dict[str, Any]) -> Dict[str, Any]:
    try:
        record_id = record.get('recordId')
        data = record.get('data', {})
        
        # 获取输入数据
        name = data.get('name', 'Unknown')
        
        # 在这里实现你的处理逻辑
        # 例如：文本分割、内容提取、数据转换等
        result = {
            'greeting': f'Hello, {name}'
        }
        
        return {
            'recordId': record_id,
            'data': result,
            'errors': [],
            'warnings': []
        }
        
    except Exception as e:
        return {
            'recordId': record.get('recordId'),
            'data': {},
            'errors': [{'message': str(e)}],
            'warnings': []
        }
```

## 部署到Azure

```bash
# 登录Azure
az login

# 创建资源组
az group create --name myResourceGroup --location eastus

# 创建存储账户
az storage account create --name mystorageaccount --resource-group myResourceGroup

# 创建Function App
az functionapp create --resource-group myResourceGroup \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name myFunctionApp \
  --storage-account mystorageaccount

# 部署代码
func azure functionapp publish myFunctionApp
```

## 错误处理

此技能包含完善的错误处理机制：
- 无效的请求格式会返回400错误
- 处理单条记录时的错误会记录在该记录的errors数组中
- 未捕获的异常会返回500错误

## 日志

使用Azure Application Insights查看日志：
- 在Azure门户中找到你的Function App
- 导航到"监视" > "Application Insights"
- 查看日志和性能指标
