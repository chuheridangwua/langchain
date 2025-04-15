"""
数据库工具模块 - 提供数据库连接和SQL操作功能
"""

from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from typing import Dict, List, Any, Optional, Union
import os
import re
from dotenv import load_dotenv
from ..models.llm import initialize_model
from langchain.prompts import ChatPromptTemplate

# 加载环境变量
load_dotenv()

# 数据库连接信息（固定）
HOSTNAME = '127.0.0.1'
PORT = '5432'  # PostgreSQL默认端口是5432
DATABASE = '0414'
USERNAME = 'postgres'  # PostgreSQL默认用户
PASSWORD = 'root'  # 数据库密码

# PostgreSQL连接URL - 这是唯一允许使用的连接
PG_URI = f'postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}'

# SQL生成提示词模板
SQL_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
你是一位精通SQL的数据库专家。你的任务是根据用户的自然语言描述，生成准确、高效的SQL查询语句。

请遵循以下准则：
1. 只生成一个完整的、可执行的SQL查询语句
2. 遵循标准SQL语法，优先考虑PostgreSQL兼容性
3. 确保查询安全、高效、性能良好
4. 处理好WHERE条件，确保条件逻辑正确
5. 适当添加ORDER BY、GROUP BY、LIMIT等子句
6. 不要包含任何解释性文本，只输出SQL查询语句
7. 不要使用反引号或代码块标记（```sql 或 ```）

数据库的表结构如下：
{table_info}

重要提示:
- 你必须只输出SQL语句，不要有任何前缀（如"SQLQuery:"）或其他说明文字
- 如果你无法根据提供的表结构生成查询，请明确说明"无法根据当前表结构生成SQL查询"
- 请不要在字段名或表名周围添加引号，除非它们是关键字或包含特殊字符
- 请使用简单连接语法而不是CROSS JOIN，除非明确需要交叉连接
- 如果查询涉及多个表，确保正确处理表之间的关系
- 默认限制结果数量，除非用户明确要求所有结果
"""),
    ("human", "{question}")
])

# 全局单例数据库连接实例
_DB_CONNECTION = None

class DatabaseConnection:
    """数据库连接管理类 - 固定使用预设数据库"""
    
    def __init__(self):
        """
        初始化数据库连接 - 仅允许使用预设的连接信息
        """
        self.connection_string = PG_URI
        self.name = "default"
        try:
            self.db = SQLDatabase.from_uri(self.connection_string)
            self.model = None
            print(f"已连接到预设数据库: {DATABASE} (用户: {USERNAME}@{HOSTNAME}:{PORT})")
        except Exception as e:
            print(f"初始化数据库连接失败: {str(e)}")
            raise
    
    def set_llm(self, model: Optional[ChatOpenAI] = None):
        """
        设置语言模型
        
        Args:
            model: ChatOpenAI实例，如果为None则使用项目配置的模型
        """
        if model is None:
            # 使用项目中的model实例
            self.model = initialize_model()
        else:
            self.model = model
    
    def get_toolkit(self) -> SQLDatabaseToolkit:
        """
        获取SQL数据库工具包
        
        Returns:
            SQLDatabaseToolkit: SQL数据库工具包
        """
        if self.model is None:
            self.set_llm()
        
        return SQLDatabaseToolkit(db=self.db, llm=self.model)
    
    def get_tables(self) -> List[str]:
        """
        获取数据库中的所有表名
        
        Returns:
            List[str]: 表名列表
        """
        return self.db.get_table_names()
    
    def get_table_info(self, table_name: Optional[str] = None) -> str:
        """
        获取表结构信息
        
        Args:
            table_name: 表名，如果为None则返回所有表的结构
            
        Returns:
            str: 表结构信息
        """
        if table_name:
            return self.db.get_table_info([table_name])
        return self.db.get_table_info()
    
    def run_query(self, query: str) -> List[Dict[str, Any]]:
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        # 清除可能由AI生成的前缀，如"SQLQuery: "
        query = self._cleanup_sql_query(query)
        return self.db.run(query)
    
    def _cleanup_sql_query(self, query: str) -> str:
        """
        清理SQL查询，移除AI可能添加的前缀
        
        Args:
            query: 原始SQL查询字符串
            
        Returns:
            str: 清理后的SQL查询
        """
        # 移除"SQLQuery: "前缀
        query = re.sub(r'^SQLQuery:\s*', '', query.strip())
        
        # 移除其他可能的注释或前缀
        query = re.sub(r'^--.*$', '', query, flags=re.MULTILINE)
        
        return query.strip()
    
    def generate_sql(self, question: str) -> str:
        """
        使用AI生成SQL查询
        
        Args:
            question: 用自然语言描述的查询需求
            
        Returns:
            str: 生成的SQL查询语句
        """
        if self.model is None:
            self.set_llm()
        
        # 获取表结构信息
        table_info = self.get_table_info()
        
        # 使用提示词模板生成SQL查询
        formatted_prompt = SQL_GENERATION_PROMPT.format(
            table_info=table_info,
            question=question
        )
        
        # 调用模型生成SQL
        try:
            # 检查formatted_prompt是否为ChatPromptTemplate对象
            if hasattr(formatted_prompt, 'format_prompt'):
                messages = formatted_prompt.format_prompt().to_messages()
            else:
                # 如果是字符串或其他类型，直接构造消息
                messages = [{"role": "user", "content": formatted_prompt}]
            
            sql_response = self.model.invoke(messages)
            
            # 提取SQL语句
            sql_query = sql_response.content.strip()
            
            # 清理SQL语句
            sql_query = self._cleanup_sql_query(sql_query)
            
            return sql_query
        except Exception as e:
            print(f"生成SQL查询失败: {str(e)}")
            # 如果生成失败，返回一个错误消息，让调用者处理
            return f"无法生成SQL查询: {str(e)}"


def get_db_connection() -> DatabaseConnection:
    """
    获取数据库连接的全局单例实例
    
    Returns:
        DatabaseConnection: 数据库连接实例
    """
    global _DB_CONNECTION
    if _DB_CONNECTION is None:
        try:
            _DB_CONNECTION = DatabaseConnection()
        except Exception as e:
            print(f"创建数据库连接失败: {str(e)}")
            raise
    return _DB_CONNECTION


# 在模块导入时自动创建数据库连接
try:
    db_connection = get_db_connection()
    print("已自动创建并连接到预设数据库")
except Exception as e:
    print(f"自动连接预设数据库失败: {str(e)}")


@tool(description="获取数据库表列表")
def get_database_tables(params: Union[str, dict] = "") -> str:
    """
    获取预设数据库中的所有表
    
    Returns:
        str: 表名列表
    """
    try:
        # 获取连接实例
        db_conn = get_db_connection()
        tables = db_conn.get_tables()
        if not tables:
            return "数据库中没有找到表"
        return f"数据库中的表: {', '.join(tables)}"
    except Exception as e:
        return f"获取数据库表失败: {str(e)}"


@tool(description="获取数据库表结构")
def get_table_structure(table_name_or_params: Union[str, dict] = "") -> str:
    """
    获取数据库表的结构信息
    
    Args:
        table_name_or_params: 表名或包含表名的字典
        
    Returns:
        str: 表结构信息
    """
    try:
        # 处理参数
        table_name = None
        
        if isinstance(table_name_or_params, dict):
            if "table_name" in table_name_or_params:
                table_name = table_name_or_params["table_name"]
        elif isinstance(table_name_or_params, str) and table_name_or_params:
            table_name = table_name_or_params
        
        # 获取连接实例
        db_conn = get_db_connection()
        table_info = db_conn.get_table_info(table_name)
        
        if not table_info:
            if table_name:
                return f"表 '{table_name}' 不存在或没有结构信息"
            else:
                return "数据库中没有表结构信息"
                
        return f"表结构信息:\n{table_info}"
    except Exception as e:
        return f"获取表结构失败: {str(e)}"


@tool(description="执行SQL查询")
def execute_sql_query(query_or_params: Union[str, dict]) -> str:
    """
    在预设数据库中执行SQL查询并返回结果
    
    Args:
        query_or_params: SQL查询语句或包含查询的字典
        
    Returns:
        str: 查询结果
    """
    try:
        # 处理参数
        query = None
        
        if isinstance(query_or_params, dict):
            if "query" in query_or_params:
                query = query_or_params["query"]
            elif "sql" in query_or_params:
                query = query_or_params["sql"]
        elif isinstance(query_or_params, str):
            query = query_or_params
        
        if not query:
            return "错误: 未提供SQL查询语句"
        
        # 获取连接实例
        db_conn = get_db_connection()
        
        # 清理SQL，移除可能的前缀
        query = db_conn._cleanup_sql_query(query)
        
        # 执行查询
        results = db_conn.run_query(query)
        
        # 格式化结果为字符串
        if not results:
            return "查询没有返回任何结果"
        
        # 确保结果是列表类型
        if not isinstance(results, list):
            # 如果结果是字符串类型，直接返回该字符串
            if isinstance(results, str):
                return f"查询结果:\n{results}"
            # 尝试将结果转换为列表（如果可能）
            try:
                results = [results]
            except:
                return f"查询结果类型错误，无法处理: {type(results)}"
        
        # 获取列名
        try:
            columns = list(results[0].keys())
            
            # 构建表格式输出
            output = "查询结果:\n"
            output += " | ".join(columns) + "\n"
            output += "-" * (sum(len(col) for col in columns) + 3 * (len(columns) - 1)) + "\n"
            
            for row in results:
                output += " | ".join(str(row[col]) for col in columns) + "\n"
                
            return output
        except (AttributeError, IndexError) as e:
            # 如果结果不是预期的字典列表格式，直接返回原始结果
            return f"查询结果 (非标准格式):\n{results}"
            
    except Exception as e:
        return f"执行SQL查询失败: {str(e)}"


class CustomQuerySQLDatabaseTool(QuerySQLDatabaseTool):
    """自定义数据库查询工具，处理特殊前缀"""
    
    def _run(self, query: str) -> str:
        """
        重写运行方法，清理SQL查询
        
        Args:
            query: SQL查询语句
            
        Returns:
            str: 查询结果
        """
        # 移除可能的SQLQuery前缀
        query = re.sub(r'^SQLQuery:\s*', '', query.strip())
        return super()._run(query)


@tool(description="使用AI生成并执行SQL查询")
def ai_query_database(question_or_params: Union[str, dict]) -> str:
    """
    使用AI根据自然语言问题生成SQL查询并在预设数据库上执行
    
    Args:
        question_or_params: 用自然语言描述的查询需求或包含问题的字典
        
    Returns:
        str: 查询结果
    """
    try:
        # 处理参数
        question = None
        limit_results = 10
        
        if isinstance(question_or_params, dict):
            if "question" in question_or_params:
                question = question_or_params["question"]
            elif "query" in question_or_params:
                question = question_or_params["query"]
                
            if "limit_results" in question_or_params:
                limit_results = question_or_params["limit_results"]
        elif isinstance(question_or_params, str):
            question = question_or_params
        
        if not question:
            return "错误: 未提供查询问题"
        
        # 获取连接实例
        db_conn = get_db_connection()
        
        if db_conn.model is None:
            db_conn.set_llm()
            
        # 使用自定义提示词生成SQL
        try:
            # 添加限制结果数量的提示
            query_with_limit = f"{question} (限制返回最多{limit_results}条结果)"
            
            # 生成SQL查询
            sql_query = db_conn.generate_sql(query_with_limit)
            
            # 执行查询
            results = db_conn.run_query(sql_query)
            
            # 格式化结果为字符串
            if not results:
                return f"问题: {question}\n\nAI生成的SQL查询:\n{sql_query}\n\n查询没有返回结果。"
            
            # 处理非列表类型的结果
            if not isinstance(results, list):
                if isinstance(results, str):
                    result_str = f"查询结果:\n{results}"
                    return f"问题: {question}\n\nAI生成的SQL查询:\n{sql_query}\n\n{result_str}"
                try:
                    results = [results]
                except:
                    return f"问题: {question}\n\nAI生成的SQL查询:\n{sql_query}\n\n查询结果类型错误，无法处理: {type(results)}"
            
            # 获取列名
            columns = list(results[0].keys())
            
            # 构建表格式结果
            result_str = "查询结果:\n"
            result_str += " | ".join(columns) + "\n"
            result_str += "-" * (sum(len(col) for col in columns) + 3 * (len(columns) - 1)) + "\n"
            
            for row in results:
                result_str += " | ".join(str(row[col]) for col in columns) + "\n"
            
            # 组合完整输出（不包含解释）
            output = f"问题: {question}\n\n"
            output += f"AI生成的SQL查询:\n{sql_query}\n\n"
            output += f"{result_str}"
            
            return output
            
        except Exception as generation_error:
            # 如果自定义方法失败，回退到标准方法
            print(f"自定义SQL生成失败: {str(generation_error)}，使用标准方法")
            
            # 创建SQL查询链
            query_chain = create_sql_query_chain(db_conn.model, db_conn.db)
            
            # 创建自定义数据库查询工具
            db_tool = CustomQuerySQLDatabaseTool(
                db=db_conn.db,
                llm=db_conn.model
            )
            
            # 构建完整的查询链
            full_chain = (
                {"question": RunnablePassthrough()}
                | query_chain
                | db_tool
            )
            
            # 添加限制结果数量的提示
            query_with_limit = f"{question} (限制返回最多{limit_results}条结果)"
            
            # 执行查询
            try:
                result = full_chain.invoke(query_with_limit)
                return f"问题: {question}\n\n{result}"
            except Exception as query_error:
                # 如果查询失败，尝试直接生成SQL并手动执行
                try:
                    sql_query = query_chain.invoke(question)
                    
                    # 清理SQL
                    sql_query = re.sub(r'^SQLQuery:\s*', '', sql_query.strip())
                    
                    if not sql_query or "我无法" in sql_query or "不清楚" in sql_query:
                        return f"AI无法生成查询: {sql_query}"
                    
                    # 手动执行SQL
                    results = db_conn.run_query(sql_query)
                    
                    # 格式化结果
                    if not results:
                        return f"问题: {question}\n\nAI生成了SQL查询:\n{sql_query}\n\n但查询没有返回结果。"
                    
                    # 处理非列表类型的结果
                    if not isinstance(results, list):
                        if isinstance(results, str):
                            return f"问题: {question}\n\nAI生成了SQL查询:\n{sql_query}\n\n查询结果:\n{results}"
                        try:
                            results = [results]
                        except:
                            return f"问题: {question}\n\nAI生成了SQL查询:\n{sql_query}\n\n查询结果类型错误，无法处理: {type(results)}"
                    
                    # 获取列名
                    columns = list(results[0].keys())
                    
                    # 构建表格式输出
                    output = f"问题: {question}\n\nAI生成了SQL查询:\n{sql_query}\n\n查询结果:\n"
                    output += " | ".join(columns) + "\n"
                    output += "-" * (sum(len(col) for col in columns) + 3 * (len(columns) - 1)) + "\n"
                    
                    for row in results:
                        output += " | ".join(str(row[col]) for col in columns) + "\n"
                        
                    return output
                    
                except Exception as backup_error:
                    return f"AI查询数据库失败: {str(query_error)}\n尝试备用方法也失败: {str(backup_error)}"
    except Exception as e:
        return f"AI查询数据库失败: {str(e)}" 