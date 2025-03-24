import json
import os
from datetime import date
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
from astrbot import logger
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.platform import AstrMessageEvent


PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_PATH = os.path.join(PLUGIN_DIR, "resource", "华文新魏.ttf")
BACKGROUND_PATH = os.path.join(PLUGIN_DIR, "resource", "background.png")
TEMP_DIR = os.path.join(PLUGIN_DIR, "temp")

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)


# 全局变量设置
FONT_SIZE = 20  # 字体大小
LINE_HEIGHT = 30  # 行高
MARGIN_LEFT = 40  # 左边距
MARGIN_RIGHT = 10  # 右边距
BACKGROUND_COLOR = 'white'  # 背景颜色
IMAGE_WIDTH = 550
IMAGE_HEIGHT = 450  # 固定背景图片高度
TOP_MARGIN = 10 # 顶部边缘

@register("历史上的今天", "Zhalslar", "饰乐插件", "1.0.0", "https://github.com/Zhalslar/astrbot_plugin_yuafeng_today_in_history")
class HistoryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.today_date_str = date.today().strftime("%Y_%m_%d")
    @filter.command("历史上的今天")
    async def handle_history_today(self, event: AstrMessageEvent):

        cache_file_path = os.path.join(TEMP_DIR, f"{self.today_date_str}.png")

        if os.path.exists(cache_file_path):
            yield event.image_result(cache_file_path)
            return
        try:
            async with aiohttp.ClientSession() as client:
                month = date.today().strftime("%m")
                day = date.today().strftime("%d")
                url = f"https://baike.baidu.com/cms/home/eventsOnHistory/{month}.json"
                response = await client.get(url)
                response.encoding = "utf-8"  # 修改编码为 utf-8
                text = await response.text()
                data = self.html_to_json_func(text=text)

                today = f"{month}{day}"
                f_today = f"{month.lstrip('0') or '0'}月{day.lstrip('0') or '0'}日"
                reply = f"【历史上的今天-{f_today}】\n"
                len_max = len(data[month][today])

                for i in range(len_max):
                    str_year = data[month][today][i]["year"]
                    str_title = data[month][today][i]["title"]
                    reply += f"{str_year} {str_title}" + ("\n" if i < len_max - 1 else "")

                image_path = self.text_to_image_path(reply)
                yield event.image_result(image_path)

        except Exception as e:
            logger.error(f"任务处理失败: {e}")


    @staticmethod
    def html_to_json_func(text: str) -> json:
        """处理返回的HTML内容，转换为JSON格式"""
        text = text.replace("<\/a>", "").replace("\n", "")

        while True:
            address_head = text.find("<a target=")
            address_end = text.find(">", address_head)
            if address_head == -1 or address_end == -1:
                break
            text_middle = text[address_head:address_end + 1]
            text = text.replace(text_middle, "")

        address_head = 0
        while True:
            address_head = text.find('"desc":', address_head)
            address_end = text.find('"cover":', address_head)
            if address_head == -1 or address_end == -1:
                break
            text_middle = text[address_head + 8:address_end - 2]
            address_head = address_end
            text = text.replace(text_middle, "")

        address_head = 0
        while True:
            address_head = text.find('"title":', address_head)
            address_end = text.find('"festival"', address_head)
            if address_head == -1 or address_end == -1:
                break
            text_middle = text[address_head + 9:address_end - 2]
            if '"' in text_middle:
                text_middle = text_middle.replace('"', " ")
                text = text[:address_head + 9] + text_middle + text[address_end - 2:]
            address_head = address_end

        return json.loads(text)

    def text_to_image_path(self, text: str) -> str:
        """将给定文本转换为图像，并返回图像的保存路径"""

        font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))

        lines = text.split('\n')
        max_width = 0
        total_height = 0

        # 计算整个文本的高度和每一行的最大宽度
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width, line_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            max_width = max(max_width, line_width)
            total_height += LINE_HEIGHT

        # 加载背景图片
        background_img = Image.open(BACKGROUND_PATH).resize((IMAGE_WIDTH, IMAGE_HEIGHT))
        draw = ImageDraw.Draw(background_img)

        y_text = TOP_MARGIN
        for line in lines:
            line_color = (random.randint(0, 64), random.randint(0, 16), random.randint(0, 32))
            draw.text((MARGIN_LEFT, y_text), line, fill=line_color, font=font)
            y_text += LINE_HEIGHT

        # 将图片保存
        image_path = os.path.join(TEMP_DIR, f"{self.today_date_str}.png")
        img_byte_arr = BytesIO()
        background_img.save(img_byte_arr, format='PNG')
        with open(image_path, 'wb') as f:
            f.write(img_byte_arr.getvalue())
        return image_path








