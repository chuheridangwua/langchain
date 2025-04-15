# LangChain 智能聊天代理系统

这是一个基于LangChain框架构建的高级智能聊天代理系统。该系统能够通过大语言模型与用户进行自然语言交互，并根据需要使用各种工具来辅助回答，包括网络搜索、文件操作、代码执行和数据库查询等多种功能。

## 项目结构

```
langchain-app/
│
├── main.py                # 主程序入口
├── sessions/              # 会话历史存储目录
├── src/                   # 源代码目录
│   ├── __init__.py        # 包初始化文件
│   ├── chat.py            # 交互式对话模块
│   ├── models/            # 语言模型相关模块
│   │   ├── __init__.py
│   │   └── llm.py         # 语言模型初始化和配置
│   ├── agents/            # 代理相关模块
│   │   ├── __init__.py
│   │   └── agent.py       # 代理创建和管理
│   ├── prompts/           # 提示词模板模块
│   │   ├── __init__.py
│   │   └── agent_prompts.py # 代理提示词模板
│   ├── tools/             # 工具函数模块
│   │   ├── __init__.py    # 工具导出
│   │   ├── base_tools.py  # 基础工具定义
│   │   ├── tavily_tools.py # 联网搜索工具
│   │   ├── duckduckgo_tools.py # DuckDuckGo搜索工具
│   │   ├── python_code_tools.py # Python代码执行工具
│   │   ├── file_tools.py  # 文件操作工具
│   │   ├── database_tools.py # 数据库操作工具
│   │   └── local_kb_tools.py # 本地知识库工具
│   └── utils/             # 工具函数模块
│       ├── __init__.py
│       ├── callbacks.py   # 回调处理器和日志
│       └── session.py     # 会话管理功能
└── README.md              # 项目说明文件
```

## 系统核心功能

1. **智能对话**
   - 基于大语言模型的自然语言交互
   - 支持流式输出响应（打字机效果）
   - 上下文感知对话，保持对话连贯性

2. **工具集成**
   - **网络搜索工具** - 支持Tavily和DuckDuckGo搜索引擎，获取实时信息
   - **Python代码执行** - 动态生成和执行Python代码
   - **文件操作工具** - 读写文件、目录管理、文件信息获取等
   - **数据库工具** - SQL查询执行、表结构获取、AI辅助数据库查询
   - **知识库工具** - 本地知识库检索、网站内容添加到知识库

3. **会话管理系统**
   - 自动保存对话历史，支持JSON格式持久化
   - 会话恢复功能，可从之前的对话继续
   - 查看历史记录命令，支持模糊匹配
   - 多会话管理，可在不同会话间切换

4. **系统功能**
   - 日志记录和错误处理
   - 可扩展的插件化架构
   - 内置防止无限循环的安全机制

## 环境要求

- Python 3.8+
- 依赖库:
  - langchain
  - langchain_openai
  - langchain_community
  - tavily-python
  - duckduckgo-search (可选)
  - beautifulsoup4 (用于网页内容处理)
  - sqlite3 (数据库操作)
  - datetime, json, os, re等标准库

## 安装与配置

1. 克隆代码库:
   ```bash
   git clone <repository-url> langchain-app
   cd langchain-app
   ```

2. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

3. 环境变量配置:
   - 创建`.env`文件并添加以下内容:
   ```
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ```

## 如何使用

1. 启动程序:
   ```bash
   python main.py
   ```

2. 会话管理:
   - 启动时，系统会检查是否有保存的会话
   - 可选择恢复之前的会话或创建新会话
   - 聊天历史会自动保存到`sessions`目录

3. 对话命令:
   - `history` - 查看当前会话的历史对话记录（支持拼写错误，如`histroy`）
   - `exit`, `quit`, `q`, `退出` - 退出程序

4. 使用工具示例:
   - 搜索信息：*"请帮我查一下今天的国际新闻"*
   - 代码执行：*"帮我写一个计算斐波那契数列的Python函数"*
   - 文件操作：*"列出当前目录下的所有文件"*
   - 数据库查询：*"查询用户表中年龄大于30的用户"*
   - 知识库访问：*"在我的知识库中查找关于人工智能的信息"*

## 扩展开发

### 添加新工具

1. 在`src/tools/`目录下创建新的工具文件
2. 使用`@tool`装饰器定义工具函数:

```python
from langchain.tools import Tool, tool

@tool(description="工具功能描述")
def new_tool(parameter: str) -> str:
    """新工具的功能描述"""
    # 工具实现逻辑
    return f"工具结果: {parameter}"
```

3. 在`src/tools/__init__.py`中导出新工具
4. 在`src/agents/agent.py`中将新工具添加到工具列表中

### 修改代理提示词

1. 在`src/prompts/agent_prompts.py`中定义新的提示词模板
2. 更新`get_agent_prompt`函数返回新的提示词

## 高级特性

### 知识库管理

系统支持本地知识库，可以添加和检索文档:

```python
# 添加网站到知识库
add_website_to_knowledge_base.invoke({"url": "https://example.com"})

# 从知识库检索信息
result = retrieve_from_knowledge_base.invoke({"query": "查询内容"})
```

### 数据库操作

系统支持SQL数据库查询和AI辅助的数据库操作:

```python
# 获取数据库表结构
table_info = get_table_structure.invoke({"table_name": "users"})

# AI辅助数据库查询
result = ai_query_database.invoke({
    "question": "有多少用户的年龄超过30岁？"
})
```

## 常见问题

1. **Q: 如何更改语言模型?**  
   A: 在`src/models/llm.py`中修改`initialize_model`函数。

2. **Q: 会话数据存储在哪里?**  
   A: 会话数据以JSON格式存储在`sessions`目录中。

3. **Q: 如何添加自定义知识库?**  
   A: 使用`local_kb_tools.py`中的工具函数添加文档到知识库。

4. **Q: 如何限制代理的工具使用?**  
   A: 在`src/agents/agent.py`中的`create_agent`函数中修改工具列表。

5. **Q: 为什么列出目录内容时要使用"./"而不是"."?**  
   A: 当使用`list_directory`工具列出当前目录内容时，请优先使用`"./"`而非单独的`"."`。在某些环境中，使用单独的点号作为当前目录可能无法被正确识别。系统已进行优化，将自动把`"."`转换为`"./"`以确保兼容性。

## 开发路线图

- [ ] 支持更多语言模型
- [ ] 添加Web界面
- [ ] 增加多用户支持
- [ ] 引入语音交互
- [ ] 添加图像处理能力

## 许可证

本项目使用MIT许可证 - 详情见LICENSE文件 