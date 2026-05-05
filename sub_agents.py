from typing import Dict, Any, List, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient


class SubAgent:
    """
    子智能体基类
    封装了通用的子智能体调用逻辑
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        mcp_config: Dict[str, Any],
        model: ChatOpenAI,
        logger: Optional[logging.Logger] = None,
        middlewares: Optional[List] = None,
        allowed_tools: Optional[set] = None,
    ):
        """
        初始化子智能体
        
        Args:
            name: 智能体名称（用作工具名称）
            description: 工具描述
            system_prompt: 系统提示词
            mcp_config: MCP服务器配置
            model: 执行器模型
            logger: 日志记录器
            middlewares: 中间件列表
            allowed_tools: 允许使用的工具名称集合，None 表示使用所有工具
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.mcp_config = mcp_config
        self.model = model
        self.logger = logger
        self.middlewares = middlewares or []
        self.allowed_tools = allowed_tools
    
    async def invoke(self, question: str) -> str:
        """
        调用子智能体执行任务
        
        Args:
            question: 用户问题
            
        Returns:
            智能体的回复内容
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": question},
        ]
        
        client = MultiServerMCPClient(self.mcp_config)
        tools = await client.get_tools()
        if self.allowed_tools:
            tools = [t for t in tools if getattr(t, "name", "") in self.allowed_tools]
        
        agent = create_agent(
            self.model,
            tools=tools,
            middleware=self.middlewares,
        )
        
        result = await agent.ainvoke({"messages": messages})
        
        if self.logger:
            self._log_result(result["messages"])
        
        return result["messages"][-1].content
    
    def _log_result(self, messages: List) -> None:
        """记录执行结果日志"""
        for msg in messages:
            self.logger.info(f"msg.type: {msg.type}")
            self.logger.info(f"msg.content: {msg.content}")
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                self.logger.info(f"msg.tool_calls: {msg.tool_calls}")
    
    def create_tool(self):
        """
        创建可用于主智能体的工具函数
        
        Returns:
            被@tool装饰的异步函数
        """
        @tool(self.name, description=self.description)
        async def tool_func(question: str) -> str:
            return await self.invoke(question)
        
        tool_func.__name__ = f"call_{self.name}"
        tool_func.__doc__ = self.description
        
        return tool_func
