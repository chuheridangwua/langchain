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
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 导入文本分割器
from langchain_chroma import Chroma  # 导入更新后的Chroma库
from langchain_huggingface import HuggingFaceEmbeddings  # 导入HuggingFace嵌入模型
from langchain_community.document_loaders import WebBaseLoader  # 导入网页加载器
from pydantic import BaseModel, Field
from typing import Optional

model = ChatOpenAI(
    model="deepseek-v3-250324",  # 使用DeepSeek的大模型
    openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",  # API密钥
    openai_api_base="https://ark.cn-beijing.volces.com/api/v3",  # API基础URL
    streaming=True,  # 启用流式输出
)

# # 初始化嵌入模型，用于将文本转换为向量
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-zh-v1.5"  # 使用北京智源的中文嵌入模型
)

# 创建本地知识库的目录
persist_dir = "chroma_data_dir"

# # 百度百科链接
# urls = [
#     "https://baike.baidu.com/item/%E7%91%9E%E5%B9%B8%E5%92%96%E5%95%A1/64137312?fromtitle=%E7%91%9E%E5%B9%B8&fromid=63866093&fromModule=lemma_search-box",
#     "https://baike.baidu.com/item/%E5%BA%93%E8%BF%AA%E5%92%96%E5%95%A1/61942947?fromModule=search-result_lemma",
#     "https://baike.baidu.com/item/%E8%9C%9C%E9%9B%AA%E5%86%B0%E5%9F%8E/8822463",
#     "https://baike.baidu.com/item/%E9%9C%B8%E7%8E%8B%E8%8C%B6%E5%A7%AC?fromModule=lemma_search-box"
# ]

# # 加载网页数据
# print("正在加载百度百科数据，请稍候...")
# loader = WebBaseLoader(
#     web_paths=urls,
#     encoding="utf-8",  # 明确指定编码，确保中文正确处理
# )

# # 执行文档加载
# docs = loader.load()
# print(f"成功加载 {len(docs)} 个百度百科文档")

# # 检查是否成功加载了所有链接的内容
# for i, doc in enumerate(docs):
#     print(f"文档 {i+1} 的URL: {doc.metadata.get('source', '未知')}")
#     print(f"文档 {i+1} 内容的前100个字符: {doc.page_content[:100]}...")
    
# # 初始化文本分割器，将长文档分割成小块
# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,  # 每块文本大约1000个字符
#     chunk_overlap=200,  # 相邻块之间重叠200个字符，保持上下文连贯性
# )

# # 执行文档分割
# split_docs = splitter.split_documents(docs)
# print(f"文档已分割为 {len(split_docs)} 个小块")

# # 打印分割后的文档信息，确认所有链接的内容都被处理
# source_counts = {}
# for doc in split_docs:
#     source = doc.metadata.get('source', '未知')
#     if source in source_counts:
#         source_counts[source] += 1
#     else:
#         source_counts[source] = 1

# print("各来源文档的分块数量:")
# for source, count in source_counts.items():
#     print(f"{source}: {count}个分块")

# # 创建向量存储
# vector_store = Chroma.from_documents(
#     documents=split_docs,
#     embedding=embedding_model,
#     persist_directory=persist_dir
# )

# # 确认向量存储中的文档数量
# print(f"向量存储中共有 {vector_store._collection.count()} 个文档向量")


# 加载本地知识库
vector_store = Chroma(persist_directory=persist_dir, embedding_function=embedding_model)

# # 测试
# retriever = vector_store.similarity_search("蜜雪")  
# print(retriever)

system = """
您是关键词提取专家。
请从用户问题中提取核心关键词，以便在知识库中进行高效检索。
不需要完整句子，只需返回最相关的关键词列表。

例如：
用户问题：瑞幸是干什么的？
回复：瑞幸

用户问题：瑞幸咖啡的创始人是谁？
回复：瑞幸咖啡 创始人
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "{question}")
])


class Search(BaseModel):
    """定义了一个数据模型，用于搜索视频内容"""
    #内容的相似性和发布年份
    query: str = Field(default=None, description='搜索内容的相似性查询')
    # publish_year: Optional[int] = Field(default=None, description='视频发布的年份')

chain = {'question':RunnablePassthrough()} | prompt | model


# 定义检索函数
def retrieve_from_knowledge_base(query, top_k=3):
    """
    从知识库中检索与查询相关的文档
    
    参数:
        query: 用户查询字符串
        top_k: 返回的最相关文档数量
        
    返回:
        检索到的文档列表
    """
    # 使用chain提取关键词
    keywords_response = chain.invoke(query)
    # 从AIMessage对象中提取内容
    keywords = keywords_response.content
    print(f"从查询中提取的关键词: {keywords}")
    
    # 使用关键词进行相似性搜索
    retrieved_docs = vector_store.similarity_search(keywords, k=top_k)
    
    print(f"检索到 {len(retrieved_docs)} 个相关文档")
    return retrieved_docs

# 定义RAG问答系统
def rag_qa_system(query):
    """
    基于检索增强生成的问答系统
    
    参数:
        query: 用户问题
        
    返回:
        生成的回答
    """
    # 从知识库检索相关文档
    docs = retrieve_from_knowledge_base(query)
    
    # 构建提示模板
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", """
        您是一个专业的知识助手。请基于提供的文档内容回答用户的问题。
        如果文档中没有相关信息，请诚实地告知用户您不知道，不要编造信息。
        请确保回答准确、全面且易于理解。
        """),
        ("human", "请回答以下问题，基于这些文档内容：\n\n{context}\n\n问题: {question}")
    ])
    
    # 准备上下文
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # 生成回答
    response = model.invoke(qa_prompt.format(context=context, question=query))
    
    return response.content

# 简单的交互式界面
def interactive_qa():
    """提供简单的交互式问答界面"""
    print("知识库问答系统已启动。输入'退出'结束对话。")
    
    while True:
        query = input("\n请输入您的问题: ")
        if query.lower() in ['退出', 'exit', 'quit']:
            print("感谢使用，再见！")
            break
            
        print("\n正在思考...")
        answer = rag_qa_system(query)
        print(f"\n回答: {answer}")

if __name__ == "__main__":
    print("欢迎使用本地知识库问答系统！")
    print("系统正在初始化...")
    interactive_qa()








