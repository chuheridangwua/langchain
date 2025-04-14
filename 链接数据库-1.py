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

# 引入langchain openai
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    # model='deepseek/deepseek-chat:free', 
    model="deepseek/deepseek-chat-v3-0324:free",
    openai_api_key="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",
    openai_api_base="https://openrouter.ai/api/v1",
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

# 测试连接
# print(db.get_usable_table_names())
# print(db.run('SELECT * FROM users;'))

# 直接使用大模型和数据库整合（生成sql语句，不执行）
# test_chain = create_sql_query_chain(model, db)
# print(test_chain.invoke({'question': '有多少用户'}))


answer_prompt = PromptTemplate.from_template(
    """给定以下用户问题、SQL语句和SQL执行后的结果，回答用户问题
    Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    回答:
    """
)

# 执行SQL语句工具，正确初始化
execute_sql_tool = QuerySQLDatabaseTool(db=db)

# 生成sql语句工具
generate_sql_tool = create_sql_query_chain(model, db)

chain = (
    RunnablePassthrough.assign(
        query = generate_sql_tool  
    ).assign(
        result = itemgetter('query') | execute_sql_tool
    ) | answer_prompt | model | StrOutputParser()
)

response = chain.invoke({'question': '有多少用户'})
print(response)










