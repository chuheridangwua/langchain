"""
自动代码生成与执行工具

该工具使用LangChain和Python REPL工具链，根据用户的自然语言指令：
1. 生成符合要求的Python代码
2. 自动执行生成的代码
3. 返回执行结果

作者: AI助手
创建日期: 2023
"""

import os
from typing import Optional, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_experimental.utilities import PythonREPL
from pydantic import BaseModel, Field

# 配置语言模型
def get_llm(streaming: bool = True):
    """
    初始化并返回语言模型
    
    Args:
        streaming: 是否启用流式输出
        
    Returns:
        配置好的ChatOpenAI模型实例
    """
    # 使用项目中现有的模型配置
    return ChatOpenAI(
        model="deepseek-v3-250324",  # 使用DeepSeek的大模型
        openai_api_key="09c7ad8f-1659-417b-b6e3-fc7b891061d4",  # API密钥
        openai_api_base="https://ark.cn-beijing.volces.com/api/v3",  # API基础URL
        streaming=streaming,  # 流式输出设置
    )

# 创建Python REPL工具
python_repl = PythonREPL()

# 定义代码生成的提示模板
code_generation_template = ChatPromptTemplate.from_messages([
    ("system", """
你是一个专业的Python开发专家。你的任务是根据用户的需求生成有效的Python代码。

请遵循以下准则：
1. 生成完整的、可执行的Python代码
2. 为代码添加详细的注释，解释每个关键步骤
3. 确保代码安全可靠、性能高效
4. 尽量使用Python标准库，除非特别需要第三方库
5. 适当处理可能的异常和边缘情况
6. 不要包含任何解释性文本，只返回可直接执行的Python代码

重要: 你的输出将直接被Python解释器执行，因此必须是有效的Python代码。
"""),
    ("human", "{instruction}")
])

# 代码执行和结果显示模板
result_explanation_template = ChatPromptTemplate.from_messages([
    ("system", """
你是一个专业的代码分析师，擅长解释代码执行结果。请根据以下信息提供清晰的分析：

1. 用户的原始指令
2. 生成的Python代码
3. 代码执行的结果或错误信息

请提供以下内容：
1. 简要总结代码实现了什么功能
2. 分析执行结果是否符合预期
3. 如果有错误，解释错误原因并提供修复建议
4. 提供任何可能的优化或改进建议

保持分析简洁明了，重点关注用户关心的结果。
"""),
    ("human", """
用户指令: {instruction}

生成的代码:
```python
{generated_code}
```

执行结果:
```
{execution_result}
```
""")
])

class CodeExecutor:
    """
    代码生成和执行器类
    """
    def __init__(self, streaming: bool = True):
        """
        初始化代码执行器
        
        Args:
            streaming: 是否启用流式输出
        """
        self.llm = get_llm(streaming=streaming)
        self.python_repl = PythonREPL()
        
        # 设置代码生成链
        self.code_generation_chain = (
            code_generation_template | 
            self.llm | 
            StrOutputParser()
        )
        
        # 设置结果解释链
        self.result_explanation_chain = (
            result_explanation_template | 
            self.llm | 
            StrOutputParser()
        )
    
    def generate_and_execute(self, instruction: str) -> Dict[str, Any]:
        """
        根据指令生成并执行Python代码
        
        Args:
            instruction: 用户的自然语言指令
            
        Returns:
            包含生成的代码、执行结果和解释的字典
        """
        # 生成代码
        print("正在根据指令生成代码...")
        generated_code = self.code_generation_chain.invoke({"instruction": instruction})
        
        # 执行代码
        print("\n正在执行生成的代码...")
        try:
            execution_result = self.python_repl.run(generated_code)
        except Exception as e:
            execution_result = f"执行错误: {str(e)}"
        
        # 解释结果
        print("\n正在分析执行结果...")
        explanation = self.result_explanation_chain.invoke({
            "instruction": instruction,
            "generated_code": generated_code,
            "execution_result": execution_result
        })
        
        return {
            "instruction": instruction,
            "generated_code": generated_code,
            "execution_result": execution_result,
            "explanation": explanation
        }

# 示例用法
if __name__ == "__main__":
    # 创建代码执行器实例
    executor = CodeExecutor(streaming=False)
    
    # 获取用户输入的指令
    print("请输入您的Python代码生成指令 (输入'退出'结束程序):")
    
    while True:
        user_instruction = input("\n> ")
        
        if user_instruction.lower() in ['退出', 'exit', 'quit']:
            print("程序已退出。")
            break
        
        if not user_instruction.strip():
            print("指令不能为空，请重新输入。")
            continue
        
        # 生成并执行代码
        result = executor.generate_and_execute(user_instruction)
        
        # 显示生成的代码
        print("\n生成的Python代码:")
        print("```python")
        print(result["generated_code"])
        print("```")
        
        # 显示执行结果
        print("\n执行结果:")
        print("```")
        print(result["execution_result"])
        print("```")
        
        # 显示结果解释
        print("\n结果分析:")
        print(result["explanation"])
