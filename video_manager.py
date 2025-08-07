import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import threading
from datetime import datetime
import json

class VideoManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("视频管理系统")
        self.root.geometry("1200x800")
        
        # 数据库初始化
        self.init_database()
        
        # 创建界面
        self.create_widgets()
        
        # 加载视频列表
        self.load_video_list()
    
    def init_database(self):
        """初始化数据库"""
        self.conn = sqlite3.connect('videos.db')
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
    
    def create_widgets(self):
        """创建GUI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制区域
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 添加视频按钮
        ttk.Button(control_frame, text="添加视频", command=self.add_videos).pack(side=tk.LEFT, padx=(0, 10))
        
        # 批量操作按钮
        ttk.Button(control_frame, text="批量发布", command=self.batch_publish).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="批量重命名", command=self.batch_rename).pack(side=tk.LEFT, padx=(0, 10))
        
        # 筛选框架
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(side=tk.RIGHT)
        
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
        columns = ("选择", "ID", "显示名称", "文件名", "描述", "状态", "创建时间")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题和宽度
        self.tree.heading("选择", text="选择")
        self.tree.heading("ID", text="ID")
        self.tree.heading("显示名称", text="显示名称")
        self.tree.heading("文件名", text="文件名")
        self.tree.heading("描述", text="描述")
        self.tree.heading("状态", text="状态")
        self.tree.heading("创建时间", text="创建时间")
        
        self.tree.column("选择", width=50, anchor="center")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("显示名称", width=200)
        self.tree.column("文件名", width=200)
        self.tree.column("描述", width=300)
        self.tree.column("状态", width=100, anchor="center")
        self.tree.column("创建时间", width=150, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.edit_video)
        
        # 底部状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def add_videos(self):
        """添加视频文件"""
        files = filedialog.askopenfilenames(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                ("所有文件", "*.*")
            ]
        )
        
        if files:
            for file_path in files:
                self.add_single_video(file_path)
            
            self.load_video_list()
            self.status_var.set(f"已添加 {len(files)} 个视频文件")
    
    def add_single_video(self, file_path):
        """添加单个视频到数据库"""
        filename = os.path.basename(file_path)
        display_name = os.path.splitext(filename)[0]  # 默认使用文件名（不含扩展名）
        
        # 检查是否已存在
        self.cursor.execute("SELECT id FROM videos WHERE file_path = ?", (file_path,))
        if self.cursor.fetchone():
            return  # 已存在，跳过
        
        # 生成AI描述（模拟）
        description = self.generate_ai_description(filename)
        
        # 插入数据库
        self.cursor.execute('''
            INSERT INTO videos (filename, display_name, file_path, description)
            VALUES (?, ?, ?, ?)
        ''', (filename, display_name, file_path, description))
        
        self.conn.commit()
    
    def generate_ai_description(self, filename):
        """生成AI描述（模拟）"""
        # 这里可以集成Ollama API
        # 暂时返回模拟描述
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
            
            # 添加复选框
            self.tree.insert("", "end", values=("□", item_id, display_name, filename, 
                                               description, status, created_at))
    
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
            
            self.tree.insert("", "end", values=("□", item_id, display_name, filename, 
                                               description, status, created_at))
    
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
            SELECT display_name, description, status FROM videos WHERE id = ?
        ''', (video_id,))
        video_data = self.cursor.fetchone()
        
        if not video_data:
            return
        
        display_name, description, status = video_data
        
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
                  command=lambda: self.generate_ai_name(name_var)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(ai_frame, text="AI生成描述", 
                  command=lambda: self.generate_ai_desc(desc_text)).pack(side=tk.LEFT)
        
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
    
    def generate_ai_name(self, name_var):
        """AI生成名称"""
        # 这里可以集成Ollama API
        # 暂时返回模拟名称
        ai_name = f"AI生成的视频名称_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        name_var.set(ai_name)
    
    def generate_ai_desc(self, desc_text):
        """AI生成描述"""
        # 这里可以集成Ollama API
        # 暂时返回模拟描述
        ai_desc = f"这是一个由AI生成的视频描述，内容丰富有趣，值得观看。生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        desc_text.delete("1.0", tk.END)
        desc_text.insert("1.0", ai_desc)
    
    def batch_publish(self):
        """批量发布（模拟）"""
        selected_items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if values[0] == "☑":  # 检查是否选中
                selected_items.append(values[1])  # 添加视频ID
        
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要发布的视频")
            return
        
        # 模拟发布过程
        def publish_thread():
            self.status_var.set("正在发布...")
            for i, video_id in enumerate(selected_items):
                # 模拟发布延迟
                self.root.after(1000 * (i + 1), lambda vid=video_id: self.update_publish_status(vid, "已发布"))
            
            self.root.after(1000 * (len(selected_items) + 1), 
                          lambda: self.status_var.set(f"发布完成，共发布 {len(selected_items)} 个视频"))
        
        threading.Thread(target=publish_thread, daemon=True).start()
    
    def update_publish_status(self, video_id, status):
        """更新发布状态"""
        self.cursor.execute('''
            UPDATE videos SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (status, video_id))
        self.conn.commit()
        self.load_video_list()
    
    def batch_rename(self):
        """批量重命名（AI生成）"""
        selected_items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            if values[0] == "☑":  # 检查是否选中
                selected_items.append(values[1])  # 添加视频ID
        
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要重命名的视频")
            return
        
        # 批量AI重命名
        for video_id in selected_items:
            self.cursor.execute('SELECT filename FROM videos WHERE id = ?', (video_id,))
            filename = self.cursor.fetchone()[0]
            
            # 生成AI名称
            ai_name = f"AI_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.cursor.execute('''
                UPDATE videos SET display_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (ai_name, video_id))
        
        self.conn.commit()
        self.load_video_list()
        messagebox.showinfo("成功", f"已为 {len(selected_items)} 个视频生成AI名称")
    
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
