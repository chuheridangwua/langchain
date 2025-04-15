"""
语言模型初始化模块
"""

from langchain_openai import ChatOpenAI

def initialize_model():
    """初始化大语言模型，启用流式输出"""
    try:
        # 初始化大语言模型 (LLM)，启用流式输出
        llm = ChatOpenAI(
            model="deepseek-v3-250324",  # 使用DeepSeek的大模型
            openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",  # API密钥
            openai_api_base="https://ark.cn-beijing.volces.com/api/v3",  # API基础URL
            
            streaming=True,  # 启用流式输出
            temperature=0.7,  # 设置温度参数
            max_tokens=None,  # 不限制最大输出token数
        )

        return llm
    except Exception as e:
        print(f"模型初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise 