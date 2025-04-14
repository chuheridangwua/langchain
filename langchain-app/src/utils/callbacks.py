"""
回调处理器模块 - 定义用于处理模型输出和日志的回调
"""

import logging
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from datetime import datetime

class StreamingAgentCallbackHandler(BaseCallbackHandler):
    """自定义回调处理器，用于流式输出和日志记录"""

    def __init__(self):
        """初始化处理器"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("初始化StreamingAgentCallbackHandler")
    
    def on_llm_error(self, error, **kwargs):
        """当LLM发生错误时"""
        self.logger.error(f"LLM发生错误: {str(error)}")

# 配置日志
def setup_logging():
    """设置应用程序日志配置"""
    # 创建日志目录
    import os
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"chat_{timestamp}.log")
    
    # 配置日志 - 设置为DEBUG级别以获取详细信息
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成")
    logger.info(f"日志文件路径: {log_file}")

    # 确保控制台输出也使用UTF-8编码（针对Windows系统）
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
        logger.info("Windows系统UTF-8编码设置完成")