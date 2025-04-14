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
    load_session,
    get_user_memory,
    save_user_memory,
    update_user_memory,
    get_memory_summary
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

def is_memory_command(text):
    """判断输入是否是查看记忆的命令"""
    text = text.strip().lower()
    return text in ['memory', 'mem', '记忆', '信息']

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
    
    # 获取聊天历史和用户记忆
    chat_history = get_session_history(session_id)
    user_memory = get_user_memory(session_id)
    
    # 获取记忆摘要
    memory_summary = get_memory_summary(session_id)
    
    # 创建智能代理（带有记忆信息）
    agent_executor = create_agent(llm, include_memory_info=memory_summary)
    
    # 创建回调处理器
    callbacks = [StreamingAgentCallbackHandler()]
    
    print(f"\n当前会话ID: {session_id}")
    
    # 如果会话有历史记录，显示提示信息
    if chat_history.messages:
        print("\n已加载历史对话记录。输入 'history' 查看历史记录。")
    
    # 如果有用户记忆，显示提示
    if user_memory:
        print("已加载用户信息。输入 'memory' 查看记忆内容。")
    
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
            
            # 检查是否查看记忆内容
            if is_memory_command(user_input):
                if user_memory:
                    print("\n=== 用户信息记忆 ===")
                    for key, value in user_memory.items():
                        # 跳过以下划线开头的内部字段
                        if not key.startswith('_'):
                            print(f"{key}: {value}")
                    print("=== 记录结束 ===")
                else:
                    print("\n尚未记录用户信息")
                continue
            
            try:
                # 更新用户记忆
                update_user_memory(session_id, user_input)
                
                # 获取最新的记忆摘要
                memory_summary = get_memory_summary(session_id)
                
                # 如果记忆有更新，重新创建代理
                if memory_summary:
                    agent_executor = create_agent(llm, include_memory_info=memory_summary)
                
                # 将用户输入添加到历史记录
                chat_history.add_user_message(user_input)
                
                # 确保消息包含足够的上下文
                # 限制历史记录为最近的10条消息，避免token超限
                recent_history = chat_history.messages[-10:] if len(chat_history.messages) > 10 else chat_history.messages
                
                # 记录历史消息以便调试
                logger.debug(f"聊天历史记录 ({len(recent_history)} 条消息):")
                for i, msg in enumerate(recent_history):
                    logger.debug(f"[{i}] {msg.type}: {msg.content[:50]}...")
                
                # 准备代理输入
                agent_input = {
                    "input": user_input,
                    "chat_history": recent_history
                }
                
                print("\nAI: ", end="", flush=True)
                
                # 调用代理执行器并获取结果（使用回调）
                result = agent_executor.invoke(agent_input, config={"callbacks": callbacks})
                answer = result["output"]
                
                # 换行（因为流式输出已经打印了内容）
                print()
                
                # 将AI回答添加到历史记录
                chat_history.add_ai_message(answer)
                
                # 每次对话后保存会话历史和用户记忆
                save_session(session_id)
                save_user_memory(session_id)
                
            except Exception as e:
                logger.exception("对话处理出错")
                print(f"\n发生错误: {e}")
    finally:
        # 确保在退出时保存会话和用户记忆
        save_session(session_id)
        save_user_memory(session_id)
        print(f"\n会话已保存（ID: {session_id}）")
        print(f"您可以使用此ID在下次启动时恢复会话。") 