"""
Python代码生成与执行工具模块 - 提供代码生成和执行功能
"""

from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_experimental.utilities import PythonREPL
from typing import Dict, Any, Optional
import os
import sys
import io
import contextlib
import re

# 创建一个新的Python REPL类，而不是继承PythonREPL
class SafePythonREPL:
    """安全的Python REPL，预导入常用模块并提供安全执行环境"""
    
    def __init__(self):
        self.locals = {}
        # 预导入常用模块
        self.modules = {
            "os": os,
            "sys": sys,
            "io": io,
            "datetime": __import__("datetime"),
            "json": __import__("json"),
            "math": __import__("math"),
            "random": __import__("random"),
            "re": __import__("re"),
            "time": __import__("time"),
            "pathlib": __import__("pathlib"),
        }
        
        # 将模块添加到局部变量中
        for module_name, module in self.modules.items():
            self.locals[module_name] = module
    
    def clean_code(self, code: str) -> str:
        """清理代码，移除可能导致语法错误的多余标记
        
        Args:
            code: 输入的Python代码
            
        Returns:
            str: 清理后的代码
        """
        # 移除可能存在的代码块标记
        code = re.sub(r'^```python\s*', '', code)
        code = re.sub(r'\s*```$', '', code)
        code = re.sub(r'^```\s*', '', code)
        
        # 移除开头可能的Python声明
        code = re.sub(r'^python\s*', '', code)
        
        return code.strip()
    
    def run(self, command: str) -> str:
        """在安全环境中运行Python代码，并提供预导入的模块
        
        Args:
            command: 要执行的Python代码
            
        Returns:
            str: 执行结果
        """
        # 首先清理代码
        command = self.clean_code(command)
        
        # 捕获标准输出
        old_stdout = sys.stdout
        mystdout = io.StringIO()
        sys.stdout = mystdout
        
        try:
            # 执行实际代码
            exec(command, self.locals)
            output = mystdout.getvalue()
            
            # 如果没有输出，但是有返回值（通常是最后一行表达式的值）
            if not output.strip() and len(command.strip().split("\n")) == 1:
                try:
                    result = eval(command, self.locals)
                    if result is not None:
                        output = str(result)
                except:
                    pass
                    
            return output if output.strip() else "代码执行成功，但没有输出。"
        except Exception as e:
            return f"执行错误: {str(e)}"
        finally:
            sys.stdout = old_stdout

# 创建安全的Python REPL实例
python_repl = SafePythonREPL()

# 代码生成的提示模板
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
7. 不要使用代码块标记（```python 或 ```）

重要:
- 以下模块已经预导入，可以直接使用: os, sys, io, datetime, json, math, random, re, time, pathlib
- 不要在代码中导入这些已预导入的模块，直接使用即可
- 你的输出将直接被Python解释器执行，因此必须是有效的Python代码
"""),
    ("human", "{instruction}")
])

def get_llm(streaming: bool = False) -> ChatOpenAI:
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

@tool(description="根据自然语言指令生成并执行Python代码")
def generate_and_execute_code(instruction: str) -> str:
    """根据用户的自然语言指令生成并执行Python代码
    
    Args:
        instruction: 用户的自然语言指令，描述需要实现的功能
        
    Returns:
        str: 包含生成的代码和执行结果的字符串
    """
    # 初始化语言模型
    llm = get_llm(streaming=False)
    
    # 设置代码生成链
    code_generation_chain = (
        code_generation_template | 
        llm | 
        StrOutputParser()
    )
    
    # 生成代码
    try:
        generated_code = code_generation_chain.invoke({"instruction": instruction})
        # 清理生成的代码，确保没有```标记等
        generated_code = python_repl.clean_code(generated_code)
    except Exception as e:
        return f"代码生成失败: {str(e)}"
    
    # 执行代码
    try:
        execution_result = python_repl.run(generated_code)
    except Exception as e:
        execution_result = f"执行错误: {str(e)}"
    
    # 格式化返回结果
    response = f"""
生成的Python代码:
```python
{generated_code}
```

执行结果:
```
{execution_result}
```
"""
    
    return response

@tool(description="执行指定的Python代码并返回结果")
def execute_python_code(code: str) -> str:
    """执行用户提供的Python代码
    
    Args:
        code: 需要执行的Python代码
        
    Returns:
        str: 代码执行的结果
    """
    try:
        # 清理代码中可能存在的特殊标记
        cleaned_code = python_repl.clean_code(code)
        result = python_repl.run(cleaned_code)
        return f"执行结果:\n{result}"
    except Exception as e:
        return f"执行错误: {str(e)}" 