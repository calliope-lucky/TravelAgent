import asyncio
import logging
import pathlib
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
    ModelCallLimitMiddleware,
    SummarizationMiddleware
)
from langgraph.checkpoint.memory import MemorySaver

from sub_agents import SubAgent
from config import Config
from mcp_config import (
    TRAIN_MCP_CONFIG,
    HOTEL_MCP_CONFIG,
    ATTRACTIONS_MCP_CONFIG,
    FOOD_MCP_CONFIG,
)


# 项目根目录（mcp_config.py 所在目录）
PROJECT_ROOT = pathlib.Path(__file__).parent


def load_prompt(relative_path):
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


system_prompt = load_prompt("prompts/main_agent_prompt.txt")
train_prompt = load_prompt("prompts/train_agent_prompt.txt")
hotel_prompt = load_prompt("prompts/hotel_agent_prompt.txt")
attractions_prompt = load_prompt("prompts/attractions_agent_prompt.txt")
food_prompt = load_prompt("prompts/food_agent_prompt.txt")


my_loggers = [
    logging.getLogger("main_agent"),
    logging.getLogger("train_agent"),
    logging.getLogger("hotel_agent"),
    logging.getLogger("attractions_agent"),
    logging.getLogger("food_agent"),
]
file_handler = logging.FileHandler("logs/dialogue.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

for logger in my_loggers:
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

model = ChatOpenAI(
    openai_api_base=Config.OPENAI_API_BASE,
    openai_api_key=Config.OPENAI_API_KEY,
    model_name=Config.MAIN_MODEL_NAME,
)
executor_model = ChatOpenAI(
    openai_api_base=Config.OPENAI_API_BASE,
    openai_api_key=Config.OPENAI_API_KEY,
    model_name=Config.EXECUTOR_MODEL_NAME,
)

tool_retry_middleware = ToolRetryMiddleware(
    max_retries=2, backoff_factor=2.0, initial_delay=1.0, max_delay=4.0, jitter=True
)
tool_call_limit_middleware = ToolCallLimitMiddleware(
    tool_name="maps_search_detail", run_limit=15, exit_behavior="continue"
)
model_call_limit_middleware = ModelCallLimitMiddleware(
    run_limit=10, exit_behavior="end"
)
summarization_middleware = SummarizationMiddleware(
    model=model,
    trigger=("tokens", 100000),
    keep=("tokens", 25000)
)


train_agent = SubAgent(
    name="train_agent",
    description="获取火车票信息, 请输入关于火车票查询的问题，问题中需包含出发地、目的地和具体日期",
    system_prompt=train_prompt,
    mcp_config=TRAIN_MCP_CONFIG,
    model=executor_model,
    logger=my_loggers[1],
    middlewares=[tool_retry_middleware, model_call_limit_middleware],
)

hotel_agent = SubAgent(
    name="hotel_agent",
    description="获取酒店信息, 请输入关于酒店查询的问题，问题中需包含城市名称",
    system_prompt=hotel_prompt,
    mcp_config=HOTEL_MCP_CONFIG,
    model=executor_model,
    logger=my_loggers[2],
    middlewares=[tool_retry_middleware, tool_call_limit_middleware, model_call_limit_middleware],
    allowed_tools={"maps_around_search", "maps_search_detail", "maps_geo"},
)

attractions_agent = SubAgent(
    name="attractions_agent",
    description="获取景点信息, 请输入关于景点查询的问题，问题中需包含城市名称",
    system_prompt=attractions_prompt,
    mcp_config=ATTRACTIONS_MCP_CONFIG,
    model=executor_model,
    logger=my_loggers[3],
    middlewares=[tool_retry_middleware, model_call_limit_middleware],
)

food_agent = SubAgent(
    name="food_agent",
    description="获取美食信息, 请输入关于美食查询的问题，问题中需包含城市名称",
    system_prompt=food_prompt,
    mcp_config=FOOD_MCP_CONFIG,
    model=executor_model,
    logger=my_loggers[4],
    middlewares=[tool_retry_middleware, model_call_limit_middleware],
)

call_train_agent = train_agent.create_tool()
call_hotel_agent = hotel_agent.create_tool()
call_attractions_agent = attractions_agent.create_tool()
call_food_agent = food_agent.create_tool()


agent = create_agent(
    model,
    tools=[
        call_train_agent,
        call_hotel_agent,
        call_attractions_agent,
        call_food_agent,
    ],
    checkpointer=MemorySaver(),
    middleware=[summarization_middleware]
)


async def chat(message, thread_id = "1", is_first_message = False):
    config = {"configurable": {"thread_id": thread_id}}
    
    if is_first_message:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
    else:
        messages = [{"role": "user", "content": message}]
    
    result = await agent.ainvoke({"messages": messages}, config=config)
    model_output = result["messages"]
    for msg in model_output:
        my_loggers[0].info(f"msg.type: {msg.type}")
        my_loggers[0].info(f"msg.content: {msg.content}")
        if hasattr(msg, "tool_calls"):
            my_loggers[0].info(f"msg.tool_calls: {msg.tool_calls}")
    return result["messages"][-1].content


async def stream_chat(message, thread_id = "1", is_first_message = False):
    config = {"configurable": {"thread_id": thread_id}}
    
    if is_first_message:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
    else:
        messages = [{"role": "user", "content": message}]
    
    # 记录用户输入
    my_loggers[0].info(f"[Stream] User input: {message}")
    
    # 标记为流式输出
    my_loggers[0].info("[Stream] === Stream chat started ===")
    
    tool_names = {
        "train_agent": "火车票查询",
        "hotel_agent": "酒店查询",
        "attractions_agent": "景点查询",
        "food_agent": "美食查询",
    }
    
    seen_tool_calls = set()
    collected_messages = []  # 收集所有消息用于日志
    current_chunk_content = []  # 合并连续的 AIMessageChunk
    
    async for token, metadata in agent.astream({"messages": messages}, config=config, stream_mode="messages"):
        node = metadata.get("langgraph_node", "")
        
        if node == "model":
            if token.content:
                # 检查是否是连续的 AIMessageChunk，如果是则合并
                msg_type_name = type(token).__name__
                if msg_type_name == "AIMessageChunk":
                    current_chunk_content.append(token.content)
                else:
                    # 如果不是 chunk，先保存之前合并的内容
                    if current_chunk_content:
                        collected_messages.append({
                            "type": "ai",
                            "content": "".join(current_chunk_content),
                            "tool_calls": None
                        })
                        current_chunk_content = []
                    collected_messages.append(token)
                yield {"type": "text", "content": token.content}
            elif hasattr(token, "tool_calls") and token.tool_calls:
                # 先保存之前合并的 chunk 内容
                if current_chunk_content:
                    collected_messages.append({
                        "type": "ai",
                        "content": "".join(current_chunk_content),
                        "tool_calls": None
                    })
                    current_chunk_content = []
                
                for tool_call in token.tool_calls:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "")
                        tool_id = tool_call.get("id", "")
                    else:
                        tool_name = getattr(tool_call, "name", "")
                        tool_id = getattr(tool_call, "id", "")
                    
                    if not tool_name:
                        continue
                    
                    call_key = f"{tool_name}_{tool_id}"
                    if call_key in seen_tool_calls:
                        continue
                    seen_tool_calls.add(call_key)
                    
                    display_name = tool_names.get(tool_name, tool_name)
                    yield {"type": "tool", "name": display_name, "tool_name": tool_name}
        
        elif node == "tools":
            # 先保存之前合并的 chunk 内容
            if current_chunk_content:
                collected_messages.append({
                    "type": "ai",
                    "content": "".join(current_chunk_content),
                    "tool_calls": None
                })
                current_chunk_content = []
            
            if hasattr(token, "name") and token.name:
                collected_messages.append(token)
                tool_name = tool_names.get(token.name, token.name)
                content = token.content if hasattr(token, "content") else ""
                yield {"type": "tool_result", "name": tool_name, "content": content, "tool_name": token.name}
    
    # 最后保存剩余的 chunk 内容
    if current_chunk_content:
        collected_messages.append({
            "type": "ai",
            "content": "".join(current_chunk_content),
            "tool_calls": None
        })
    
    # 流式结束后，统一记录日志（与子智能体日志格式一致）
    my_loggers[0].info("[Stream] === Stream chat ended ===")
    
    for msg in collected_messages:
        # 处理合并后的消息对象或原始 token
        if isinstance(msg, dict):
            msg_type = msg["type"]
            msg_content = msg["content"]
            msg_tool_calls = msg["tool_calls"]
        else:
            # 对于原始 token，使用 type() 获取真实类型名称
            msg_type = type(msg).__name__
            msg_content = getattr(msg, 'content', '')
            msg_tool_calls = getattr(msg, "tool_calls", None)
        
        my_loggers[0].info(f"msg.type: {msg_type}")
        my_loggers[0].info(f"msg.content: {msg_content}")
        if msg_tool_calls:
            my_loggers[0].info(f"msg.tool_calls: {msg_tool_calls}")


async def main():
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "我想五一劳动节之后(2026-05-07)从南京出发，到南昌，玩三天，一个人"},
    ]
    result = await chat(messages[-1]["content"], is_first_message=True)
    print(f"model:\n{result}")
    
    while True:
        user_input = input("user:\n")
        if user_input == "exit":
            print("model:\nbye!")
            break
        result = await chat(user_input)
        print(f"model:\n{result}")


if __name__ == "__main__":
    asyncio.run(main())
