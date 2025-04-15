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
            # 基础模块
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
            
            # 文件操作相关模块
            "csv": __import__("csv"),
            "pickle": __import__("pickle"),
            "shutil": __import__("shutil"),
            "tempfile": __import__("tempfile"),
            "glob": __import__("glob"),
            "fnmatch": __import__("fnmatch"),
            "fileinput": __import__("fileinput"),
            "configparser": __import__("configparser"),
            "zipfile": __import__("zipfile"),
            "tarfile": __import__("tarfile"),
            "gzip": __import__("gzip"),
            "bz2": __import__("bz2"),
            "lzma": __import__("lzma"),
            
            # 数据处理相关模块
            "collections": __import__("collections"),
            "itertools": __import__("itertools"),
            "functools": __import__("functools"),
            "operator": __import__("operator"),
            "statistics": __import__("statistics"),
            "array": __import__("array"),
            "struct": __import__("struct"),
            "copy": __import__("copy"),
            "enum": __import__("enum"),
            "typing": __import__("typing"),
            
            # 网络和Web相关模块
            "urllib": __import__("urllib"),
            "http": __import__("http"),
            "email": __import__("email"),
            "socket": __import__("socket"),
            "html": __import__("html"),
            "base64": __import__("base64"),
            "hashlib": __import__("hashlib"),
            
            # 数据格式处理模块
            "xml": __import__("xml"),
            "uuid": __import__("uuid"),
            
            # 数据库相关模块
            "sqlite3": __import__("sqlite3"),
            
            # 日期时间处理
            "calendar": __import__("calendar"),
            
            # 尝试导入可能安装的第三方库（如果失败则忽略）
            **self._try_import_modules([
                # 数据科学相关
                "numpy", 
                "pandas", 
                "matplotlib", 
                "seaborn", 
                
                # 网络请求
                "requests", 
                "bs4", 
                
                # 数据格式
                "yaml", 
                "toml", 
                
                # Excel处理
                "openpyxl",  # 处理现代Excel(.xlsx)
                "xlrd",      # 读取Excel
                "xlwt",      # 写入Excel(.xls)
                "xlsxwriter", # 创建Excel(.xlsx)
                "xlutils",   # Excel工具集
                
                # Word文档处理
                "docx",      # python-docx包，处理.docx文件
                "docx2txt",  # 从Word提取文本
                "python-docx", # 另一种导入尝试
                "docxtpl",   # 基于模板的Word处理
                
                # PDF处理
                "PyPDF2",    # PDF处理
                "PyPDF4",    # PDF处理升级版
                "reportlab", # PDF生成
                
                # 图像处理
                "pillow", 
                "opencv-python",
                
                # 数据分析和可视化
                "plotly",
                "scikit-learn",
                "scipy"
            ])
        }
        
        # 将模块添加到局部变量中
        for module_name, module in self.modules.items():
            self.locals[module_name] = module
    
    def _try_import_modules(self, module_names):
        """尝试导入模块，如果不可用则忽略"""
        imported_modules = {}
        for module_name in module_names:
            try:
                # 处理特殊情况
                if module_name == "python-docx":
                    # python-docx包实际上导入为docx
                    try:
                        imported_modules["docx"] = __import__("docx")
                    except ImportError:
                        pass
                elif module_name == "pillow":
                    # Pillow库实际导入为PIL
                    try:
                        imported_modules["PIL"] = __import__("PIL")
                        # 添加常用的PIL子模块
                        imported_modules["Image"] = __import__("PIL.Image", fromlist=["Image"])
                    except ImportError:
                        pass
                else:
                    # 尝试导入模块
                    imported_modules[module_name] = __import__(module_name)
                    
                # 为常见库添加特殊支持
                if module_name == "numpy":
                    imported_modules["np"] = imported_modules[module_name]
                elif module_name == "pandas":
                    imported_modules["pd"] = imported_modules[module_name]
                elif module_name == "matplotlib":
                    imported_modules["plt"] = __import__("matplotlib.pyplot", fromlist=["pyplot"])
                elif module_name == "bs4":
                    try:
                        imported_modules["BeautifulSoup"] = __import__("bs4").BeautifulSoup
                    except:
                        pass
                elif module_name == "openpyxl":
                    # 导入常用的openpyxl子模块
                    try:
                        imported_modules["load_workbook"] = __import__("openpyxl", fromlist=["load_workbook"]).load_workbook
                        imported_modules["Workbook"] = __import__("openpyxl", fromlist=["Workbook"]).Workbook
                    except:
                        pass
                elif module_name == "scikit-learn":
                    # scikit-learn通常作为sklearn导入
                    try:
                        imported_modules["sklearn"] = __import__("sklearn")
                    except:
                        pass
                elif module_name == "PyPDF2" or module_name == "PyPDF4":
                    # 为PDF库添加常用的子模块
                    try:
                        imported_modules["PdfReader"] = getattr(__import__(module_name, fromlist=["PdfReader"]), "PdfReader")
                        imported_modules["PdfWriter"] = getattr(__import__(module_name, fromlist=["PdfWriter"]), "PdfWriter")
                    except:
                        pass
            except ImportError:
                # 如果模块不可用，则忽略
                pass
        return imported_modules
    
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
2. 为代码添加详细的中文注释，解释每个关键步骤
3. 确保代码安全可靠、性能高效
4. 必须明确导入所有使用到的模块，不要假设任何模块已被预导入
5. 适当处理可能的异常和边缘情况
6. 不要包含任何解释性文本，只返回可直接执行的Python代码
7. 不要使用代码块标记（```python 或 ```）
8. 所有需要输出的结果必须使用print()函数打印，不要直接使用变量作为输出

关于输出和导入的重要规则：
- 即使是下面列出的"预导入模块"，也必须在代码中明确导入才能使用
- 所有需要展示的结果必须使用print()函数输出，而不是直接写变量名
- 对于数据分析任务，使用print(df.head())而不是直接写df.head()
- 对于matplotlib图表，必须调用plt.show()显示图表

常用模块参考（使用时需要先导入）:

基础模块:
- os, sys, io, datetime, json, math, random, re, time, pathlib, calendar
- collections, itertools, functools, operator, statistics, copy, enum, typing
- xml, html, uuid, sqlite3, base64, hashlib

文件操作:
- csv, pickle, shutil, tempfile, glob, fnmatch, fileinput, configparser
- zipfile, tarfile, gzip, bz2, lzma

网络请求:
- urllib, http, email, socket, requests

Excel处理:
- openpyxl (包括load_workbook和Workbook)
- xlrd, xlwt, xlsxwriter, xlutils

Word文档处理:
- docx (python-docx包)
- docx2txt, docxtpl

PDF处理:
- PyPDF2/PyPDF4 (包括PdfReader和PdfWriter)
- reportlab

数据科学与可视化:
- numpy (别名: np)
- pandas (别名: pd)
- matplotlib.pyplot (别名: plt)
- seaborn, plotly, sklearn, scipy

图像处理:
- PIL.Image (从PIL导入Image)
- cv2 (如果OpenCV可用)

你的输出将直接被Python解释器执行，因此必须是有效的Python代码，包含所有必要的导入语句。
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