from src.models import initialize_model
from src.chat import interactive_conversation
from src.utils import setup_logging

def main():
    """主函数，执行智能对话应用流程"""
    try:
        # 设置日志
        setup_logging()
        # 初始化模型
        llm = initialize_model()
        
        # 开始交互式对话
        interactive_conversation(llm)
    except Exception as e:
        print(f"程序运行出错: {str(e)}")

# 程序入口点
if __name__ == "__main__":
    main()
