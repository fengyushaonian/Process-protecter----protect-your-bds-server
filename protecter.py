import os
import sys
import psutil
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class ProcessMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("草泥马微软，让我给你擦屁股，服务端一点自保能力都没有 牢风开发")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 设置中文字体支持
        self.font_config()
        
        # 监控相关变量
        self.process_name = ""
        self.process_path = ""
        self.process_id = None
        self.is_monitoring = False
        self.restart_count = 0
        self.monitor_thread = None
        
        # 创建UI
        self.create_widgets()
    
    def font_config(self):
        """配置字体以支持中文显示"""
        default_font = ('SimHei', 10)
        self.root.option_add("*Font", default_font)
    
    def create_widgets(self):
        """创建GUI组件"""
        # 顶部配置区域
        config_frame = ttk.LabelFrame(self.root, text="进程配置")
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # 进程名称输入
        ttk.Label(config_frame, text="进程名称:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.process_name_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.process_name_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # 进程路径选择
        ttk.Label(config_frame, text="进程路径:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.process_path_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.process_path_var, width=30).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="浏览...", command=self.browse_process).grid(row=1, column=2, padx=5, pady=5)
        
        # 控制按钮
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="开始监控", command=self.start_monitoring)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="停止监控", command=self.stop_monitoring, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        self.reset_btn = ttk.Button(control_frame, text="重置计数", command=self.reset_counter)
        self.reset_btn.pack(side="left", padx=5)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(self.root, text="监控状态")
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 状态标签
        ttk.Label(status_frame, text="当前状态:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.status_var = tk.StringVar(value="未监控")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 进程ID标签
        ttk.Label(status_frame, text="进程ID:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.pid_var = tk.StringVar(value="N/A")
        ttk.Label(status_frame, textvariable=self.pid_var).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 重启计数标签
        ttk.Label(status_frame, text="重启次数:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.restart_var = tk.StringVar(value="0")
        ttk.Label(status_frame, textvariable=self.restart_var).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # 日志区域
        ttk.Label(status_frame, text="日志信息:").grid(row=3, column=0, padx=5, pady=5, sticky="nw")
        self.log_text = tk.Text(status_frame, height=10, width=60, state="disabled")
        self.log_text.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(status_frame, command=self.log_text.yview)
        scrollbar.grid(row=3, column=2, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 设置网格权重，使日志区域可扩展
        status_frame.grid_rowconfigure(3, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
    
    def browse_process(self):
        """浏览并选择进程可执行文件"""
        file_path = filedialog.askopenfilename(
            title="选择进程可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if file_path:
            self.process_path_var.set(file_path)
            # 自动提取进程名称
            process_name = os.path.basename(file_path)
            self.process_name_var.set(process_name)
    
    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_text.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")  # 滚动到最后一行
        self.log_text.config(state="disabled")
    
    def is_process_running(self):
        """检查进程是否正在运行"""
        if not self.process_name:
            return False
            
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'].lower() == self.process_name.lower():
                    self.process_id = proc.info['pid']
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False
    
    def start_process(self):
        """启动进程"""
        try:
            if not self.process_path or not os.path.exists(self.process_path):
                self.log_message(f"错误: 进程路径不存在 - {self.process_path}")
                return False
                
            # 启动进程
            self.process_id = os.startfile(self.process_path)
            # 对于某些系统，os.startfile可能不返回PID，这里做兼容处理
            if self.process_id is None:
                time.sleep(1)  # 等待进程启动
                self.is_process_running()  # 重新获取PID
                
            self.log_message(f"进程已启动 - {self.process_name} (PID: {self.process_id})")
            return True
        except Exception as e:
            self.log_message(f"启动进程失败: {str(e)}")
            return False
    
    def monitor_process(self):
        """监控进程的线程函数"""
        while self.is_monitoring:
            if self.is_process_running():
                # 进程正在运行
                self.status_var.set("运行中")
                self.status_label.config(foreground="green")
                self.pid_var.set(str(self.process_id))
            else:
                # 进程未运行，尝试重启
                self.status_var.set("草泥马的傻逼mojang，把我服务端崩了，尝试重启...")
                self.status_label.config(foreground="red")
                self.pid_var.set("N/A")
                self.log_message(f"进程 {self.process_name} 已停止，尝试重启...")
                
                if self.start_process():
                    self.restart_count += 1
                    self.restart_var.set(str(self.restart_count))
                    self.status_var.set("运行中")
                    self.status_label.config(foreground="green")
            
            # 每2秒检查一次
            time.sleep(2)
    
    def start_monitoring(self):
        """开始监控进程"""
        self.process_name = self.process_name_var.get().strip()
        self.process_path = self.process_path_var.get().strip()
        
        if not self.process_name or not self.process_path:
            messagebox.showerror("错误", "请输入进程名称和路径")
            return
        
        if not os.path.exists(self.process_path):
            messagebox.showerror("错误", "进程路径不存在")
            return
        
        self.is_monitoring = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # 检查进程是否已在运行
        if not self.is_process_running():
            self.log_message(f"进程 {self.process_name} 未运行，尝试启动...")
            self.start_process()
        else:
            self.log_message(f"开始监控进程 {self.process_name} (PID: {self.process_id})")
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self.monitor_process, daemon=True)
        self.monitor_thread.start()
        
        self.status_var.set("监控中")
        self.status_label.config(foreground="blue")
        self.log_message("开始监控...")
    
    def stop_monitoring(self):
        """停止监控进程"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        self.status_var.set("已停止监控")
        self.status_label.config(foreground="red")
        self.log_message("已停止监控")
    
    def reset_counter(self):
        """重置重启计数器"""
        self.restart_count = 0
        self.restart_var.set("0")
        self.log_message("重启计数器已重置")



if __name__ == "__main__":
    # 检查并安装所需库
    try:
        import psutil
    except ImportError:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    root = tk.Tk()
    app = ProcessMonitorApp(root)
    root.mainloop()
