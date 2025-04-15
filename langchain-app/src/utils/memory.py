# """
# 用户信息记忆管理模块 - 帮助AI记住用户提供的基本信息
# """

# import re
# import json
# import os
# from typing import Dict, Optional, Any
# from datetime import datetime

# # 用户信息目录
# MEMORY_DIR = "user_memory"
# if not os.path.exists(MEMORY_DIR):
#     os.makedirs(MEMORY_DIR)

# # 内存中的用户信息存储
# user_memory_store: Dict[str, Dict[str, Any]] = {}

# def get_user_memory(session_id: str) -> Dict[str, Any]:
#     """获取指定会话的用户信息记忆
    
#     Args:
#         session_id: 会话ID
        
#     Returns:
#         包含用户信息的字典
#     """
#     if session_id not in user_memory_store:
#         # 尝试从磁盘加载用户信息
#         user_memory_store[session_id] = load_user_memory(session_id) or {}
#     return user_memory_store[session_id]

# def save_user_memory(session_id: str) -> bool:
#     """保存用户信息到磁盘
    
#     Args:
#         session_id: 会话ID
        
#     Returns:
#         保存是否成功
#     """
#     if session_id not in user_memory_store:
#         return False
    
#     memory = user_memory_store[session_id]
    
#     # 如果没有记忆内容，则不需要保存
#     if not memory:
#         return True
    
#     # 创建记忆文件路径
#     memory_path = os.path.join(MEMORY_DIR, f"{session_id}_memory.json")
    
#     try:
#         # 添加最后更新时间
#         memory['_last_updated'] = datetime.now().isoformat()
        
#         # 写入文件
#         with open(memory_path, 'w', encoding='utf-8') as f:
#             json.dump(memory, f, ensure_ascii=False, indent=2)
            
#         return True
    
#     except Exception as e:
#         print(f"保存用户信息失败: {e}")
#         return False

# def load_user_memory(session_id: str) -> Optional[Dict[str, Any]]:
#     """从磁盘加载用户信息
    
#     Args:
#         session_id: 会话ID
        
#     Returns:
#         包含用户信息的字典，如果不存在则返回None
#     """
#     memory_path = os.path.join(MEMORY_DIR, f"{session_id}_memory.json")
    
#     if not os.path.exists(memory_path):
#         return None
    
#     try:
#         with open(memory_path, 'r', encoding='utf-8') as f:
#             memory = json.load(f)
        
#         return memory
    
#     except Exception as e:
#         print(f"加载用户信息失败: {e}")
#         return None

# def extract_user_name(message: str) -> Optional[str]:
#     """从消息中提取用户名称
    
#     Args:
#         message: 用户消息
        
#     Returns:
#         提取的用户名称，如果未找到则返回None
#     """
#     # 匹配"我叫XXX"、"我的名字是XXX"等模式
#     name_patterns = [
#         r'我叫([\u4e00-\u9fa5a-zA-Z]+)',
#         r'我的名字是([\u4e00-\u9fa5a-zA-Z]+)',
#         r'(?:我(?:的)?(?:名(?:字)?|姓名)(?:是|叫))([\u4e00-\u9fa5a-zA-Z]+)',
#         r'(?:call me|name is|i am|i\'m)\s+([a-zA-Z\s]+)'
#     ]
    
#     for pattern in name_patterns:
#         match = re.search(pattern, message)
#         if match:
#             return match.group(1).strip()
    
#     return None

# def update_user_memory(session_id: str, message: str) -> None:
#     """根据用户消息更新记忆
    
#     Args:
#         session_id: 会话ID
#         message: 用户消息
#     """
#     memory = get_user_memory(session_id)
    
#     # 尝试提取用户名
#     name = extract_user_name(message)
#     if name and len(name) < 20:  # 添加长度限制避免错误提取
#         memory['name'] = name
#         save_user_memory(session_id)

# def get_memory_summary(session_id: str) -> str:
#     """获取用户记忆摘要，用于提示AI
    
#     Args:
#         session_id: 会话ID
        
#     Returns:
#         记忆摘要字符串
#     """
#     memory = get_user_memory(session_id)
    
#     if not memory:
#         return ""
    
#     summary_parts = []
    
#     if 'name' in memory:
#         summary_parts.append(f"用户名称: {memory['name']}")
    
#     # 可以在这里添加其他类型的记忆项
    
#     if not summary_parts:
#         return ""
        
#     return "用户信息记忆:\n" + "\n".join(summary_parts) 