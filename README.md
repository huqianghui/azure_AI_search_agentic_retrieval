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
func start
```

访问: `http://localhost:7071`

### 2. 配置 Azure AI Search

根据需求选择配置文件：
- `config/RAG/` - 用于向量检索和 RAG
- `config/keywords/` - 用于关键词检索
- `config/non-split-RAG/` - 用于不分块的 RAG

### 3. 运行示例 Notebook

```bash
cd azure-search-classic-rag
jupyter notebook
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
