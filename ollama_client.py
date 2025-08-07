#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama客户端 - 用于与qwen3:8b模型交互
"""

import requests
import json
import time
from typing import Optional

class OllamaClient:
    """Ollama客户端类"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
    
    def check_connection(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            print(f"连接Ollama失败: {e}")
            return False
    
    def check_model(self) -> bool:
        """检查模型是否可用"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                return self.model in model_names
            return False
        except Exception as e:
            print(f"检查模型失败: {e}")
            return False
    
    def generate_text(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """生成文本"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 40
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
                # 清理<think>标签
                return self.clean_think_tags(response_text)
            else:
                print(f"生成失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"生成文本时出错: {e}")
            return None
    
    def clean_think_tags(self, text: str) -> str:
        """清理<think>标签"""
        import re
        # 移除<think>...</think>标签及其内容
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # 移除单独的<think>标签
        text = re.sub(r'<think>', '', text)
        text = re.sub(r'</think>', '', text)
        return text.strip()
    
    def generate_video_title(self, filename: str, description: str = "") -> str:
        """生成视频标题"""
        prompt = f"""请用中文生成一个吸引人的视频标题，不要思考，直接输出。

视频文件名：{filename}
要求：
1. 必须使用中文
2. 标题要简洁明了，不超过20个字
3. 要有吸引力，适合在短视频平台发布
4. 不要包含特殊符号或emoji
5. 直接输出标题，不要其他内容

中文标题："""
        
        result = self.generate_text(prompt, max_tokens=50)
        if result:
            # 清理结果，只保留标题部分
            result = result.strip()
            # 移除可能的引号
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            if result.startswith("'") and result.endswith("'"):
                result = result[1:-1]
            return result
        else:
            return f"AI生成标题_{filename}"
    
    def generate_video_description(self, filename: str, title: str = "") -> str:
        """生成视频描述"""
        prompt = f"""请用中文生成一个吸引人的视频描述，不要思考，直接输出。

视频文件名：{filename}
要求：
1. 必须使用中文
2. 描述要简洁有趣，不超过100字
3. 要有吸引力，适合在短视频平台发布
4. 直接输出描述，不要其他内容

中文描述："""
        
        result = self.generate_text(prompt, max_tokens=150)
        if result:
            return result.strip()
        else:
            return f"这是一个关于{filename}的精彩视频，内容有趣，值得观看。"
    
    def test_connection(self) -> dict:
        """测试连接和模型"""
        result = {
            "connection": False,
            "model_available": False,
            "model_name": self.model,
            "base_url": self.base_url
        }
        
        # 测试连接
        if self.check_connection():
            result["connection"] = True
            print("✅ Ollama服务连接成功")
            
            # 测试模型
            if self.check_model():
                result["model_available"] = True
                print(f"✅ 模型 {self.model} 可用")
            else:
                print(f"❌ 模型 {self.model} 不可用")
                print("请确保已安装该模型：ollama pull qwen2.5:8b")
        else:
            print("❌ Ollama服务连接失败")
            print("请确保Ollama服务正在运行：ollama serve")
        
        return result
