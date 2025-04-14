# 引入langchain聊天场景的提示词模板
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_core.runnables import RunnablePassthrough
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import chat_agent_executor 
# 引入langchain openai
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    # model='deepseek/deepseek-chat:free', 
    model="deepseek-v3-250324",  # 使用DeepSeek的大模型
    openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",  # API密钥
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",  # API基础URL
    streaming=True
    # max_tokens=1024
)

# PostgreSQL数据库配置
HOSTNAME = '127.0.0.1'
PORT = '5432'  # PostgreSQL默认端口是5432
DATABASE = '0414'
USERNAME = 'postgres'  # PostgreSQL默认用户
PASSWORD = 'root'  # 你的PostgreSQL密码

# PostgreSQL连接URL
PG_URI = f'postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}'

db = SQLDatabase.from_uri(PG_URI)

# 创建工具包
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

#使用agent完整整个数据库的整合
system_prompt = """
您是一个被设计用来与SQL数据库交互的代理。
给定一个输入问题，创建一个语法正确的SQL语句并执行，然后查看查询结果并返回答案。
除非用户指定了他们想要获得的示例的具体数量，否则始终将SQL查询限制为最多10个结果。
你可以按相关列对结果进行排序，以返回数据库中最匹配的数据。
您可以使用与数据库交互的工具。
在执行查询之前，你必须仔细检查。
如果在执行查询时出现错误，请重写查询并重试。
不要对数据库做任何DML语句(插入，更新，删除等)。

首先，你应该查看数据库中的表，看看可以查询什么。不要跳过这一步。
然后查询最相关的表的模式。
"""

# 创建agent执行器 - 将system_prompt作为prompt参数传递
agent_executor = chat_agent_executor.create_react_agent(model, tools, prompt=system_prompt)

response = agent_executor.invoke({'messages': [HumanMessage(content="2025-04-14谁用了什么书")]})
print(response)




