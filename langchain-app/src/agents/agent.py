from langchain.agents import AgentExecutor, ZeroShotAgent, ConversationalAgent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_core.messages import SystemMessage, HumanMessage
from ..tools import (
    get_current_time, 
    search_tool, 
    generate_and_execute_code, 
    execute_python_code, 
    duckduckgo_search,
    retrieve_from_knowledge_base,
    get_knowledge_base_info,
    add_website_to_knowledge_base,
    get_document_metadata,
    get_database_tables,
    get_table_structure,
    execute_sql_query,
    ai_query_database,
    # 文件操作工具
    read_file,
    write_file,
    append_to_file,
    list_directory,
    create_directory,
    delete_file,
    delete_directory,
    move_file,
    copy_file,
    get_file_info
)
from ..prompts import get_agent_prompt


def create_agent(llm):
    """使用ConversationalAgent创建智能代理
    
    Args:
        llm: 语言模型实例
    """

    tools = [
        get_current_time,
        search_tool,
        duckduckgo_search,
        generate_and_execute_code,
        execute_python_code,
        retrieve_from_knowledge_base,
        get_knowledge_base_info,
        add_website_to_knowledge_base,
        get_document_metadata,
        get_database_tables,
        get_table_structure,
        execute_sql_query,
        ai_query_database,
        # 文件操作工具
        read_file,
        write_file,
        append_to_file,
        list_directory,
        create_directory,
        delete_file,
        delete_directory,
        move_file,
        copy_file,
        get_file_info,
    ]

    # 构造工具描述字符串
    tools_description = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    
    # 获取知识库信息
    try:
        knowledge_base_info = get_knowledge_base_info.invoke({})  # 使用空字典调用工具
        print("成功获取知识库信息")
    except Exception as e:
        print(f"获取知识库信息失败: {str(e)}")
        knowledge_base_info = None
    
    # 获取数据库表信息 - 数据库连接是自动的
    try:
        # 尝试获取数据库表信息
        tables_info = get_database_tables.invoke({})
        print(f"数据库表信息: {tables_info}")
    except Exception as e:
        print(f"获取数据库表信息失败: {str(e)}")
        tables_info = None
    
    # 获取智能代理提示词
    prompt_dict = get_agent_prompt(tools_description, knowledge_base_info, tables_info)
    
    # 创建 ConversationalAgent 模板
    prompt = ConversationalAgent.create_prompt(
        tools, 
        prefix=prompt_dict["prefix"],
        suffix=prompt_dict["suffix"],
        input_variables=prompt_dict["input_variables"]
    )
    
    print("Agent初始化完成")

    # 定义 llm_chain
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    
    # 创建 ConversationalAgent
    agent = ConversationalAgent(
        llm_chain=llm_chain,
        tools=tools,
        verbose=True
    )
    
    # 创建 AgentExecutor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        max_iterations=15  # 限制最大迭代次数，避免无限循环
    )

    return agent_executor


class Agent:
    """智能代理封装类，提供更方便的调用接口"""
    
    def __init__(self, llm):
        """初始化智能代理
        
        Args:
            llm: 语言模型实例
        """
        self.agent_executor = create_agent(llm)
        self.chat_history = []
    
    def invoke(self, query_or_message):
        """调用智能代理处理查询
        
        Args:
            query_or_message: 字符串查询或HumanMessage对象，或包含消息的字典
            
        Returns:
            dict: 包含agent响应的字典
        """
        # 处理不同类型的输入
        if isinstance(query_or_message, str):
            # 纯文本查询
            messages = [HumanMessage(content=query_or_message)]
            input_data = {'messages': messages, 'chat_history': self.chat_history}
        elif isinstance(query_or_message, HumanMessage):
            # 单个消息对象
            messages = [query_or_message]
            input_data = {'messages': messages, 'chat_history': self.chat_history}
        elif isinstance(query_or_message, dict) and 'messages' in query_or_message:
            # 已经是消息字典格式
            input_data = query_or_message.copy()
            if 'chat_history' not in input_data:
                input_data['chat_history'] = self.chat_history
            messages = input_data['messages']
        else:
            raise ValueError("输入格式不支持，请使用字符串、HumanMessage或包含'messages'的字典")
        
        # 调用agent执行器
        result = self.agent_executor.invoke(input_data)
        
        # 更新聊天历史
        if messages and len(messages) > 0:
            # 添加用户消息
            self.chat_history.append(messages[0])
            
            # 添加AI回复
            if 'output' in result:
                ai_message = result['output']
                self.chat_history.append(ai_message)
        
        return result
