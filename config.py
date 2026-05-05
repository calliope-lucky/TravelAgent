import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置类"""

    # OpenAI API 配置
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.ant-ling.com/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # 模型配置
    MAIN_MODEL_NAME = os.getenv("MAIN_MODEL_NAME", "Ling-2.6-1T")
    EXECUTOR_MODEL_NAME = os.getenv("EXECUTOR_MODEL_NAME", "Ling-2.6-flash")


# 导入时自动验证
if not Config.OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 未设置，请在 .env 文件中配置")
