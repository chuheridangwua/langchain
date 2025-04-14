"""
工具模块 - 包含所有可用工具的定义
"""

from langchain.tools import tool
import datetime

@tool(description="获取当前系统时间和日期")
def get_current_time() -> str:
    """获取当前系统时间和日期
    
    Returns:
        str: 当前日期和时间的格式化字符串
    """
    now = datetime.datetime.now()
    formatted_time = now.strftime("%Y年%m月%d日 %H:%M:%S")
    return f"当前时间是: {formatted_time}"

# 这里可以添加更多工具函数
# @tool
# def another_tool(parameter: str) -> str:
#     """另一个工具函数的描述"""
#     return f"工具处理结果: {parameter}" 