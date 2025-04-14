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
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import chat_agent_executor 
# 引入langchain openai
from langchain_openai import ChatOpenAI
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 导入文本分割器
from langchain_chroma import Chroma  # 导入更新后的Chroma库
from langchain_huggingface import HuggingFaceEmbeddings  # 导入HuggingFace嵌入模型
from langchain_community.document_loaders import WebBaseLoader  # 导入网页加载器
from pydantic import BaseModel, Field
from typing import List, Optional

model = ChatOpenAI(
    model="deepseek-v3-250324",  # 使用DeepSeek的大模型
    openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",  # API密钥
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",  # API基础URL
    streaming=False,  # 启用流式输出
)

# model = ChatOpenAI(
#     model="arliai/qwq-32b-arliai-rpr-v1:free",
#     openai_api_key="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",
#     openai_api_base="https://openrouter.ai/api/v1",
# )

# 初始化嵌入模型，用于将文本转换为向量
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-zh-v1.5"  # 使用北京智源的中文嵌入模型
)

# 人模型
class Person(BaseModel):
    name: Optional[str] = Field(default=None, description='表示人的名字')
    hair_color: Optional[str] = Field(default=None, description='头发颜色')
    height_in_meters: Optional[float] = Field(default=None, description='人的身高')
    
    
class ManyPerson(BaseModel):
    people: List[Person] = Field(default=None, description='表示人的列表')

# 结构化输出解析器（结合 Pydantic）
parser = JsonOutputParser(pydantic_schema=ManyPerson)

# 定义自定义提示以提供指令和任何其他上下文
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
你是一个专业的信息提取助手。
你需要从用户提供的自然语言中提取所有人物的信息，并以JSON格式返回。

你需要返回的JSON结构如下：
{{{{
  "people": [
    {{{{
      "name": "人名1",
      "hair_color": "头发颜色1",
      "height_in_meters": 身高1
    }}}},
    {{{{
      "name": "人名2",
      "hair_color": "头发颜色2", 
      "height_in_meters": 身高2
    }}}},
    ...
  ]
}}}}
提取每个人的以下字段信息：
- name：表示人的名字
- hair_color：头发颜色
- height_in_meters：人的身高

重要提示：
1. 文本中可能提到多个人，务必提取所有人的信息并放入people列表中
2. 如果存在相对身高描述（如"比某人高/矮多少"），请计算出实际身高值
3. 如果某项信息缺失，请将其值设为null
4. 只返回JSON，不要添加解释、自然语言、markdown标记或代码块
"""),
    ("human", "{question}")
])

# 构建链
chain = {'question': RunnablePassthrough()} | prompt | model | parser

# 调用测试
result = chain.invoke("我认识一个叫John的人，他身高1.8米，头发是棕色的。还有个叫Mary的人，比john高10厘米，头发的颜色和他一样。")
print(result)







