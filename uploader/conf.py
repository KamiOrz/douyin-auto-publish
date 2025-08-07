# -*- coding: utf-8 -*-
"""
配置文件
"""

# Chrome浏览器路径，如果为空则使用系统默认路径
LOCAL_CHROME_PATH = ""

# 是否使用Chrome浏览器（True使用Chrome，False使用Chromium）
USE_CHROME_BROWSER = True

# Playwright Chromium 路径（自动检测）
import os
from playwright.async_api import async_playwright

# 其他配置
BASE_DIR = "."

# Chromium 版本信息
CHROMIUM_VERSION = "139.0.7258.5"
PLAYWRIGHT_VERSION = "1.54.0"
