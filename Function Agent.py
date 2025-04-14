from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool

# 1. 初始化 LLM（豆包模型）
llm = ChatOpenAI(
    model="doubao-lite-32k-240828",
    openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
)

# 2. 定义 Tavily 搜索工具
def create_search_tool():
    return TavilySearchResults(
        name="tavily_search_results_json",
        max_results=3,
        tavily_api_key="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"
    )

# 3. 定义一个简单计算器工具（结构化函数调用兼容）
@tool
def calculator(expression: str) -> str:
    """用于计算数学表达式，如 '2 + 3 * 4'"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"错误: {str(e)}"

# 4. 准备工具列表
tools = [
    create_search_tool(),
    calculator
]

# 5. Prompt Template（Function Agent 通常搭配 function-friendly prompt）
agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """
你是一个联网助手，优先使用工具获取最新和准确的数据。
如果你无法确认答案是否准确，请调用合适的工具来查找。
"""),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])


# 6. 创建 Function Agent
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=agent_prompt)

# 7. 创建 AgentExecutor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    return_intermediate_steps=True,
    handle_parsing_errors=True
)

# 8. 测试
query = "查一下北京的天气"
response = agent_executor.invoke({"input": query})

print("\n✅ 最终结果：", response["output"])
