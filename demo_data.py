#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示数据生成脚本
用于测试视频管理系统的各项功能
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_demo_data():
    """创建演示数据"""
    # 连接数据库
    conn = sqlite3.connect('videos.db')
    cursor = conn.cursor()
    
    # 确保表存在
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            display_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT '未发布',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 演示视频数据
    demo_videos = [
        {
            'filename': 'demo_video_1.mp4',
            'display_name': '精彩生活片段',
            'file_path': '/Users/demo/Videos/demo_video_1.mp4',
            'description': '这是一个关于日常生活的精彩视频，记录了美好时光。',
            'status': '未发布'
        },
        {
            'filename': 'demo_video_2.mp4',
            'display_name': '美食制作教程',
            'file_path': '/Users/demo/Videos/demo_video_2.mp4',
            'description': '详细的美食制作过程，从准备材料到成品展示，步骤清晰易懂。',
            'status': '已发布'
        },
        {
            'filename': 'demo_video_3.mp4',
            'display_name': '旅行vlog',
            'file_path': '/Users/demo/Videos/demo_video_3.mp4',
            'description': '记录了一次难忘的旅行经历，美丽的风景和有趣的故事。',
            'status': '发布失败'
        },
        {
            'filename': 'demo_video_4.mp4',
            'display_name': '技术分享',
            'file_path': '/Users/demo/Videos/demo_video_4.mp4',
            'description': '分享一些实用的技术技巧和心得体会，希望对大家有帮助。',
            'status': '未发布'
        },
        {
            'filename': 'demo_video_5.mp4',
            'display_name': '音乐表演',
            'file_path': '/Users/demo/Videos/demo_video_5.mp4',
            'description': '精彩的音乐表演，展现了音乐的魅力。',
            'status': '已发布'
        },
        {
            'filename': 'demo_video_6.mp4',
            'display_name': '运动健身',
            'file_path': '/Users/demo/Videos/demo_video_6.mp4',
            'description': '专业的健身指导，帮助你保持健康的生活方式。',
            'status': '未发布'
        },
        {
            'filename': 'demo_video_7.mp4',
            'display_name': '手工艺术',
            'file_path': '/Users/demo/Videos/demo_video_7.mp4',
            'description': '精美的手工艺术作品制作过程，展现了创作者的匠心。',
            'status': '已发布'
        },
        {
            'filename': 'demo_video_8.mp4',
            'display_name': '宠物日常',
            'file_path': '/Users/demo/Videos/demo_video_8.mp4',
            'description': '可爱的宠物日常，记录了它们的有趣瞬间。',
            'status': '发布失败'
        }
    ]
    
    # 清空现有数据
    cursor.execute('DELETE FROM videos')
    
    # 插入演示数据
    for i, video in enumerate(demo_videos):
        # 生成不同的创建时间
        created_at = datetime.now() - timedelta(days=random.randint(1, 30))
        
        cursor.execute('''
            INSERT INTO videos (filename, display_name, file_path, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            video['filename'],
            video['display_name'],
            video['file_path'],
            video['description'],
            video['status'],
            created_at.strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    conn.close()
    
    print(f"已创建 {len(demo_videos)} 个演示视频数据")
    print("演示数据包括：")
    print("- 未发布状态: 3个视频")
    print("- 已发布状态: 3个视频") 
    print("- 发布失败状态: 2个视频")
    print("\n现在可以运行程序查看效果：")
    print("python video_manager_improved.py")

if __name__ == "__main__":
    create_demo_data()
