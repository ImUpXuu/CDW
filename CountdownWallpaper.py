#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
倒计时壁纸生成器
功能：生成带有倒计时和励志语录的桌面壁纸
作者：UpXuu
GitHub: https://github.com/ImUpXuu
版本：2.2.0
"""

import os
import sys
import datetime
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont
import platform
import ctypes
from pathlib import Path
import json

# 配置文件路径
def get_resource_path(filename):
    """获取资源文件路径（兼容打包后的环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return Path(sys.executable).parent / filename
    else:
        # 开发环境
        return Path(__file__).parent / filename

CONFIG_FILE = get_resource_path("cdw.json")

print('倒计时壁纸生成器')
print('版本：2.2.0 | 作者：UpXuu | GitHub: https://github.com/ImUpXuu')
print('=' * 60)


def load_config():
    """加载配置文件"""
    if not CONFIG_FILE.exists():
        print("未找到配置文件，启动配置管理器...")
        start_manager()
        # 管理器关闭后重新检查
        if not CONFIG_FILE.exists():
            print("错误：配置文件仍未创建，无法生成壁纸")
            sys.exit(1)
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"配置文件读取失败：{e}")
        print("将启动配置管理器...")
        start_manager()
        # 重新读取
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)


def start_manager():
    """启动配置管理器（如果不存在则下载）"""
    manager_exe = get_resource_path("CDWManager.exe")
    
    # 检查管理器是否存在
    if not manager_exe.exists():
        print("未找到管理器，正在下载...")
        download_manager()
    
    # 启动管理器
    if manager_exe.exists():
        try:
            print("使用 exe 版管理器")
            subprocess.Popen([str(manager_exe)])
            print("配置管理器已启动，请完成配置后关闭管理器")
        except Exception as e:
            print(f"启动管理器失败：{e}")
    else:
        print("错误：未找到管理器")
        print("请手动下载 CDWManager.exe 到项目目录")


def download_manager():
    """下载管理器"""
    manager_exe = get_resource_path("CDWManager.exe")
    download_url = "https://raw-githubusercontent-com-gh.2x.nz/ImUpXuu/CDW/refs/heads/main/dist/CDWManager.exe"
    
    try:
        import requests
        print(f"下载地址：{download_url}")
        response = requests.get(download_url, stream=True, timeout=30)
        
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(manager_exe, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 显示进度
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r下载进度：{percent:.1f}%", end='')
            
            print(f"\n✓ 管理器下载完成：{manager_exe}")
        else:
            print(f"✗ 下载失败：HTTP {response.status_code}")
            
    except Exception as e:
        print(f"✗ 下载异常：{e}")
        print("请手动下载管理器到项目目录")


# 加载配置
config = load_config()

# 从配置中读取参数
countdowns = config.get('countdowns', [])
enabled_countdowns = []
if countdowns:
    for cd in countdowns:
        if cd.get('enabled', True):
            enabled_countdowns.append(cd)

if enabled_countdowns:
    # 第一个作为主倒计时
    main_countdown = enabled_countdowns[0]
    TARGET_DATE = datetime.datetime.strptime(main_countdown['date'], '%Y-%m-%d').date()
    COUNTDOWN_NAME = main_countdown.get('name', '目标')
    # 其他倒计时显示在右侧
    other_countdowns = enabled_countdowns[1:]
else:
    TARGET_DATE = datetime.date(2026, 6, 23)
    COUNTDOWN_NAME = '目标'
    other_countdowns = []

# 一言 API 配置
hitokoto_config = config.get('hitokoto', {})
HITOKOTO_CONFIG = {
    "api_url": "https://v1.hitokoto.cn",
    "timeout": 10,
    "types": hitokoto_config.get('types', ['d', 'i', 'k', 'l']),
}

# 壁纸配置
wallpaper_config = config.get('wallpaper', {})
FONT_CONFIG = {
    "custom_font_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), wallpaper_config.get('font_path', 'font.ttf')),
    "base_title_size": 80,
    "base_days_size": 270,
    "base_unit_size": 60,
    "base_week_size": 40,
    "base_inspire_size": 35,
}

COLOR_CONFIG = {
    "title_color": (25, 200, 253),
    "days_color": (25, 200, 253),
    "week_color": (180, 200, 255, 220),
    "inspire_color": (255, 255, 255),
    "shadow_color": (0, 0, 0, 180),
}

COPYRIGHT_CONFIG = {
    "text": "powered by UpXuu & 一言 API",
    "position": "bottom_left",
    "base_font_size": 16,
    "color": (150, 150, 150, 180),
}

TIME_CONFIG = {
    "show": True,
    "position": "bottom_left",
    "base_font_size": 14,
    "color": (180, 180, 180, 160),
    "format": "%Y-%m-%d %H:%M:%S",
}

BACKGROUND_CONFIG = {
    "enabled": True,
    "color": (173, 216, 230, 180),
    "horizontal_padding": 80,
    "vertical_padding": 50,
}

API_CONFIG = {
    "bing_urls": [
        "https://bing.img.run/uhd.php",
        "https://api.bimg.cc/random?mkt=zh-CN",
        "https://bing.biturl.top/?resolution=1920&format=image&index=0&mkt=zh-CN",
    ],
    "bing_timeout": 15,
}


class WallpaperGenerator:
    def __init__(self):
        self.wallpaper_dir = Path.home() / "CountdownWallpapers"
        self.wallpaper_dir.mkdir(exist_ok=True)
        
        self.screen_width, self.screen_height = self.get_resolution()
        self.scale_factor = self.calculate_scale_factor()
        self.font_sizes = self.calculate_font_sizes()
        self.setup_fonts()
        
    def get_resolution(self):
        """获取屏幕分辨率"""
        try:
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            return (width, height)
        except:
            return (1920, 1080)
    
    def calculate_scale_factor(self):
        """计算缩放比例"""
        scale = self.screen_width / 1920
        return max(0.7, min(scale, 2.0))
    
    def calculate_font_sizes(self):
        """计算字体大小"""
        sizes = {
            "title_size": int(FONT_CONFIG["base_title_size"] * self.scale_factor),
            "days_size": int(FONT_CONFIG["base_days_size"] * self.scale_factor),
            "unit_size": int(FONT_CONFIG["base_unit_size"] * self.scale_factor),
            "week_size": int(FONT_CONFIG["base_week_size"] * self.scale_factor),
            "inspire_size": int(FONT_CONFIG["base_inspire_size"] * self.scale_factor),
            "copyright_size": int(COPYRIGHT_CONFIG["base_font_size"] * self.scale_factor),
            "time_size": int(TIME_CONFIG["base_font_size"] * self.scale_factor),
        }
        return {k: max(10, min(v, 500)) for k, v in sizes.items()}
    
    def setup_fonts(self):
        """设置字体"""
        self.font_paths = []
        custom_font = FONT_CONFIG["custom_font_path"]
        
        if os.path.exists(custom_font):
            self.font_paths.append(custom_font)
        
        system_fonts = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
        
        for font_path in system_fonts:
            if os.path.exists(font_path):
                self.font_paths.append(font_path)
    
    def get_chinese_font(self, size):
        """获取中文字体"""
        for font_path in self.font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()
    
    def get_hitokoto_quote(self):
        """获取一言诗句"""
        if not hitokoto_config.get('enabled', True):
            return self.get_backup_quote()
        
        try:
            params = {}
            for type in HITOKOTO_CONFIG["types"]:
                params.setdefault('c', []).append(type)
            
            response = requests.get(
                HITOKOTO_CONFIG["api_url"],
                params=params,
                timeout=HITOKOTO_CONFIG["timeout"]
            )
            
            if response.status_code == 200:
                data = response.json()
                hitokoto = data.get('hitokoto', '')
                from_who = data.get('from_who', '')
                quote = f"{hitokoto} - {from_who}" if from_who else hitokoto
                return quote
        except:
            pass
        
        return self.get_backup_quote()
    
    def get_backup_quote(self):
        """备用诗句"""
        import random
        backup_quotes = [
            "锲而不舍，金石可镂 - 荀子",
            "少壮不努力，老大徒伤悲 - 《长歌行》",
            "天行健，君子以自强不息 - 《周易》",
            "宝剑锋从磨砺出，梅花香自苦寒来 - 警世贤文",
            "长风破浪会有时，直挂云帆济沧海 - 李白",
        ]
        return random.choice(backup_quotes)
    
    def get_bing_wallpaper(self):
        """获取 Bing 壁纸"""
        for i, bing_url in enumerate(API_CONFIG["bing_urls"]):
            try:
                response = requests.get(bing_url, timeout=API_CONFIG["bing_timeout"], stream=True)
                if response.status_code == 200:
                    temp_path = self.wallpaper_dir / f"bing_temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    image = Image.open(temp_path)
                    if image.size != (self.screen_width, self.screen_height):
                        image = image.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
                    
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    
                    return image
            except:
                continue
        
        return self.create_default_background()
    
    def create_default_background(self):
        """创建默认背景"""
        try:
            width = min(self.screen_width, 1920)
            height = min(self.screen_height, 1080)
            
            image = Image.new('RGB', (width, height), (25, 25, 112))
            draw = ImageDraw.Draw(image)
            
            import random
            for _ in range(50):
                x = random.randint(0, width)
                y = random.randint(0, height)
                size = random.randint(1, 2)
                brightness = random.randint(200, 255)
                draw.ellipse([x, y, x + size, y + size], fill=(brightness, brightness, brightness))
            
            if (width, height) != (self.screen_width, self.screen_height):
                image = image.resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
            
            return image
        except:
            return Image.new('RGB', (800, 600), (25, 25, 112))
    
    def calculate_days_left(self):
        """计算剩余天数"""
        today = datetime.date.today()
        return max(0, (TARGET_DATE - today).days)
    
    def calculate_weeks_left(self, days_left):
        """计算剩余周数"""
        return days_left / 7.0
    
    def draw_copyright_info(self, draw, width, height):
        """绘制版权信息"""
        if not COPYRIGHT_CONFIG.get("text"):
            return 0
        
        copyright_font = self.get_chinese_font(self.font_sizes["copyright_size"])
        copyright_text = COPYRIGHT_CONFIG["text"]
        copyright_bbox = draw.textbbox((0, 0), copyright_text, font=copyright_font)
        copyright_width = copyright_bbox[2] - copyright_bbox[0]
        copyright_height = copyright_bbox[3] - copyright_bbox[1]
        
        position = COPYRIGHT_CONFIG.get("position", "bottom_left")
        margin = int(10 * self.scale_factor)
        
        if position == "bottom_left":
            x, y = margin, height - copyright_height - margin
        elif position == "bottom_right":
            x, y = width - copyright_width - margin, height - copyright_height - margin
        elif position == "top_left":
            x, y = margin, margin
        elif position == "top_right":
            x, y = width - copyright_width - margin, margin
        else:
            x, y = margin, height - copyright_height - margin
        
        draw.text((x, y), copyright_text, fill=COPYRIGHT_CONFIG["color"], font=copyright_font)
        return copyright_height
    
    def draw_refresh_time(self, draw, width, height, copyright_height=0):
        """绘制刷新时间"""
        if not TIME_CONFIG.get("show", True):
            return
        
        time_font = self.get_chinese_font(self.font_sizes["time_size"])
        refresh_text = f"刷新时间：{datetime.datetime.now().strftime(TIME_CONFIG['format'])}"
        refresh_bbox = draw.textbbox((0, 0), refresh_text, font=time_font)
        refresh_width = refresh_bbox[2] - refresh_bbox[0]
        refresh_height = refresh_bbox[3] - refresh_bbox[1]
        
        position = TIME_CONFIG.get("position", "bottom_left")
        margin = int(10 * self.scale_factor)
        spacing = int(5 * self.scale_factor)
        
        if position == "bottom_left":
            x = margin
            y = height - refresh_height - margin
            if copyright_height > 0 and COPYRIGHT_CONFIG.get("position") == "bottom_left":
                y -= copyright_height + spacing
        elif position == "bottom_right":
            x = width - refresh_width - margin
            y = height - refresh_height - margin
            if copyright_height > 0 and COPYRIGHT_CONFIG.get("position") == "bottom_right":
                y -= copyright_height + spacing
        else:
            x, y = margin, margin
        
        draw.text((x, y), refresh_text, fill=TIME_CONFIG["color"], font=time_font)
    
    def create_countdown_overlay(self, background_image):
        """创建倒计时叠加层"""
        try:
            width, height = background_image.size
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            days_left = self.calculate_days_left()
            weeks_left = self.calculate_weeks_left(days_left)
            inspire_text = self.get_hitokoto_quote()
            
            title_font = self.get_chinese_font(self.font_sizes["title_size"])
            days_font = self.get_chinese_font(self.font_sizes["days_size"])
            unit_font = self.get_chinese_font(self.font_sizes["unit_size"])
            week_font = self.get_chinese_font(self.font_sizes["week_size"])
            inspire_font = self.get_chinese_font(self.font_sizes["inspire_size"])
            
            title = f"距离{COUNTDOWN_NAME}还有"
            days_text = f"{days_left}"
            unit_text = "天"
            week_text = f"≈ {weeks_left:.1f} 周"
            
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            days_bbox = draw.textbbox((0, 0), days_text, font=days_font)
            unit_bbox = draw.textbbox((0, 0), unit_text, font=unit_font)
            week_bbox = draw.textbbox((0, 0), week_text, font=week_font)
            inspire_bbox = draw.textbbox((0, 0), inspire_text, font=inspire_font)
            
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            days_width = days_bbox[2] - days_bbox[0]
            days_height = days_bbox[3] - days_bbox[1]
            unit_width = unit_bbox[2] - unit_bbox[0]
            unit_height = unit_bbox[3] - unit_bbox[1]
            week_width = week_bbox[2] - week_bbox[0]
            week_height = week_bbox[3] - week_bbox[1]
            inspire_width = inspire_bbox[2] - inspire_bbox[0]
            inspire_height = inspire_bbox[3] - inspire_bbox[1]
            
            spacing = int(30 * self.scale_factor)
            title_spacing = int(40 * self.scale_factor)
            week_spacing = int(20 * self.scale_factor)
            
            total_height = (title_height + days_height + week_height + inspire_height +
                            title_spacing + week_spacing + spacing * 2)
            start_y = (height - total_height) // 2
            current_y = start_y
            shadow_offset = int(4 * self.scale_factor)
            
            if BACKGROUND_CONFIG.get("enabled", True):
                bg_padding_h = int(BACKGROUND_CONFIG["horizontal_padding"] * self.scale_factor)
                bg_padding_v = int(BACKGROUND_CONFIG["vertical_padding"] * self.scale_factor)
                bg_width = max(title_width, days_width + unit_width + int(20 * self.scale_factor),
                               week_width, inspire_width) + bg_padding_h * 2
                bg_height = total_height + bg_padding_v * 2
                bg_x = (width - bg_width) // 2
                bg_y = start_y - bg_padding_v
                
                draw.rectangle([bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
                               fill=BACKGROUND_CONFIG["color"])
            
            title_x = (width - title_width) // 2
            draw.text((title_x + shadow_offset, current_y + shadow_offset), title,
                      fill=COLOR_CONFIG["shadow_color"], font=title_font)
            draw.text((title_x, current_y), title, fill=COLOR_CONFIG["title_color"], font=title_font)
            current_y += title_height + title_spacing
            
            combined_width = days_width + unit_width + int(20 * self.scale_factor)
            combined_x = (width - combined_width) // 2
            draw.text((combined_x + shadow_offset, current_y + shadow_offset), days_text,
                      fill=COLOR_CONFIG["shadow_color"], font=days_font)
            draw.text((combined_x, current_y), days_text, fill=COLOR_CONFIG["days_color"], font=days_font)
            
            unit_y = current_y + (days_height - unit_height) // 2
            unit_x = combined_x + days_width + int(20 * self.scale_factor)
            draw.text((unit_x + shadow_offset, unit_y + shadow_offset), unit_text,
                      fill=COLOR_CONFIG["shadow_color"], font=unit_font)
            draw.text((unit_x, unit_y), unit_text, fill=COLOR_CONFIG["title_color"], font=unit_font)
            current_y += days_height + week_spacing
            
            week_x = (width - week_width) // 2
            draw.text((week_x + shadow_offset, current_y + shadow_offset), week_text,
                      fill=COLOR_CONFIG["shadow_color"], font=week_font)
            draw.text((week_x, current_y), week_text, fill=COLOR_CONFIG["week_color"], font=week_font)
            current_y += week_height + spacing
            
            inspire_x = (width - inspire_width) // 2
            draw.text((inspire_x + shadow_offset, current_y + shadow_offset), inspire_text,
                      fill=COLOR_CONFIG["shadow_color"], font=inspire_font)
            draw.text((inspire_x, current_y), inspire_text, fill=COLOR_CONFIG["inspire_color"], font=inspire_font)
            current_y += inspire_height + spacing * 2
            
            if other_countdowns:
                other_font_size = max(14, int(self.font_sizes["inspire_size"] * 0.8))
                other_font = self.get_chinese_font(other_font_size)
                today = datetime.date.today()
                
                for cd in other_countdowns:
                    cd_name = cd.get('name', '目标')
                    cd_date = datetime.datetime.strptime(cd['date'], '%Y-%m-%d').date()
                    cd_days = max(0, (cd_date - today).days)
                    
                    other_text = f"{cd_name}：还剩 {cd_days} 天"
                    other_bbox = draw.textbbox((0, 0), other_text, font=other_font)
                    other_width = other_bbox[2] - other_bbox[0]
                    other_x = (width - other_width) // 2
                    
                    draw.text((other_x, current_y), other_text, fill=COLOR_CONFIG["inspire_color"], font=other_font)
                    current_y += other_font_size + spacing
            
            copyright_height = self.draw_copyright_info(draw, width, height)
            self.draw_refresh_time(draw, width, height, copyright_height)
            
            if background_image.mode != 'RGBA':
                background_image = background_image.convert('RGBA')
            result_image = Image.alpha_composite(background_image, overlay)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"countdown_{timestamp}.jpg"
            filepath = self.wallpaper_dir / filename
            result_image_rgb = result_image.convert('RGB')
            result_image_rgb.save(filepath, quality=95)
            
            return filepath
            
        except Exception as e:
            print(f"生成图片失败：{e}")
            return None
    
    def set_wallpaper(self, image_path):
        """设置壁纸"""
        try:
            SPI_SETDESKWALLPAPER = 0x0014
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDWININICHANGE = 0x02
            abs_path = str(Path(image_path).absolute())
            
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, abs_path,
                SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
            )
            return result
        except:
            return False
    
    def cleanup_old_files(self):
        """清理旧文件"""
        try:
            cutoff_time = datetime.datetime.now() - datetime.timedelta(days=3)
            for file_path in self.wallpaper_dir.glob("countdown_*.jpg"):
                file_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
        except:
            pass
    
    def generate(self):
        """生成壁纸"""
        days_left = self.calculate_days_left()
        weeks_left = days_left / 7.0
        print(f"目标：{COUNTDOWN_NAME}")
        print(f"剩余：{days_left} 天 ≈ {weeks_left:.1f} 周")
        
        try:
            background_image = self.get_bing_wallpaper()
            wallpaper_path = self.create_countdown_overlay(background_image)
            
            if wallpaper_path:
                if self.set_wallpaper(wallpaper_path):
                    self.cleanup_old_files()
                    print(f"壁纸已更新：{wallpaper_path}")
                    return True
            return False
            
        except Exception as e:
            print(f"生成失败：{e}")
            return False


def main():
    """主函数"""
    generator = WallpaperGenerator()
    success = generator.generate()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
