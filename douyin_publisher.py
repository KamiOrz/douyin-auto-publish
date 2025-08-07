#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音发布器接口
用于对接批量发布功能到douyin_uploader/main.py
"""

import asyncio
import os
import sys
from datetime import datetime
import threading
from typing import Optional, List, Dict

# 添加本地uploader路径
sys.path.append('./uploader')

# 尝试导入发布器
try:
    from douyin_uploader.main import DouYinVideo, douyin_setup
    DOUYIN_PUBLISHER_AVAILABLE = True
    print("✅ 抖音发布器可用")
except ImportError as e:
    DOUYIN_PUBLISHER_AVAILABLE = False
    print(f"⚠️ 抖音发布器不可用: {e}")
    print("将使用模拟发布功能")


class DouyinPublisher:
    """抖音发布器"""
    
    def __init__(self, account_file: str = None):
        """
        初始化发布器
        
        Args:
            account_file: 账号cookie文件路径，如果为None则使用默认路径
        """
        if account_file is None:
            # 默认账号文件路径
            self.account_file = "./uploader/accounts/douyin_account.json"
        else:
            self.account_file = account_file
        
        self.is_initialized = False
        self.publish_queue = []
        self.current_publishing = False
    
    async def initialize(self) -> bool:
        """
        初始化发布器，检查cookie是否有效
        
        Returns:
            bool: 初始化是否成功
        """
        if not DOUYIN_PUBLISHER_AVAILABLE:
            print("❌ 抖音发布器不可用")
            return False
            
        try:
            # 检查账号设置
            success = await douyin_setup(self.account_file, handle=True)
            if success:
                self.is_initialized = True
                print("✅ 抖音发布器初始化成功")
                return True
            else:
                print("❌ 抖音发布器初始化失败")
                return False
        except Exception as e:
            print(f"❌ 抖音发布器初始化出错: {e}")
            return False
    
    def publish_video(self, video_info: Dict) -> bool:
        """
        发布单个视频
        
        Args:
            video_info: 视频信息字典，包含：
                - title: 视频标题
                - file_path: 视频文件路径
                - description: 视频描述
                - tags: 标签列表
                - publish_date: 发布时间（datetime对象，可选）
                - thumbnail_path: 封面图片路径（可选）
        
        Returns:
            bool: 发布是否成功
        """
        if not DOUYIN_PUBLISHER_AVAILABLE:
            print(f"⚠️ 模拟发布视频: {video_info.get('title', '未知标题')}")
            return True
            
        try:
            # 检查文件是否存在
            if not os.path.exists(video_info['file_path']):
                print(f"❌ 视频文件不存在: {video_info['file_path']}")
                return False
            
            # 创建发布任务
            title = video_info.get('title', '')
            file_path = video_info['file_path']
            tags = video_info.get('tags', [])
            publish_date = video_info.get('publish_date', 0)  # 0表示立即发布
            thumbnail_path = video_info.get('thumbnail_path')
            
            # 创建DouYinVideo对象
            douyin_video = DouYinVideo(
                title=title,
                file_path=file_path,
                tags=tags,
                publish_date=publish_date,
                account_file=self.account_file,
                thumbnail_path=thumbnail_path
            )
            
            # 运行发布任务
            asyncio.run(douyin_video.main())
            
            print(f"✅ 视频发布成功: {title}")
            return True
            
        except Exception as e:
            print(f"❌ 视频发布失败: {e}")
            return False
    
    def publish_videos_batch(self, video_list: List[Dict], progress_callback=None) -> Dict:
        """
        批量发布视频
        
        Args:
            video_list: 视频信息列表
            progress_callback: 进度回调函数，接收参数：(current, total, success_count, failed_count, current_success)
        
        Returns:
            Dict: 发布结果统计
        """
        if not self.is_initialized:
            print("❌ 发布器未初始化")
            return {"success": 0, "failed": 0, "total": len(video_list)}
        
        success_count = 0
        failed_count = 0
        total = len(video_list)
        
        print(f"🚀 开始批量发布 {total} 个视频...")
        
        for i, video_info in enumerate(video_list):
            current_success = False
            try:
                print(f"📤 正在发布第 {i+1}/{total} 个视频: {video_info.get('title', '未知标题')}")
                
                # 发布视频
                success = self.publish_video(video_info)
                
                if success:
                    success_count += 1
                    current_success = True
                else:
                    failed_count += 1
                
                # 调用进度回调，传递当前视频的发布结果
                if progress_callback:
                    progress_callback(i + 1, total, success_count, failed_count, current_success)
                
                # 发布间隔，避免频率过高
                if i < total - 1:  # 不是最后一个视频
                    print("⏳ 等待5秒后发布下一个视频...")
                    import time
                    time.sleep(5)
                
            except Exception as e:
                print(f"❌ 发布第 {i+1} 个视频时出错: {e}")
                failed_count += 1
                current_success = False
                
                if progress_callback:
                    progress_callback(i + 1, total, success_count, failed_count, current_success)
        
        result = {
            "success": success_count,
            "failed": failed_count,
            "total": total
        }
        
        print(f"📊 批量发布完成: 成功 {success_count} 个，失败 {failed_count} 个")
        return result
    
    def extract_tags_from_description(self, description: str) -> List[str]:
        """
        从描述中提取标签
        
        Args:
            description: 视频描述
            
        Returns:
            List[str]: 标签列表
        """
        tags = []
        
        # 简单的标签提取逻辑
        # 查找#开头的标签
        import re
        hashtags = re.findall(r'#(\w+)', description)
        tags.extend(hashtags)
        
        # 如果没有找到标签，使用默认标签
        if not tags:
            tags = ['电吉他伴奏', '吉他即兴伴奏', '伴奏']
        
        return tags[:5]  # 限制最多5个标签
    
    def create_publish_info(self, video_data: Dict) -> Dict:
        """
        从数据库视频信息创建发布信息
        
        Args:
            video_data: 数据库中的视频信息
            
        Returns:
            Dict: 发布信息
        """
        title = video_data.get('display_name', video_data.get('filename', ''))
        file_path = video_data.get('file_path', '')
        description = video_data.get('description', '')
        
        # 从描述中提取标签
        tags = self.extract_tags_from_description(description)
        
        # 创建发布信息
        publish_info = {
            'title': title+'\n\n'+description,
            'file_path': file_path,
            'description': description,
            'tags': tags,
            'publish_date': 0,  # 立即发布
            'thumbnail_path': None  # 暂时不使用封面
        }
        
        return publish_info


# 测试函数
async def test_douyin_publisher():
    """测试抖音发布器"""
    publisher = DouyinPublisher()
    
    # 初始化
    success = await publisher.initialize()
    if not success:
        print("❌ 发布器初始化失败")
        return
    
    # 测试发布信息创建
    video_data = {
        'display_name': '测试视频标题',
        'file_path': '/path/to/video.mp4',
        'description': '这是一个测试视频 #测试 #精彩内容',
        'filename': 'test_video.mp4'
    }
    
    publish_info = publisher.create_publish_info(video_data)
    print(f"📝 发布信息: {publish_info}")
    
    # 测试标签提取
    tags = publisher.extract_tags_from_description("这是一个测试视频 #测试 #精彩内容 #短视频")
    print(f"🏷️ 提取的标签: {tags}")


if __name__ == "__main__":
    asyncio.run(test_douyin_publisher())
