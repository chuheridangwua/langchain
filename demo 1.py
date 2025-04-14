# 引入langchain聊天场景的提示词模板
import os
from langchain_core.prompts import ChatPromptTemplate

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.prompts import MessagesPlaceholder

# 引入langchain openai
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    # model='deepseek/deepseek-chat:free', 
    model="deepseek/deepseek-chat-v3-0324:free",
    openai_api_key="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",
    openai_api_base="https://openrouter.ai/api/v1",
    streaming=True
    # max_tokens=1024

)

# 创建聊天提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的AI助手，用{language}回答用户的问题。"),
    MessagesPlaceholder(variable_name="my_msg")
])

# 创建处理链
chain = prompt | llm 


#保存聊天记录
store = {} #key:session_id,value:chat_history

# 获取会话历史记录
def get_session_history(session_id):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


do_message = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="my_msg", # 输入消息的key
)

def print_streaming_response(response):
    """打印流式响应内容"""
    full_response = ""
    for chunk in response:
        if hasattr(chunk, 'content'):
            print(chunk.content, end="", flush=True)
            full_response += chunk.content
    print("\n")
    return full_response

def chat_loop():
    """运行聊天循环"""
    print("欢迎使用AI聊天助手！输入'退出'或'exit'结束对话。")
    
    # 为当前会话使用固定的session_id
    session_id = "user_session"
    config = {"configurable": {'session_id': session_id}}
    
    # 设置默认语言
    language = "中文"
    
    while True:
        # 获取用户输入
        user_input = input("\n用户: ")
        
        # 检查是否退出
        if user_input.lower() in ['退出', 'exit', 'quit', 'q']:
            print("感谢使用，再见！")
            break
            
        # 处理用户输入，使用流式输出
        print("\nAI: ", end="", flush=True)
        response = do_message.stream(
            {
                "my_msg": [HumanMessage(content=user_input)],
                "language": language
            },
            config
        )
        print_streaming_response(response)

if __name__ == "__main__":
    chat_loop()