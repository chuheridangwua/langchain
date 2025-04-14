"""
会话管理模块 - 管理用户会话和聊天历史记录
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional
import logging
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 创建会话存储目录
SESSION_DIR = "sessions"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# 会话存储
session_store: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> ChatMessageHistory:
    """获取指定会话ID的聊天历史
    
    Args:
        session_id: 会话ID
        
    Returns:
        对应的聊天历史对象
    """
    if session_id not in session_store:
        # 尝试从磁盘加载历史记录
        session_store[session_id] = load_session(session_id) or ChatMessageHistory()
    return session_store[session_id]

def save_session(session_id: str) -> bool:
    """保存会话历史到磁盘
    
    Args:
        session_id: 会话ID
        
    Returns:
        保存是否成功
    """
    if session_id not in session_store:
        return False
    
    history = session_store[session_id]
    
    # 创建会话文件路径
    session_path = os.path.join(SESSION_DIR, f"{session_id}.json")
    
    try:
        # 将消息历史转换为可序列化格式
        serialized_messages = []
        
        for message in history.messages:
            if message.type == "human":
                msg_type = "human"
            elif message.type == "ai":
                msg_type = "ai"
            elif message.type == "system":
                msg_type = "system"
            else:
                msg_type = "other"
                
            serialized_messages.append({
                "type": msg_type,
                "content": message.content,
                "timestamp": datetime.now().isoformat()
            })
        
        # 写入文件
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(serialized_messages, f, ensure_ascii=False, indent=2)
            
        logging.info(f"已保存会话 {session_id}")
        return True
    
    except Exception as e:
        logging.error(f"保存会话 {session_id} 失败: {e}")
        return False

def load_session(session_id: str) -> Optional[ChatMessageHistory]:
    """从磁盘加载会话历史
    
    Args:
        session_id: 会话ID
        
    Returns:
        加载的聊天历史对象，如果不存在则返回None
    """
    session_path = os.path.join(SESSION_DIR, f"{session_id}.json")
    
    if not os.path.exists(session_path):
        return None
    
    try:
        with open(session_path, 'r', encoding='utf-8') as f:
            serialized_messages = json.load(f)
        
        history = ChatMessageHistory()
        
        for msg in serialized_messages:
            if msg["type"] == "human":
                history.add_message(HumanMessage(content=msg["content"]))
            elif msg["type"] == "ai":
                history.add_message(AIMessage(content=msg["content"]))
            elif msg["type"] == "system":
                history.add_message(SystemMessage(content=msg["content"]))
                
        logging.info(f"已加载会话 {session_id}")
        return history
    
    except Exception as e:
        logging.error(f"加载会话 {session_id} 失败: {e}")
        return None

def create_session() -> str:
    """创建新的会话
    
    Returns:
        新会话的ID
    """
    # 使用时间戳创建唯一会话ID
    session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    session_store[session_id] = ChatMessageHistory()
    return session_id

def delete_session(session_id: str) -> bool:
    """删除会话
    
    Args:
        session_id: 要删除的会话ID
        
    Returns:
        删除是否成功
    """
    if session_id in session_store:
        del session_store[session_id]
    
    session_path = os.path.join(SESSION_DIR, f"{session_id}.json")
    
    if os.path.exists(session_path):
        try:
            os.remove(session_path)
            logging.info(f"已删除会话 {session_id}")
            return True
        except Exception as e:
            logging.error(f"删除会话 {session_id} 失败: {e}")
            return False
    
    return True 