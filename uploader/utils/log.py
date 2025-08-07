# -*- coding: utf-8 -*-
"""
日志模块
"""

import logging

# 创建抖音日志记录器
douyin_logger = logging.getLogger('douyin')
douyin_logger.setLevel(logging.INFO)

# 如果没有处理器，添加一个控制台处理器
if not douyin_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    douyin_logger.addHandler(handler)
