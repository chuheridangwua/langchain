# 工具模块

本目录包含了应用程序使用的各种工具函数，这些工具可以被语言模型调用以完成特定任务。

## 可用工具

1. **基础工具** (base_tools.py)
   - `get_current_time`: 获取当前系统时间和日期

2. **搜索工具** (tavily_tools.py)
   - `search_tool`: 使用Tavily搜索引擎进行网络搜索

3. **Python代码工具** (python_code_tools.py)
   - `generate_and_execute_code`: 生成并执行Python代码
   - `execute_python_code`: 执行用户提供的Python代码

4. **DuckDuckGo搜索工具** (duckduckgo_tools.py)
   - `duckduckgo_search`: 使用DuckDuckGo搜索引擎进行网络搜索

5. **本地知识库工具** (local_kb_tools.py)
   - `retrieve_from_knowledge_base`: 从本地知识库中检索相关信息
   - `get_knowledge_base_info`: 获取本地知识库状态信息

## 如何添加新工具

创建一个新的工具模块文件，使用`@tool`装饰器定义工具函数，然后在`__init__.py`中导入并添加到`__all__`列表中。