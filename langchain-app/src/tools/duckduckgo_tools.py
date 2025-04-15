"""
DuckDuckGo搜索工具模块 - 提供联网搜索功能，无需API密钥
"""

from langchain.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

@tool(description="使用DuckDuckGo进行网络搜索，返回相关搜索结果。适用于快速获取网络信息。")
def duckduckgo_search(query: str) -> str:
    """使用DuckDuckGo进行网络搜索
    
    Args:
        query: 搜索查询字符串
        
    Returns:
        str: 搜索结果
    """
    # 创建搜索引擎包装器
    search = DuckDuckGoSearchAPIWrapper(
        max_results=5  # 返回5条最相关的结果
    )
    
    # 执行搜索并返回结果
    results = search.run(query)
    
    # 如果没有结果，给出友好提示
    if not results or results.strip() == "":
        return "未找到相关搜索结果，请尝试调整搜索关键词。"
    
    return results 