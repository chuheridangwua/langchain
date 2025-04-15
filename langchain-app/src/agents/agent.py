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
    get_document_metadata
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
    ]

    # 构造工具描述字符串
    tools_description = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    
    # 获取知识库信息
    try:
        knowledge_base_info = get_knowledge_base_info.invoke("")  # 使用invoke方法正确调用工具
        print("成功获取知识库信息")
    except Exception as e:
        print(f"获取知识库信息失败: {str(e)}")
        knowledge_base_info = None
    
    # 获取智能代理提示词
    prompt_dict = get_agent_prompt(tools_description, knowledge_base_info)
    
    # 创建 ConversationalAgent 模板
    prompt = ConversationalAgent.create_prompt(
        tools, 
        prefix=prompt_dict["prefix"],
        suffix=prompt_dict["suffix"],
        input_variables=prompt_dict["input_variables"]
    )
    
    print("Agent初始化完成", prompt)

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
        max_iterations=6  # 限制最大迭代次数，避免无限循环
    )

    return agent_executor
