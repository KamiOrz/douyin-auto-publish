#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频管理系统启动脚本
"""

import sys
import os

def main():
    """主函数"""
    try:
        # 检查Python版本
        if sys.version_info < (3, 7):
            print("错误: 需要Python 3.7或更高版本")
            sys.exit(1)
        
        # 导入并运行视频管理器
        from video_manager_improved import VideoManager
        
        print("正在启动视频管理系统...")
        app = VideoManager()
        app.run()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖包: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
