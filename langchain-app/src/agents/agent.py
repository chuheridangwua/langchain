from langchain.agents import AgentExecutor, ZeroShotAgent
from langchain.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_core.messages import SystemMessage, HumanMessage
from ..tools import get_current_time, search_tool, generate_and_execute_code, execute_python_code


def create_agent(llm, include_memory_info=None):
    """使用中文提示词和 ZeroShotAgent 创建智能代理（ReAct 风格）
    
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

    # 构造工具描述字符串（供 prompt 展示）
    tools_description = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
    
    # 创建系统消息内容
    system_message_content = f"""你是一个智能助手，可以调用以下工具：

{tools_description}

"""

    # 添加用户记忆信息（如果存在）
    if include_memory_info:
        system_message_content += f"""
以下是关于当前用户的信息：
{include_memory_info}

请在回答时利用这些信息提供个性化的回应。
"""

    # 添加代理格式指导
    system_message_content += """
请严格按照以下格式进行输出：

Question: 用户的问题
Thought: 你的推理
Action: 工具名称
Action Input: 要传给工具的输入内容
Observation: 工具输出的内容
...（可多轮）
Thought: 对结果的进一步思考
Final Answer: 给用户的最终答案
"""

    # 使用更现代的聊天模板方法
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_message_content),
        MessagesPlaceholder(variable_name="chat_history"),  # 聊天历史占位符
        HumanMessage(content="{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    # 使用旧的ZeroShotAgent，但使用新的提示模板
    agent = ZeroShotAgent(
        llm_chain=LLMChain(llm=llm, prompt=prompt),
        tools=tools,
        verbose=True
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        handle_parsing_errors=True
    )

    return agent_executor
