# 引入langchain聊天场景的提示词模板
import os
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnablePassthrough

# 引入langchain openai  
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="deepseek/deepseek-chat-v3-0324:free",
    openai_api_key="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",
    openai_api_base="https://openrouter.ai/api/v1",
)

documents=[
    Document(page_content="我是一只名叫旺财的金毛犬，今年3岁，喜欢玩飞盘和散步。",metadata={"source":"旺财"}),
    Document(page_content="我是一只名叫咪咪的波斯猫，今年2岁，喜欢晒太阳和追逐玩具鼠。",metadata={"source":"咪咪"}),
    Document(page_content="我是一只名叫花花的兔子，今年1岁，喜欢吃胡萝卜和在草地上蹦跳。",metadata={"source":"花花"}),
]

# 实例化向量数据库
vector_store = Chroma.from_documents(documents, embedding=HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-zh-v1.5"
))

# 创建检索器
retriever = vector_store.as_retriever(search_kwargs={"k": 1})

# 创建提示词模板
template = """
使用提供的上下文信息回答问题：
{question}

上下文：
{context}
"""

prompt = ChatPromptTemplate.from_template(template)

# 定义一个函数来格式化检索结果
def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

# 构建RAG链
chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | prompt
    | model
)

# 执行查询
response = chain.invoke("旺财喜欢干什么？")
print(response)






