from langchain.schema.runnable import RunnableMap
from langchain_core.prompts import ChatPromptTemplate
from langserve import RemoteRunnable

# # 初始化远程Runnable
# openai = RemoteRunnable("http://localhost:8000/openai/")

# # 创建聊天提示模板
# prompt = ChatPromptTemplate.from_messages([
#     ("system", "你是一个喜欢写故事的助手"),
#     ("user", "写一个故事，主题是: {topic}")
# ])

# # 定义自定义链
# chain = prompt | RunnableMap({
#     "openai": openai
# })

# # 同步调用并打印结果
# print("同步调用/openai/invoke结果")
# response = chain.invoke({"topic": "猫"})
# print(response)


# 初始化远程Runnable
openai_str_parser = RemoteRunnable("http://localhost:8000/openai_ext/")

# 创建链
chain_str_parser =  RunnableMap({
    "openai": openai_str_parser
})

# 测试字符串解析器
# print("测试StrOutputParser")
# response = chain_str_parser.invoke({"topic": "猫"})
# print(response)

# 流式调用测试
print("流式调用/openai/stream结果")
for chunk in chain_str_parser.stream({"topic": "狗"}):
    print(chunk["openai"].content, end="|", flush=True)