import json
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from pathlib import Path

# 获取项目根目录（mcp_data 的父目录）
PROJECT_ROOT = Path(__file__).parent.parent

mcp = FastMCP("FoodTools")


def load_food_data() -> Dict:
    """加载美食数据"""
    try:
        with open("mcp_data/sample_food.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load_restaurant_data() -> Dict:
    """加载餐厅数据"""
    try:
        with open("mcp_data/sample_restaurants.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@mcp.tool()
def get_food_info(city: str) -> List[Dict[str, object]] | str:
    """
    获取某个城市的特色美食信息

    :param city: 城市名称，如"成都"、"西安"、"杭州"等
    :type city: str
    :return: 包含美食信息的列表，每项包含美食名称、介绍和推荐餐厅
    :rtype: List[Dict[str, object]]
    """
    data = load_food_data()

    if city not in data:
        available_cities = list(data.keys())
        return f"未找到该城市的美食信息！可用城市：{', '.join(available_cities)}"

    return data[city]


@mcp.tool()
def get_restaurant_info(city: str) -> List[Dict[str, str]] | str:
    """
    获取城市的餐厅、饭店信息

    :param city: 城市名，如"北京"、"上海"、"广州"等
    :type city: str
    :return: 包含餐厅饭店信息的字典列表，包含名称、地址、评分、人均价格和特色菜
    :rtype: List[Dict[str, str]]
    """
    data = load_restaurant_data()

    if city not in data:
        available_cities = list(data.keys())
        return f"未找到该城市的餐厅信息！可用城市：{', '.join(available_cities)}"

    return data[city]


if __name__ == "__main__":
    mcp.run(transport="stdio")
