# 引入langchain聊天场景的提示词模板
from langchain_community.tools.tavily_search import TavilySearchResults

# 引入langchain openai  
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import chat_agent_executor
from langchain_core.messages import HumanMessage
from langchain.agents import AgentExecutor

model = ChatOpenAI(
    # model="deepseek/deepseek-chat-v3-0324:free",
    # model="google/gemini-2.5-pro-exp-03-25:free",
    # openai_api_key="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",
    # openai_api_base="https://openrouter.ai/api/v1",
    
    model="doubao-lite-32k-240828",
    openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",
)

# result = model.invoke("济南天气怎么样")
# print(result)

search = TavilySearchResults(max_results=3,tavily_api_key="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")

# result = search.invoke("济南天气怎么样")
# print(result)

tools = [search]

# model_with_tools = model.bind_tools(tools)
# result = model_with_tools.invoke("济南天气怎么样")
# print(result)

#创建代理
agent_executor = chat_agent_executor.create_tool_calling_executor(model,tools)

    
response = agent_executor.invoke({"messages":[HumanMessage(content="济南天气怎么样")]})
print(response)
# print(response["messages"][2].content)






