from langchain.agents import AgentExecutor, ZeroShotAgent, ConversationalAgent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_core.messages import SystemMessage, HumanMessage
from ..tools import get_current_time, search_tool, generate_and_execute_code, execute_python_code


def create_agent(llm, include_memory_info=None):
    """使用ConversationalAgent创建智能代理
    
    Args:
        llm: 语言模型实例
        include_memory_info: 可选的用户记忆信息，会被包含在提示词中
    """

    tools = [
        get_current_time,
        search_tool,
        generate_and_execute_code,
        execute_python_code
    ]

    # 构造工具描述字符串
    tools_description = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    
    # 构建系统提示词
    prefix = f"""你是一个智能助手，可以调用以下工具：

{tools_description}

"""

    # 添加用户记忆信息（如果存在）
    if include_memory_info:
        prefix += f"""
以下是关于当前用户的信息：
{include_memory_info}

请记住这些信息并在回答时利用它们提供个性化的回应。
"""

    # 添加历史消息处理提示
    prefix += """
下面是你与用户的对话历史，请记住这些信息，保持连贯性：

{chat_history}

"""

    # 创建 ConversationalAgent 模板
    prompt = ConversationalAgent.create_prompt(
        tools, 
        prefix=prefix,
        suffix="Question: {input}\n{agent_scratchpad}",
        input_variables=["input", "chat_history", "agent_scratchpad"]
    )

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
