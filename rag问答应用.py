"""
RAG(检索增强生成)问答应用程序
该程序使用LangChain框架构建一个简单的RAG系统，从网页数据中检索信息并与用户进行交互式对话
"""

# ———————————————————————————————————————————————— 导入必要的库和模块 ————————————————————————————————————————————————
from langchain_openai import ChatOpenAI  # 导入OpenAI聊天模型接口
from langchain_community.document_loaders import WebBaseLoader  # 导入网页加载器
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 导入文本分割器
from langchain_chroma import Chroma  # 导入更新后的Chroma库
from langchain_huggingface import HuggingFaceEmbeddings  # 导入HuggingFace嵌入模型
from langchain.prompts import ChatPromptTemplate  # 导入聊天提示模板
from langchain_core.prompts import MessagesPlaceholder  # 导入消息占位符
from langchain.chains.history_aware_retriever import create_history_aware_retriever  # 导入历史感知检索器创建函数
from langchain_community.chat_message_histories import ChatMessageHistory  # 导入聊天历史记录
from langchain.chains.combine_documents import create_stuff_documents_chain  # 导入文档组合链创建函数
from langchain.chains.retrieval import create_retrieval_chain  # 导入检索链创建函数
from langchain_core.runnables import RunnableWithMessageHistory  # 导入带消息历史记录的可运行对象


# ———————————————————————————————————————————————— 初始化模型 ————————————————————————————————————————————————
def initialize_models():
    """初始化大语言模型和嵌入模型"""
    # 初始化大语言模型 (LLM)，启用流式输出
    llm = ChatOpenAI(
        model="deepseek-v3-250324",  # 使用DeepSeek的大模型
        openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",  # API密钥
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3",  # API基础URL
        streaming=True,  # 启用流式输出
    )
    
    # 初始化嵌入模型，用于将文本转换为向量
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-zh-v1.5"  # 使用北京智源的中文嵌入模型
    )
    
    return llm, embedding_model


# ———————————————————————————————————————————————— 数据加载和处理 ————————————————————————————————————————————————
def load_and_process_data(embedding_model):
    """加载网页数据并处理成向量存储"""
    print("正在加载和处理数据，请稍候...")
    
    # 加载网页数据
    loader = WebBaseLoader(
        web_paths=["https://baike.baidu.com/item/%E7%91%9E%E5%B9%B8%E5%92%96%E5%95%A1/64137312?fromtitle=%E7%91%9E%E5%B9%B8&fromid=63866093&fromModule=lemma_search-box"],  # 百度百科瑞幸咖啡页面
        encoding="utf-8",  # 明确指定编码，确保中文正确处理
    )
    
    # 执行文档加载
    docs = loader.load()
    
    # 初始化文本分割器，将长文档分割成小块
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 每块文本大约500个字符
        chunk_overlap=100,  # 相邻块之间重叠100个字符，保持上下文连贯性
    )
    
    # 执行文档分割
    splits = splitter.split_documents(docs)
    
    # 创建向量存储，将文档块转换为向量并存储
    vector_store = Chroma.from_documents(
        documents=splits,  # 分割后的文档块
        embedding=embedding_model,  # 使用的嵌入模型
    )
    
    # 创建检索器，用于从向量存储中检索相关文档
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})  # k=3表示每次检索返回3个最相关的文档块
    
    return retriever


# ———————————————————————————————————————————————— 创建RAG链 ————————————————————————————————————————————————
def create_rag_chain(llm, retriever):
    """创建RAG问答链"""
    
    # 创建提示词模板，用于构建向LLM发送的提示
    system_prompt = """
    您是一个问答任务助手。
    请使用以下检索到的上下文信息来回答问题。
    如果您不知道答案，请直接说明您不知道。
    
     检索到的上下文信息:
     {context}
    """
    
    # 使用ChatPromptTemplate创建一个提示模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("user", "{input}")
    ])
    
    # 使用LangChain的链式API构建RAG问答链
    answer_chain = create_stuff_documents_chain(llm, prompt)
    
    # 子链的提示模板 - 用于将上下文相关问题转换为独立问题
    contextualize_q_system_prompt = """给定聊天历史记录和最新的用户问题，
    该问题可能引用了聊天历史中的上下文。
    请将其重新表述为一个独立的问题，使其在没有聊天历史的情况下也能被理解。
    不要回答问题，只需在必要时重新表述，否则按原样返回。"""
    
    # 创建历史感知提示模板
    retriever_history_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("user", "{input}")
    ])
    
    # 创建历史感知检索器
    history_aware_retriever = create_history_aware_retriever(
        llm,
        retriever,
        retriever_history_prompt
    )
    
    # 创建检索链，组合历史感知检索器和问答链
    rag_chain = create_retrieval_chain(
        history_aware_retriever,
        answer_chain
    )
    
    return rag_chain


# ———————————————————————————————————————————————— 会话管理 ————————————————————————————————————————————————
def setup_conversation_chain(rag_chain):
    """设置带有会话历史的对话链"""
    
    # 保存问答的历史记录
    conversation_store = {}
    
    # 获取会话历史的函数
    def get_session_history(session_id):
        if session_id not in conversation_store:
            conversation_store[session_id] = ChatMessageHistory()
        return conversation_store[session_id]
    
    # 创建带有消息历史的可运行对象
    conversation_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        output_messages_key="answer",
        history_messages_key="chat_history",
    )
    
    return conversation_chain


# ———————————————————————————————————————————————— 流式输出处理函数 ————————————————————————————————————————————————
def stream_output(text):
    """模拟打字效果的流式输出函数
    
    Args:
        text: 要输出的文本
    """
    for char in text:
        print(char, end='', flush=True)
    print()  # 输出完成后换行


# ———————————————————————————————————————————————— 交互式对话 ————————————————————————————————————————————————
def interactive_conversation(conversation_chain):
    """进行交互式对话"""
    session_id = "user_session"  # 用户会话ID
    
    print("\n欢迎使用RAG问答系统！")
    print("输入问题开始对话，输入'退出'结束对话\n")
    
    while True:
        # 获取用户输入
        user_input = input("\n用户: ")
        
        # 检查是否退出
        if user_input.lower() in ['退出', 'exit', 'quit', 'q']:
            print("\n感谢使用RAG问答系统，再见！")
            break
        
        try:
            print("\nAI: ", end="", flush=True)
            
            # 使用stream方法获取流式输出
            for chunk in conversation_chain.stream(
                {"input": user_input}, 
                {"configurable": {"session_id": session_id}}
            ):
                if "answer" in chunk:
                    # 打印回答的内容
                    print(chunk["answer"], end="", flush=True)
            
            # 换行
            print()
            
        except Exception as e:
            print(f"\n发生错误: {e}")
            print("请尝试重新提问或检查网络连接")


# ———————————————————————————————————————————————— 主函数 ————————————————————————————————————————————————
def main():
    """主函数，执行完整的RAG对话应用流程"""
    # 初始化模型
    llm, embedding_model = initialize_models()
    
    # 加载和处理数据
    retriever = load_and_process_data(embedding_model)
    
    # 创建RAG链
    rag_chain = create_rag_chain(llm, retriever)
    
    # 设置对话链
    conversation_chain = setup_conversation_chain(rag_chain)
    
    # 开始交互式对话
    interactive_conversation(conversation_chain)


# 程序入口点
if __name__ == "__main__":
    main()
        

