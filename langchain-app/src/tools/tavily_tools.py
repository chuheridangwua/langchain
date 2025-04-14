"""
Tavily搜索工具模块 - 提供联网搜索功能
"""

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool

@tool(description="使用Tavily进行网络搜索，返回最相关的3条搜索结果，每条结果包含标题、URL和摘要信息。")
def search_tool(query: str) -> str:
    """使用Tavily进行网络搜索
    
    Args:
        query: 搜索查询字符串
        
    Returns:
        str: 搜索结果
    """
    search = TavilySearchResults(
        name="search_tool",
        max_results=3,
        tavily_api_key="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"
    )
    
    return search.run(query)