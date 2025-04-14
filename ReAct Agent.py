from langchain.agents import initialize_agent, AgentType
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain.tools import tool

# 1. 初始化 LLM 模型（豆包）
llm = ChatOpenAI(
    model="doubao-lite-32k-240828",
    openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
)

# 2. 创建 Tavily 搜索工具
def create_search_tool():
    return TavilySearchResults(
        name="tavily_search_results_json",
        max_results=3,
        tavily_api_key="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"
    )

# ✅ 你也可以自己定义其他工具
@tool
def calculator(expression: str) -> str:
    """计算简单的数学表达式，比如 '2 + 3 * 4'"""
    try:
        return str(eval(expression))
    except:
        return "计算失败"

# 3. 准备工具列表
tools = [
    create_search_tool(),
    calculator
]

# 4. 创建 ReAct Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
)

# 5. 测试输入
query = "今天星期几？"

# 6. 执行 agent
response = agent.invoke({"input": query})

print("\n🧠 最终输出：", response["output"])
