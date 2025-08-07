#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频管理系统配置文件
"""

import os
import json

class Config:
    """配置管理类"""
    
    def __init__(self):
        self.config_file = 'config.json'
        self.default_config = {
            'database': {
                'path': 'videos.db',
                'backup_enabled': True,
                'backup_interval': 7  # 天
            },
            'ui': {
                'window_size': '1200x800',
                'theme': 'default',
                'language': 'zh_CN'
            },
            'ai': {
                'ollama_url': 'http://localhost:11434',
                'model': 'llama2',
                'enabled': False
            },
            'publish': {
                'douyin': {
                    'enabled': False,
                    'api_key': '',
                    'api_secret': ''
                },
                'bilibili': {
                    'enabled': False,
                    'api_key': '',
                    'api_secret': ''
                }
            },
            'video': {
                'supported_formats': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'],
                'max_file_size': 1024 * 1024 * 1024,  # 1GB
                'auto_generate_description': True,
                'auto_generate_name': False
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    return self.merge_config(self.default_config, config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_config
        else:
            # 创建默认配置文件
            self.save_config(self.default_config)
            return self.default_config
    
    def save_config(self, config=None):
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def merge_config(self, default, user):
        """合并配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def get_supported_formats(self):
        """获取支持的视频格式"""
        return self.get('video.supported_formats', ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'])
    
    def get_database_path(self):
        """获取数据库路径"""
        return self.get('database.path', 'videos.db')
    
    def is_ai_enabled(self):
        """检查AI功能是否启用"""
        return self.get('ai.enabled', False)
    
    def get_ollama_config(self):
        """获取Ollama配置"""
        return {
            'url': self.get('ai.ollama_url', 'http://localhost:11434'),
            'model': self.get('ai.model', 'llama2')
        }
    
    def get_publish_config(self, platform):
        """获取发布平台配置"""
        return self.get(f'publish.{platform}', {})
    
    def update_ui_config(self, window_size=None, theme=None):
        """更新UI配置"""
        if window_size:
            self.set('ui.window_size', window_size)
        if theme:
            self.set('ui.theme', theme)

# 全局配置实例
config = Config()
