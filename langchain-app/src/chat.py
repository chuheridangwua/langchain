"""
交互式对话模块 - 处理用户与AI的交互
"""

import os
import re
import logging
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

from .agents import create_agent
from .utils import (
    StreamingAgentCallbackHandler,
    create_session,
    get_session_history,
    save_session,
    load_session
)

# 设置日志
logger = logging.getLogger(__name__)

def list_available_sessions():
    """列出所有可用的会话"""
    session_dir = "sessions"
    if not os.path.exists(session_dir):
        return []
    
    sessions = []
    for file in os.listdir(session_dir):
        if file.endswith(".json"):
            session_id = file[:-5]  # 移除 .json 后缀
            sessions.append(session_id)
    
    return sessions

def is_history_command(text):
    """判断输入是否是查看历史记录的命令
    
    支持多种可能的拼写变体和简写
    """
    # 去除空格并转小写
    text = text.strip().lower()
    
    # 精确匹配
    if text in ['history', 'hist']:
        return True
    
    # 常见拼写错误
    if text in ['histroy', 'hisotry', 'histor', 'histry']:
        return True
    
    # 使用编辑距离算法可以检测更多变体，但这里先使用简单的方法
    # 正则匹配"h.*t.*r.*y"模式
    if re.match(r'^h\w*[it]\w*[st]\w*r\w*y$', text):
        return True
        
    return False

def format_chat_history(messages):
    """格式化聊天历史记录为ConversationalAgent可用的格式
    
    Args:
        messages: 消息列表
        
    Returns:
        格式化后的聊天历史字符串
    """
    if not messages:
        return ""
    
    formatted_history = []
    
    for message in messages:
        if message.type == "human":
            formatted_history.append(f"Human: {message.content}")
        elif message.type == "ai":
            formatted_history.append(f"AI: {message.content}")
    
    return "\n".join(formatted_history)

def interactive_conversation(llm):
    """进行交互式对话"""
    print("\n欢迎使用聊天系统\n")
    
    # 检查是否有可用的会话
    available_sessions = list_available_sessions()
    session_id = None
    
    if available_sessions:
        print("找到以下已保存的会话：")
        for i, s_id in enumerate(available_sessions):
            print(f"{i+1}. {s_id}")
        
        print("\n请选择操作：")
        print("0. 创建新会话")
        for i, s_id in enumerate(available_sessions):
            print(f"{i+1}. 恢复会话 {s_id}")
        
        while True:
            try:
                choice = input("\n请输入选项编号: ")
                if choice.strip() == "0":
                    # 创建新会话
                    session_id = create_session()
                    break
                elif choice.strip().isdigit() and 1 <= int(choice) <= len(available_sessions):
                    # 恢复已有会话
                    session_id = available_sessions[int(choice) - 1]
                    break
                else:
                    print("无效的选择，请重试")
            except ValueError:
                print("请输入有效的数字")
    
    # 如果没有选择会话或没有可用会话，创建新会话
    if not session_id:
        session_id = create_session()
    
    # 获取聊天历史
    chat_history = get_session_history(session_id)
    
    # 创建智能代理
    agent_executor = create_agent(llm)
    
    # 创建回调处理器
    callbacks = [StreamingAgentCallbackHandler()]
    
    print(f"\n当前会话ID: {session_id}")
    
    # 如果会话有历史记录，显示提示信息
    if chat_history.messages:
        print("\n已加载历史对话记录。输入 'history' 查看历史记录。")
    
    try:
        while True:
            # 获取用户输入
            user_input = input("\n用户: ")
            
            # 检查是否退出
            if user_input.lower() in ['退出', 'exit', 'quit', 'q']:
                print("\n再见！")
                break
            
            # 检查是否需要显示历史记录
            if is_history_command(user_input):
                print("\n=== 历史对话记录 ===")
                for i, message in enumerate(chat_history.messages):
                    prefix = "用户: " if message.type == "human" else "AI: "
                    print(f"{prefix}{message.content}")
                print("=== 记录结束 ===")
                continue
            
            try:
                # 将用户输入添加到历史记录
                chat_history.add_user_message(user_input)
                
                # 确保消息包含足够的上下文
                # 限制历史记录为最近的10条消息，避免token超限
                recent_history = chat_history.messages[-10:] if len(chat_history.messages) > 10 else chat_history.messages
                
                # 将聊天历史格式化为ConversationalAgent可用的格式
                formatted_history = format_chat_history(recent_history[:-1])  # 去掉最后一条(当前)消息
                
                # 记录历史消息以便调试
                logger.debug(f"聊天历史记录 ({len(recent_history)-1} 条消息):")
                logger.debug(formatted_history)
                
                # 准备代理输入
                agent_input = {
                    "input": user_input,
                    "chat_history": formatted_history
                }
                
                print("\nAI: ", end="", flush=True)
                
                # 调用代理执行器并获取结果（使用回调）
                result = agent_executor.invoke(agent_input, config={"callbacks": callbacks})
                answer = result["output"]
                
                # 换行（因为流式输出已经打印了内容）
                print()
                
                # 将AI回答添加到历史记录
                chat_history.add_ai_message(answer)
                
                # 每次对话后保存会话历史
                save_session(session_id)
                
            except Exception as e:
                logger.exception("对话处理出错")
                print(f"\n发生错误: {e}")
    finally:
        # 确保在退出时保存会话
        save_session(session_id)
        print(f"\n会话已保存（ID: {session_id}）")
        print(f"您可以使用此ID在下次启动时恢复会话。") 