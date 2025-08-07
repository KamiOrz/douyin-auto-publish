import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import threading
from datetime import datetime
import json
from ollama_client import OllamaClient
import asyncio
import sys

# 添加发布器路径
try:
    from douyin_publisher import DouyinPublisher
    DOUYIN_PUBLISHER_AVAILABLE = True
except ImportError:
    DOUYIN_PUBLISHER_AVAILABLE = False
    print("⚠️ 抖音发布器不可用，将使用模拟发布功能")

class VideoManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("抖音自动发布工具")
        self.root.geometry("1200x800")
        
        # 数据库初始化
        self.init_database()
        
        # 初始化Ollama客户端
        self.init_ollama()
        
        # 创建界面
        self.create_widgets()
        
        # 加载视频列表
        self.load_video_list()
    
    def init_database(self):
        """初始化数据库"""
        self.db_path = 'videos.db'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建视频表
        self.cursor.execute('''
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
        self.conn.commit()
    
    def init_ollama(self):
        """初始化Ollama客户端"""
        try:
            self.ollama_client = OllamaClient()
            # 测试连接
            test_result = self.ollama_client.test_connection()
            if test_result["connection"] and test_result["model_available"]:
                self.ai_enabled = True
                print("✅ AI功能已启用")
                # 更新AI状态显示
                if hasattr(self, 'ai_status_var'):
                    self.ai_status_var.set("AI: 已启用")
            else:
                self.ai_enabled = False
                print("⚠️ AI功能未启用，将使用模拟功能")
                # 更新AI状态显示
                if hasattr(self, 'ai_status_var'):
                    self.ai_status_var.set("AI: 未启用")
        except Exception as e:
            self.ai_enabled = False
            print(f"⚠️ Ollama初始化失败: {e}")
            print("将使用模拟AI功能")
            # 更新AI状态显示
            if hasattr(self, 'ai_status_var'):
                self.ai_status_var.set("AI: 连接失败")
    
    def create_widgets(self):
        """创建GUI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制区域
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 左侧按钮区域
        left_buttons = ttk.Frame(control_frame)
        left_buttons.pack(side=tk.LEFT)
        
        # 添加视频按钮
        self.add_videos_btn = ttk.Button(left_buttons, text="添加视频", command=self.add_videos)
        self.add_videos_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.add_folder_btn = ttk.Button(left_buttons, text="添加文件夹", command=self.add_folder)
        self.add_folder_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 批量操作按钮
        self.batch_publish_btn = ttk.Button(left_buttons, text="批量发布", command=self.batch_publish)
        self.batch_publish_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.batch_ai_btn = ttk.Button(left_buttons, text="批量AI智能描述", command=self.batch_ai_description)
        self.batch_ai_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.delete_btn = ttk.Button(left_buttons, text="删除选中", command=self.delete_selected)
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_all_btn = ttk.Button(left_buttons, text="全选", command=self.select_all)
        self.select_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.deselect_all_btn = ttk.Button(left_buttons, text="取消全选", command=self.deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧筛选区域
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(side=tk.RIGHT)
        
        # AI状态指示器
        ai_status_frame = ttk.Frame(filter_frame)
        ai_status_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.ai_status_var = tk.StringVar()
        self.ai_status_var.set("AI: 检查中...")
        ai_status_label = ttk.Label(ai_status_frame, textvariable=self.ai_status_var, 
                                   foreground="blue" if hasattr(self, 'ai_enabled') and self.ai_enabled else "red")
        ai_status_label.pack(side=tk.LEFT)
        
        ttk.Label(filter_frame, text="状态筛选:").pack(side=tk.LEFT)
        self.status_filter = ttk.Combobox(filter_frame, values=["全部", "未发布", "已发布", "发布失败"], 
                                         state="readonly", width=10)
        self.status_filter.set("全部")
        self.status_filter.pack(side=tk.LEFT, padx=(5, 0))
        self.status_filter.bind('<<ComboboxSelected>>', self.filter_videos)
        
        # 视频列表区域
        list_frame = ttk.LabelFrame(main_frame, text="视频列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建树形视图
        columns = ("选择", "ID", "显示名称", "描述", "文件名", "状态", "创建时间")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题和宽度
        self.tree.heading("选择", text="选择")
        self.tree.heading("ID", text="ID")
        self.tree.heading("显示名称", text="显示名称")
        self.tree.heading("描述", text="描述")
        self.tree.heading("文件名", text="文件名")
        self.tree.heading("状态", text="状态")
        self.tree.heading("创建时间", text="创建时间")
        
        self.tree.column("选择", width=50, anchor="center")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("显示名称", width=200)
        self.tree.column("描述", width=300)
        self.tree.column("文件名", width=200)
        self.tree.column("状态", width=100, anchor="center")
        self.tree.column("创建时间", width=150, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定事件
        self.tree.bind("<Double-1>", self.edit_video)
        self.tree.bind("<Button-1>", self.on_tree_click)
        
        # 设置标签样式
        self.tree.tag_configure("published", background="#90EE90")  # 浅绿色
        self.tree.tag_configure("failed", background="#FFB6C1")    # 浅红色
        self.tree.tag_configure("processing", background="#87CEEB")  # 浅蓝色 - 处理中
        
        # 底部状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # 初始化按钮状态
        self.is_processing = False
    
    def disable_buttons(self):
        """禁用所有按钮"""
        self.is_processing = True
        self.add_videos_btn.config(state="disabled")
        self.add_folder_btn.config(state="disabled")
        self.batch_publish_btn.config(state="disabled")
        self.batch_ai_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")
        self.select_all_btn.config(state="disabled")
        self.deselect_all_btn.config(state="disabled")
        self.status_filter.config(state="disabled")
        # Treeview不支持state选项，通过禁用事件来防止交互
        self.tree.unbind("<Double-1>")
        self.tree.unbind("<Button-1>")
    
    def enable_buttons(self):
        """启用所有按钮"""
        self.is_processing = False
        self.add_videos_btn.config(state="normal")
        self.add_folder_btn.config(state="normal")
        self.batch_publish_btn.config(state="normal")
        self.batch_ai_btn.config(state="normal")
        self.delete_btn.config(state="normal")
        self.select_all_btn.config(state="normal")
        self.deselect_all_btn.config(state="normal")
        self.status_filter.config(state="readonly")
        # 重新绑定Treeview事件
        self.tree.bind("<Double-1>", self.edit_video)
        self.tree.bind("<Button-1>", self.on_tree_click)
    
    def on_tree_click(self, event):
        """处理树形视图点击事件"""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1":  # 选择列
                item = self.tree.identify_row(event.y)
                if item:
                    self.toggle_selection(item)
                    return "break"  # 阻止默认行为
    
    def toggle_selection(self, item):
        """切换选择状态"""
        values = list(self.tree.item(item)['values'])
        if values[0] == "□":
            values[0] = "☑"
        else:
            values[0] = "□"
        self.tree.item(item, values=values)
    
    def select_all(self):
        """全选"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            values[0] = "☑"
            self.tree.item(item, values=values)
    
    def deselect_all(self):
        """取消全选"""
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            values[0] = "□"
            self.tree.item(item, values=values)
    
    def add_videos(self):
        """批量添加视频文件"""
        # 禁用按钮
        self.disable_buttons()
        
        files = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                ("所有文件", "*.*")
            ]
        )
        
        if files:
            # 批量处理所有文件
            added_count = 0
            skipped_count = 0
            error_count = 0
            
            # 批量检查已存在的文件
            file_paths = []
            valid_files = []
            
            for file_path in files:
                if os.path.exists(file_path):
                    file_paths.append(file_path)
                    valid_files.append(file_path)
                else:
                    error_count += 1
            
            if file_paths:
                # 批量查询已存在的文件
                placeholders = ','.join(['?' for _ in file_paths])
                self.cursor.execute(f"SELECT file_path FROM videos WHERE file_path IN ({placeholders})", file_paths)
                existing_paths = {row[0] for row in self.cursor.fetchall()}
                
                # 准备批量插入的数据
                batch_data = []
                for file_path in valid_files:
                    if file_path not in existing_paths:
                        filename = os.path.basename(file_path)
                        display_name = os.path.splitext(filename)[0]
                        description = f"这是一个关于{filename}的视频，内容精彩有趣。"
                        batch_data.append((filename, display_name, file_path, description))
                    else:
                        skipped_count += 1
                
                # 批量插入新文件
                if batch_data:
                    self.cursor.executemany('''
                        INSERT INTO videos (filename, display_name, file_path, description)
                        VALUES (?, ?, ?, ?)
                    ''', batch_data)
                    self.conn.commit()
                    added_count = len(batch_data)
            
            self.load_video_list()
            
            # 显示添加结果
            message = f"批量添加完成: 成功添加 {added_count} 个视频"
            if skipped_count > 0:
                message += f"，跳过 {skipped_count} 个重复文件"
            if error_count > 0:
                message += f"，失败 {error_count} 个文件"
            
            self.status_var.set(message)
            
            # 启用按钮
            self.enable_buttons()
    
    def add_single_video(self, file_path):
        """添加单个视频到数据库"""
        filename = os.path.basename(file_path)
        display_name = os.path.splitext(filename)[0]  # 默认使用文件名（不含扩展名）
        
        # 检查是否已存在
        self.cursor.execute("SELECT id FROM videos WHERE file_path = ?", (file_path,))
        if self.cursor.fetchone():
            return "skipped"  # 已存在，跳过
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return "error"  # 文件不存在
        
        # 使用默认描述，不调用AI生成
        description = f"这是一个关于{filename}的视频，内容精彩有趣。"
        
        # 插入数据库
        self.cursor.execute('''
            INSERT INTO videos (filename, display_name, file_path, description)
            VALUES (?, ?, ?, ?)
        ''', (filename, display_name, file_path, description))
        
        self.conn.commit()
        return "added"
    

    
    def add_folder(self):
        """批量添加文件夹中的视频"""
        # 禁用按钮
        self.disable_buttons()
        
        folder_path = filedialog.askdirectory(title="选择包含视频的文件夹")
        
        if folder_path:
            # 在后台线程中处理文件夹扫描和添加
            self.process_folder_in_background(folder_path)
    
    def process_folder_in_background(self, folder_path):
        """在后台线程中处理文件夹"""
        def process_thread():
            try:
                # 更新状态
                self.root.after(0, lambda: self.status_var.set("正在扫描文件夹..."))
                
                # 获取支持的视频格式
                supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
                
                # 查找文件夹中的所有视频文件
                video_files = []
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(fmt) for fmt in supported_formats):
                            video_files.append(os.path.join(root, file))
                
                if not video_files:
                    self.root.after(0, lambda: messagebox.showwarning("警告", "所选文件夹中没有找到支持的视频文件"))
                    self.root.after(0, lambda: self.status_var.set("就绪"))
                    self.root.after(0, lambda: self.enable_buttons())
                    return
                
                # 在主线程中显示确认对话框
                def show_confirm():
                    result = messagebox.askyesno("确认", f"找到 {len(video_files)} 个视频文件，是否全部添加？")
                    if result:
                        # 继续处理
                        self.add_videos_from_list(video_files)
                    else:
                        self.status_var.set("就绪")
                
                self.root.after(0, show_confirm)
                
            except Exception as e:
                print(f"处理文件夹时出错: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"处理文件夹时出错：{e}"))
                self.root.after(0, lambda: self.status_var.set("就绪"))
        
        # 启动后台线程
        threading.Thread(target=process_thread, daemon=True).start()
    
    def add_videos_from_list(self, video_files):
        """从文件列表添加视频"""
        def add_thread():
            # 为后台线程创建独立的数据库连接
            import sqlite3
            thread_conn = sqlite3.connect(self.db_path)
            thread_cursor = thread_conn.cursor()
            
            try:
                added_count = 0
                skipped_count = 0
                error_count = 0
                
                # 批量检查已存在的文件
                self.root.after(0, lambda: self.status_var.set("正在检查重复文件..."))
                file_paths = []
                valid_files = []
                
                for file_path in video_files:
                    if os.path.exists(file_path):
                        file_paths.append(file_path)
                        valid_files.append(file_path)
                    else:
                        error_count += 1
                
                if file_paths:
                    # 批量查询已存在的文件
                    placeholders = ','.join(['?' for _ in file_paths])
                    thread_cursor.execute(f"SELECT file_path FROM videos WHERE file_path IN ({placeholders})", file_paths)
                    existing_paths = {row[0] for row in thread_cursor.fetchall()}
                    
                    # 准备批量插入的数据
                    batch_data = []
                    for file_path in valid_files:
                        if file_path not in existing_paths:
                            filename = os.path.basename(file_path)
                            display_name = os.path.splitext(filename)[0]
                            description = f"这是一个关于{filename}的视频，内容精彩有趣。"
                            batch_data.append((filename, display_name, file_path, description))
                        else:
                            skipped_count += 1
                    
                    # 批量插入新文件
                    if batch_data:
                        self.root.after(0, lambda: self.status_var.set(f"正在批量添加 {len(batch_data)} 个文件..."))
                        thread_cursor.executemany('''
                            INSERT INTO videos (filename, display_name, file_path, description)
                            VALUES (?, ?, ?, ?)
                        ''', batch_data)
                        thread_conn.commit()
                        added_count = len(batch_data)
                
                # 更新界面
                self.root.after(0, lambda: self.load_video_list())
                
                # 显示结果
                message = f"文件夹批量添加完成: 成功添加 {added_count} 个视频"
                if skipped_count > 0:
                    message += f"，跳过 {skipped_count} 个重复文件"
                if error_count > 0:
                    message += f"，失败 {error_count} 个文件"
                
                self.root.after(0, lambda: self.status_var.set(message))
                
                # 显示成功消息
                if added_count > 0:
                    self.root.after(0, lambda: self.show_success_message(f"已添加 {added_count} 个视频"))
                
                # 启用按钮
                self.root.after(0, lambda: self.enable_buttons())
                
            except Exception as e:
                print(f"批量添加视频时出错: {e}")
                self.root.after(0, lambda: messagebox.showerror("错误", f"批量添加视频时出错：{e}"))
                self.root.after(0, lambda: self.status_var.set("就绪"))
                self.root.after(0, lambda: self.enable_buttons())
            finally:
                # 关闭线程数据库连接
                thread_conn.close()
        
        # 启动后台线程
        threading.Thread(target=add_thread, daemon=True).start()
    
    def add_single_video_thread_safe(self, file_path, cursor, conn):
        """线程安全的添加单个视频到数据库"""
        filename = os.path.basename(file_path)
        display_name = os.path.splitext(filename)[0]  # 默认使用文件名（不含扩展名）
        
        # 检查是否已存在
        cursor.execute("SELECT id FROM videos WHERE file_path = ?", (file_path,))
        if cursor.fetchone():
            return "skipped"  # 已存在，跳过
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return "error"  # 文件不存在
        
        # 使用默认描述，不调用AI生成
        description = f"这是一个关于{filename}的视频，内容精彩有趣。"
        
        # 插入数据库
        cursor.execute('''
            INSERT INTO videos (filename, display_name, file_path, description)
            VALUES (?, ?, ?, ?)
        ''', (filename, display_name, file_path, description))
        
        conn.commit()
        return "added"
    

    

    
    def generate_ai_description(self, filename):
        """生成AI描述"""
        if hasattr(self, 'ai_enabled') and self.ai_enabled:
            try:
                return self.ollama_client.generate_video_description(filename)
            except Exception as e:
                print(f"AI生成描述失败: {e}")
                return f"这是一个关于{filename}的视频，内容精彩有趣。"
        else:
            # 模拟描述
            return f"这是一个关于{filename}的视频，内容精彩有趣。"
    
    def load_video_list(self):
        """加载视频列表"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 从数据库加载数据
        self.cursor.execute('''
            SELECT id, display_name, filename, description, status, created_at
            FROM videos ORDER BY created_at DESC
        ''')
        
        for row in self.cursor.fetchall():
            item_id = row[0]
            display_name = row[1]
            filename = row[2]
            description = row[3]
            status = row[4]
            created_at = row[5]
            
            # 根据状态设置标签
            tags = []
            if status == "已发布":
                tags.append("published")
            elif status == "发布失败":
                tags.append("failed")
            
            # 添加复选框 - 按照新的列顺序：选择, ID, 显示名称, 描述, 文件名, 状态, 创建时间
            self.tree.insert("", "end", values=("□", item_id, display_name, description, 
                                               filename, status, created_at), tags=tags)
    
    def filter_videos(self, event=None):
        """筛选视频"""
        status_filter = self.status_filter.get()
        
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 根据筛选条件查询
        if status_filter == "全部":
            self.cursor.execute('''
                SELECT id, display_name, filename, description, status, created_at
                FROM videos ORDER BY created_at DESC
            ''')
        else:
            self.cursor.execute('''
                SELECT id, display_name, filename, description, status, created_at
                FROM videos WHERE status = ? ORDER BY created_at DESC
            ''', (status_filter,))
        
        for row in self.cursor.fetchall():
            item_id = row[0]
            display_name = row[1]
            filename = row[2]
            description = row[3]
            status = row[4]
            created_at = row[5]
            
            # 根据状态设置标签
            tags = []
            if status == "已发布":
                tags.append("published")
            elif status == "发布失败":
                tags.append("failed")
            
            # 按照新的列顺序：选择, ID, 显示名称, 描述, 文件名, 状态, 创建时间
            self.tree.insert("", "end", values=("□", item_id, display_name, description, 
                                               filename, status, created_at), tags=tags)
    
    def edit_video(self, event):
        """编辑视频信息"""
        item = self.tree.selection()
        if not item:
            return
        
        # 获取选中项的数据
        values = self.tree.item(item[0])['values']
        video_id = values[1]
        
        # 创建编辑窗口
        self.create_edit_window(video_id)
    
    def create_edit_window(self, video_id):
        """创建编辑窗口"""
        edit_window = tk.Toplevel(self.root)
        edit_window.title("编辑视频信息")
        edit_window.geometry("500x400")
        edit_window.transient(self.root)
        edit_window.grab_set()
        
        # 获取视频信息
        self.cursor.execute('''
            SELECT filename, display_name, description, status FROM videos WHERE id = ?
        ''', (video_id,))
        video_data = self.cursor.fetchone()
        
        if not video_data:
            return
        
        filename, display_name, description, status = video_data
        
        # 创建表单
        form_frame = ttk.Frame(edit_window, padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 显示名称
        ttk.Label(form_frame, text="显示名称:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=display_name)
        name_entry = ttk.Entry(form_frame, textvariable=name_var, width=50)
        name_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        # 描述
        ttk.Label(form_frame, text="描述:").grid(row=1, column=0, sticky="nw", pady=5)
        desc_var = tk.StringVar(value=description)
        desc_text = tk.Text(form_frame, height=10, width=50)
        desc_text.insert("1.0", desc_var.get())
        desc_text.grid(row=1, column=1, sticky="ew", pady=5)
        
        # 状态
        ttk.Label(form_frame, text="状态:").grid(row=2, column=0, sticky="w", pady=5)
        status_var = tk.StringVar(value=status)
        status_combo = ttk.Combobox(form_frame, textvariable=status_var, 
                                   values=["未发布", "已发布", "发布失败"], state="readonly")
        status_combo.grid(row=2, column=1, sticky="ew", pady=5)
        
        # AI生成按钮
        ai_frame = ttk.Frame(form_frame)
        ai_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(ai_frame, text="AI生成名称", 
                  command=lambda: self.generate_ai_name(name_var, filename)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(ai_frame, text="AI生成描述", 
                  command=lambda: self.generate_ai_desc(desc_text, filename)).pack(side=tk.LEFT)
        
        # 按钮框架
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        def save_changes():
            new_name = name_var.get()
            new_desc = desc_text.get("1.0", tk.END).strip()
            new_status = status_var.get()
            
            self.cursor.execute('''
                UPDATE videos 
                SET display_name = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_name, new_desc, new_status, video_id))
            self.conn.commit()
            
            self.load_video_list()
            edit_window.destroy()
            messagebox.showinfo("成功", "视频信息已更新")
        
        ttk.Button(button_frame, text="保存", command=save_changes).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=edit_window.destroy).pack(side=tk.LEFT)
        
        # 配置网格权重
        form_frame.columnconfigure(1, weight=1)
    
    def generate_ai_name(self, name_var, filename):
        """AI生成名称"""
        if hasattr(self, 'ai_enabled') and self.ai_enabled:
            try:
                # 使用原始文件名生成AI名称
                ai_name = self.ollama_client.generate_video_title(filename)
                name_var.set(ai_name)
            except Exception as e:
                print(f"AI生成名称失败: {e}")
                ai_name = f"AI生成的视频名称_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                name_var.set(ai_name)
        else:
            # 模拟名称
            ai_name = f"AI生成的视频名称_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            name_var.set(ai_name)
    
    def generate_ai_desc(self, desc_text, filename):
        """AI生成描述"""
        if hasattr(self, 'ai_enabled') and self.ai_enabled:
            try:
                # 使用原始文件名生成AI描述
                ai_desc = self.ollama_client.generate_video_description(filename)
                desc_text.delete("1.0", tk.END)
                desc_text.insert("1.0", ai_desc)
            except Exception as e:
                print(f"AI生成描述失败: {e}")
                ai_desc = f"这是一个由AI生成的视频描述，内容丰富有趣，值得观看。生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                desc_text.delete("1.0", tk.END)
                desc_text.insert("1.0", ai_desc)
        else:
            # 模拟描述
            ai_desc = f"这是一个由AI生成的视频描述，内容丰富有趣，值得观看。生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            desc_text.delete("1.0", tk.END)
            desc_text.insert("1.0", ai_desc)
    
    def get_selected_videos(self):
        """获取选中的视频ID列表"""
        selected_items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if values[0] == "☑":  # 检查是否选中
                selected_items.append(values[1])  # 添加视频ID
        return selected_items
    
    def batch_publish(self):
        """批量发布到抖音"""
        selected_items = self.get_selected_videos()
        
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要发布的视频")
            return
        
        # 检查发布器是否可用
        if not DOUYIN_PUBLISHER_AVAILABLE:
            messagebox.showwarning("警告", "抖音发布器不可用，将使用模拟发布功能")
            self.simulate_batch_publish(selected_items)
            return
        
        # 确认对话框
        result = messagebox.askyesno("确认", f"确定要发布 {len(selected_items)} 个视频到抖音吗？")
        if not result:
            return
        
        # 禁用按钮
        self.disable_buttons()
        
        # 开始真实发布
        def publish_thread():
            # 为后台线程创建独立的数据库连接
            thread_conn = sqlite3.connect(self.db_path)
            thread_cursor = thread_conn.cursor()
            
            try:
                # 创建发布器
                publisher = DouyinPublisher()
                
                # 获取选中的视频信息
                video_list = []
                for video_id in selected_items:
                    thread_cursor.execute('''
                        SELECT display_name, file_path, description, filename 
                        FROM videos WHERE id = ?
                    ''', (video_id,))
                    video_data = thread_cursor.fetchone()
                    
                    if video_data:
                        display_name, file_path, description, filename = video_data
                        
                        # 检查文件是否存在
                        if not os.path.exists(file_path):
                            print(f"❌ 视频文件不存在: {file_path}")
                            continue
                        
                        # 创建发布信息
                        publish_info = publisher.create_publish_info({
                            'display_name': display_name,
                            'file_path': file_path,
                            'description': description,
                            'filename': filename
                        })
                        
                        video_list.append(publish_info)
                
                if not video_list:
                    self.root.after(0, lambda: messagebox.showerror("错误", "没有找到有效的视频文件"))
                    self.root.after(0, lambda: self.enable_buttons())
                    return
                
                # 初始化发布器
                async def init_publisher():
                    return await publisher.initialize()
                
                # 在主线程中运行异步初始化
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                init_success = loop.run_until_complete(init_publisher())
                loop.close()
                
                if not init_success:
                    self.root.after(0, lambda: messagebox.showerror("错误", "抖音发布器初始化失败"))
                    self.root.after(0, lambda: self.enable_buttons())
                    return
                
                # 定义进度回调
                def progress_callback(current, total, success_count, failed_count, current_success):
                    self.root.after(0, lambda: self.status_var.set(
                        f"正在发布: {current}/{total} - 成功: {success_count}, 失败: {failed_count}"
                    ))
                    
                    # 更新处理中状态
                    if current <= len(selected_items):
                        video_id = selected_items[current - 1]
                        self.root.after(0, lambda vid=video_id: self.update_processing_status(vid, True))
                        
                        # 立即更新当前视频的发布状态
                        if current_success:
                            self.root.after(0, lambda vid=video_id: self.update_publish_status(vid, "已发布"))
                        else:
                            self.root.after(0, lambda vid=video_id: self.update_publish_status(vid, "发布失败"))
                        
                        # 移除处理中状态
                        self.root.after(0, lambda vid=video_id: self.update_processing_status(vid, False))
                
                # 开始批量发布
                result = publisher.publish_videos_batch(video_list, progress_callback)
                
                # 显示结果
                message = f"发布完成: 成功 {result['success']} 个，失败 {result['failed']} 个"
                self.root.after(0, lambda: self.status_var.set(message))
                self.root.after(0, lambda: self.enable_buttons())
                
                if result['success'] > 0:
                    self.root.after(0, lambda: messagebox.showinfo("发布完成", message))
                
            except Exception as e:
                print(f"批量发布出错: {e}")
                self.root.after(0, lambda: messagebox.showerror("发布失败", f"批量发布时出错：{e}"))
                self.root.after(0, lambda: self.enable_buttons())
            finally:
                # 关闭数据库连接
                thread_conn.close()
        
        threading.Thread(target=publish_thread, daemon=True).start()
    
    def simulate_batch_publish(self, selected_items):
        """模拟批量发布（当发布器不可用时使用）"""
        # 禁用按钮
        self.disable_buttons()
        
        # 模拟发布过程
        def publish_thread():
            self.status_var.set("正在发布...")
            for i, video_id in enumerate(selected_items):
                # 设置处理中状态
                self.root.after(1000 * (i + 1), lambda vid=video_id: self.update_processing_status(vid, True))
                
                # 模拟发布延迟并立即更新状态
                self.root.after(2000 * (i + 1), lambda vid=video_id: self.update_publish_status(vid, "已发布"))
                self.root.after(2000 * (i + 1), lambda vid=video_id: self.update_processing_status(vid, False))
                
                # 更新状态栏
                self.root.after(2000 * (i + 1), lambda idx=i: self.status_var.set(f"模拟发布: {idx+1}/{len(selected_items)}"))
            
            self.root.after(2000 * (len(selected_items) + 1), 
                          lambda: self.status_var.set(f"模拟发布完成，共发布 {len(selected_items)} 个视频"))
            self.root.after(2000 * (len(selected_items) + 1), 
                          lambda: self.enable_buttons())
        
        threading.Thread(target=publish_thread, daemon=True).start()
    
    def update_publish_status(self, video_id, status):
        """更新发布状态"""
        # 在后台线程中使用独立的数据库连接
        def update_in_thread():
            import sqlite3
            thread_conn = sqlite3.connect(self.db_path)
            thread_cursor = thread_conn.cursor()
            
            try:
                thread_cursor.execute('''
                    UPDATE videos SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                ''', (status, video_id))
                thread_conn.commit()
                
                # 在主线程中更新界面
                self.root.after(0, lambda: self.load_video_list())
                
            except Exception as e:
                print(f"更新发布状态时出错: {e}")
            finally:
                thread_conn.close()
        
        # 在后台线程中执行数据库更新
        threading.Thread(target=update_in_thread, daemon=True).start()
    
    def update_processing_status(self, video_id, is_processing):
        """更新处理中状态"""
        # 查找对应的树形视图项目
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if values[1] == video_id:  # ID列
                current_tags = list(self.tree.item(item)['tags'])
                
                if is_processing:
                    # 添加处理中标签
                    if "processing" not in current_tags:
                        current_tags.append("processing")
                else:
                    # 移除处理中标签
                    if "processing" in current_tags:
                        current_tags.remove("processing")
                
                # 更新项目标签
                self.tree.item(item, tags=current_tags)
                break
    
    def update_video_display(self, video_id, new_name, new_desc):
        """更新视频显示信息"""
        # 查找对应的树形视图项目
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            if values[1] == video_id:  # ID列
                # 更新显示名称和描述
                values[2] = new_name  # 显示名称列
                values[3] = new_desc  # 描述列
                
                # 移除处理中标签
                current_tags = list(self.tree.item(item)['tags'])
                if "processing" in current_tags:
                    current_tags.remove("processing")
                
                # 更新项目
                self.tree.item(item, values=values, tags=current_tags)
                break
    
    def batch_ai_description(self):
        """批量AI智能描述（生成名称和描述）"""
        selected_items = self.get_selected_videos()
        
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要生成AI描述的视频")
            return
        
        # 确认对话框
        result = messagebox.askyesno("确认", f"确定要为 {len(selected_items)} 个视频生成AI名称和描述吗？")
        if not result:
            return
        
        # 检查AI功能是否可用
        if not hasattr(self, 'ai_enabled') or not self.ai_enabled:
            messagebox.showwarning("警告", "AI功能不可用，将使用模拟数据")
        
        # 禁用按钮
        self.disable_buttons()
        
        # 批量AI生成
        success_count = 0
        failed_count = 0
        
        def generate_thread():
            nonlocal success_count, failed_count
            
            # 在后台线程中创建数据库连接
            import sqlite3
            thread_conn = sqlite3.connect(self.db_path)
            thread_cursor = thread_conn.cursor()
            
            try:
                for i, video_id in enumerate(selected_items):
                    try:
                        # 更新处理中状态 - 蓝色背景
                        self.root.after(0, lambda vid=video_id: self.update_processing_status(vid, True))
                        
                        # 获取视频信息
                        thread_cursor.execute('SELECT filename FROM videos WHERE id = ?', (video_id,))
                        filename = thread_cursor.fetchone()[0]
                        
                        # 生成AI名称
                        if hasattr(self, 'ai_enabled') and self.ai_enabled:
                            try:
                                ai_name = self.ollama_client.generate_video_title(filename)
                            except Exception as e:
                                print(f"AI生成名称失败: {e}")
                                ai_name = f"AI生成标题_{filename}"
                        else:
                            ai_name = f"AI生成标题_{filename}"
                        
                        # 生成AI描述
                        if hasattr(self, 'ai_enabled') and self.ai_enabled:
                            try:
                                ai_desc = self.ollama_client.generate_video_description(filename)
                            except Exception as e:
                                print(f"AI生成描述失败: {e}")
                                ai_desc = f"这是一个关于{filename}的精彩视频，内容有趣，值得观看。"
                        else:
                            ai_desc = f"这是一个关于{filename}的精彩视频，内容有趣，值得观看。"
                        
                        # 更新数据库
                        thread_cursor.execute('''
                            UPDATE videos 
                            SET display_name = ?, description = ?, updated_at = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        ''', (ai_name, ai_desc, video_id))
                        
                        # 立即提交单个更改
                        thread_conn.commit()
                        
                        success_count += 1
                        
                        # 更新UI界面 - 移除处理中状态，更新显示
                        self.root.after(0, lambda vid=video_id, name=ai_name, desc=ai_desc: 
                                      self.update_video_display(vid, name, desc))
                        
                        # 更新状态栏
                        self.root.after(0, lambda: self.status_var.set(f"正在处理: {i+1}/{len(selected_items)} - 成功: {success_count}"))
                        
                    except Exception as e:
                        print(f"处理视频 {video_id} 时出错: {e}")
                        failed_count += 1
                        
                        # 移除处理中状态
                        self.root.after(0, lambda vid=video_id: self.update_processing_status(vid, False))
                
                # 更新界面
                self.root.after(0, lambda: self.status_var.set(f"完成！成功: {success_count}, 失败: {failed_count}"))
                self.root.after(0, lambda: messagebox.showinfo("完成", f"批量AI生成完成！\n成功: {success_count} 个\n失败: {failed_count} 个"))
                self.root.after(0, lambda: self.enable_buttons())
                
            finally:
                # 关闭线程数据库连接
                thread_conn.close()
        
        # 在后台线程中执行
        threading.Thread(target=generate_thread, daemon=True).start()
    
    def delete_selected(self):
        """删除选中的视频（仅删除数据库数据）"""
        selected_items = self.get_selected_videos()
        
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要删除的视频")
            return
        
        # 禁用按钮
        self.disable_buttons()
        
        # 创建自定义确认对话框
        self.create_delete_confirm_dialog(selected_items)
    
    def create_delete_confirm_dialog(self, selected_items):
        """创建删除确认对话框"""
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("确认删除视频")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="确认删除视频", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 15))
        
        # 说明文字
        info_text = f"即将删除 {len(selected_items)} 个视频的数据库记录\n（实际文件不会被删除）"
        info_label = ttk.Label(main_frame, text=info_text, foreground="red", font=("Arial", 10))
        info_label.pack(pady=(0, 20))
        
        # 创建滚动框架容器
        scroll_container = ttk.Frame(main_frame)
        scroll_container.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建滚动框架
        canvas = tk.Canvas(scroll_container, height=250)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 获取要删除的视频信息
        video_info = []
        for video_id in selected_items:
            self.cursor.execute('SELECT filename, display_name FROM videos WHERE id = ?', (video_id,))
            result = self.cursor.fetchone()
            if result:
                filename, display_name = result
                video_info.append((display_name, filename))
        
        # 显示视频列表
        for i, (display_name, filename) in enumerate(video_info):
            video_frame = ttk.Frame(scrollable_frame)
            video_frame.pack(fill=tk.X, pady=3, padx=5)
            
            # 序号
            ttk.Label(video_frame, text=f"{i+1:2d}.", width=4, anchor="e").pack(side=tk.LEFT)
            
            # 显示名称
            name_label = ttk.Label(video_frame, text=display_name, font=("Arial", 10, "bold"))
            name_label.pack(side=tk.LEFT, padx=(8, 12))
            
            # 文件名
            filename_label = ttk.Label(video_frame, text=f"({filename})", foreground="gray", font=("Arial", 9))
            filename_label.pack(side=tk.LEFT)
        
        # 配置滚动区域
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", 
                                 command=lambda: self.cancel_delete(dialog), width=12)
        cancel_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 删除按钮
        delete_button = ttk.Button(button_frame, text="确认删除", 
                                 command=lambda: self.execute_delete(selected_items, dialog),
                                 width=12)
        delete_button.pack(side=tk.RIGHT)
        
        # 设置焦点
        delete_button.focus_set()
        
        # 绑定回车键和ESC键
        dialog.bind("<Return>", lambda e: self.execute_delete(selected_items, dialog))
        dialog.bind("<Escape>", lambda e: self.cancel_delete(dialog))
    
    def cancel_delete(self, dialog):
        """取消删除操作"""
        dialog.destroy()
        self.enable_buttons()
    
    def execute_delete(self, selected_items, dialog):
        """执行删除操作"""
        try:
            deleted_count = 0
            for video_id in selected_items:
                self.cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
                deleted_count += 1
            
            self.conn.commit()
            
            # 关闭对话框
            dialog.destroy()
            
            # 更新界面
            self.load_video_list()
            self.status_var.set(f"删除完成，共删除 {deleted_count} 个视频")
            
            # 显示简洁的成功消息
            self.show_success_message(f"已删除 {deleted_count} 个视频记录")
            
            # 启用按钮
            self.enable_buttons()
            
        except Exception as e:
            print(f"删除视频时出错: {e}")
            dialog.destroy()
            messagebox.showerror("删除失败", f"删除视频时出错：{e}")
            self.enable_buttons()
    
    def show_success_message(self, message):
        """显示简洁的成功消息"""
        # 创建临时消息窗口
        msg_window = tk.Toplevel(self.root)
        msg_window.title("操作成功")
        msg_window.geometry("300x100")
        msg_window.transient(self.root)
        msg_window.grab_set()
        msg_window.resizable(False, False)
        
        # 居中显示
        msg_window.update_idletasks()
        x = (msg_window.winfo_screenwidth() // 2) - (300 // 2)
        y = (msg_window.winfo_screenheight() // 2) - (100 // 2)
        msg_window.geometry(f"300x100+{x}+{y}")
        
        # 消息内容
        ttk.Label(msg_window, text="✅", font=("Arial", 20)).pack(pady=(10, 5))
        ttk.Label(msg_window, text=message, font=("Arial", 10)).pack()
        
        # 自动关闭
        msg_window.after(2000, msg_window.destroy)
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    app = VideoManager()
    app.run()
