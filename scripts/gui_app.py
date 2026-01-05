"""
GUI前端 - 完整功能版本
包含所有配置项，正确处理.env文件读写
只使用tkinter标准库，无需额外依赖
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        load_dotenv(env_file, override=True)
except ImportError:
    pass


class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("风控运营数据分析工具")
        self.root.geometry("800x750")
        
        # 变量
        self.file_path = tk.StringVar()
        
        # LLM配置变量
        self.llm_provider = tk.StringVar(value="aliyun")  # aliyun, openai, dify
        self.aliyun_api_key = tk.StringVar()
        self.aliyun_base_url = tk.StringVar()
        self.openai_api_key = tk.StringVar()
        self.dify_api_key = tk.StringVar()
        self.dify_base_url = tk.StringVar()
        
        # 飞书配置变量
        self.feishu_webhook = tk.StringVar()
        self.feishu_secret = tk.StringVar()
        
        # OSS配置变量
        self.oss_bucket = tk.StringVar()
        self.oss_endpoint = tk.StringVar()
        self.oss_access_key_id = tk.StringVar()
        self.oss_access_key_secret = tk.StringVar()
        
        # 功能选项
        self.enable_llm = tk.BooleanVar(value=True)
        self.enable_oss = tk.BooleanVar(value=True)
        self.enable_push = tk.BooleanVar(value=True)
        
        self.is_running = False
        
        # 从.env加载默认值
        self.load_from_env()
        
        # 检查 .env 文件是否存在，如果不存在则提示
        self.check_env_file()
        
        # 创建界面
        self.create_widgets()
        
    def load_from_env(self):
        """从.env文件加载所有配置"""
        env_file = PROJECT_ROOT / '.env'
        if not env_file.exists():
            return
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # LLM配置
                        if key == 'ALIYUN_BAILIAN_API_KEY':
                            self.aliyun_api_key.set(value)
                        elif key == 'ALIYUN_BAILIAN_BASE_URL':
                            self.aliyun_base_url.set(value)
                        elif key == 'OPENAI_API_KEY':
                            self.openai_api_key.set(value)
                        elif key == 'DIFY_API_KEY':
                            self.dify_api_key.set(value)
                        elif key == 'DIFY_BASE_URL':
                            self.dify_base_url.set(value)
                        
                        # 飞书配置
                        elif key == 'FEISHU_WEBHOOK_URL':
                            self.feishu_webhook.set(value)
                        elif key == 'FEISHU_WEBHOOK_SECRET':
                            self.feishu_secret.set(value)
                        
                        # OSS配置
                        elif key == 'OSS_BUCKET_NAME':
                            self.oss_bucket.set(value)
                        elif key == 'OSS_ENDPOINT':
                            self.oss_endpoint.set(value)
                        elif key == 'OSS_ACCESS_KEY_ID':
                            self.oss_access_key_id.set(value)
                        elif key == 'OSS_ACCESS_KEY_SECRET':
                            self.oss_access_key_secret.set(value)
            
            # 根据配置的API Key确定当前使用的模型
            if self.aliyun_api_key.get():
                self.llm_provider.set("aliyun")
            elif self.openai_api_key.get():
                self.llm_provider.set("openai")
            elif self.dify_api_key.get():
                self.llm_provider.set("dify")
        except Exception as e:
            print(f"加载.env文件失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 文件选择区域
        file_frame = ttk.LabelFrame(self.root, text="数据文件", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(file_frame, text="选择Excel文件", command=self.select_file).pack(side=tk.LEFT, padx=5)
        ttk.Label(file_frame, textvariable=self.file_path, foreground="gray").pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # 配置选项卡
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # LLM配置选项卡
        llm_frame = ttk.Frame(notebook, padding=10)
        notebook.add(llm_frame, text="LLM配置")
        self.create_llm_tab(llm_frame)
        
        # 飞书配置选项卡
        feishu_frame = ttk.Frame(notebook, padding=10)
        notebook.add(feishu_frame, text="飞书配置")
        self.create_feishu_tab(feishu_frame)
        
        # OSS配置选项卡
        oss_frame = ttk.Frame(notebook, padding=10)
        notebook.add(oss_frame, text="OSS配置")
        self.create_oss_tab(oss_frame)
        
        # 功能选项和操作按钮
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 功能选项
        option_frame = ttk.LabelFrame(control_frame, text="功能选项", padding=5)
        option_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Checkbutton(option_frame, text="启用LLM分析", variable=self.enable_llm).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(option_frame, text="上传到OSS", variable=self.enable_oss).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(option_frame, text="推送到飞书", variable=self.enable_push).pack(side=tk.LEFT, padx=10)
        
        # 当前使用的LLM模型显示
        current_llm = self.get_current_llm_provider()
        self.llm_status_label = ttk.Label(option_frame, text=f"当前LLM: {current_llm}", foreground="blue")
        self.llm_status_label.pack(side=tk.LEFT, padx=10)
        
        # 操作按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.run_button = ttk.Button(button_frame, text="开始分析", command=self.start_analysis)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="保存配置", command=self.save_to_env).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="运行日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.insert(tk.END, "等待开始分析...\n")
        
        # 重定向输出到日志
        self.redirect_output()
    
    def create_llm_tab(self, parent):
        """创建LLM配置选项卡"""
        # 模型选择
        provider_frame = ttk.LabelFrame(parent, text="选择LLM提供商", padding=5)
        provider_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(provider_frame, text="阿里云百炼（优先）", variable=self.llm_provider, 
                        value="aliyun", command=self.update_llm_status).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(provider_frame, text="OpenAI", variable=self.llm_provider, 
                        value="openai", command=self.update_llm_status).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(provider_frame, text="Dify", variable=self.llm_provider, 
                        value="dify", command=self.update_llm_status).pack(side=tk.LEFT, padx=10)
        
        # 阿里云百炼配置
        self.aliyun_frame = ttk.LabelFrame(parent, text="阿里云百炼配置", padding=5)
        self.aliyun_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.aliyun_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        aliyun_key_entry = ttk.Entry(self.aliyun_frame, textvariable=self.aliyun_api_key, width=60, show="*")
        aliyun_key_entry.grid(row=0, column=1, padx=5)
        aliyun_key_entry.bind('<KeyRelease>', lambda e: self.update_llm_status())
        
        ttk.Label(self.aliyun_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        base_url_entry = ttk.Entry(self.aliyun_frame, textvariable=self.aliyun_base_url, width=60)
        base_url_entry.grid(row=1, column=1, padx=5)
        ttk.Label(self.aliyun_frame, text="（可选，留空使用默认值）", foreground="gray", font=("", 8)).grid(row=1, column=2, padx=5)
        
        # OpenAI配置
        self.openai_frame = ttk.LabelFrame(parent, text="OpenAI配置", padding=5)
        self.openai_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.openai_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        openai_key_entry = ttk.Entry(self.openai_frame, textvariable=self.openai_api_key, width=60, show="*")
        openai_key_entry.grid(row=0, column=1, padx=5)
        openai_key_entry.bind('<KeyRelease>', lambda e: self.update_llm_status())
        
        # Dify配置
        self.dify_frame = ttk.LabelFrame(parent, text="Dify配置", padding=5)
        self.dify_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.dify_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        dify_key_entry = ttk.Entry(self.dify_frame, textvariable=self.dify_api_key, width=60, show="*")
        dify_key_entry.grid(row=0, column=1, padx=5)
        dify_key_entry.bind('<KeyRelease>', lambda e: self.update_llm_status())
        
        ttk.Label(self.dify_frame, text="Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Entry(self.dify_frame, textvariable=self.dify_base_url, width=60).grid(row=1, column=1, padx=5)
    
    def create_feishu_tab(self, parent):
        """创建飞书配置选项卡"""
        ttk.Label(parent, text="Webhook URL（必需）:").grid(row=0, column=0, sticky=tk.W, pady=10, padx=5)
        ttk.Entry(parent, textvariable=self.feishu_webhook, width=70).grid(row=0, column=1, padx=5)
        
        ttk.Label(parent, text="签名密钥（可选）:").grid(row=1, column=0, sticky=tk.W, pady=10, padx=5)
        ttk.Entry(parent, textvariable=self.feishu_secret, width=70, show="*").grid(row=1, column=1, padx=5)
        ttk.Label(parent, text="（如果机器人未启用签名校验，可不填）", foreground="gray", font=("", 8)).grid(row=1, column=2, padx=5)
    
    def create_oss_tab(self, parent):
        """创建OSS配置选项卡"""
        ttk.Label(parent, text="Bucket名称:").grid(row=0, column=0, sticky=tk.W, pady=10, padx=5)
        ttk.Entry(parent, textvariable=self.oss_bucket, width=70).grid(row=0, column=1, padx=5)
        
        ttk.Label(parent, text="Endpoint:").grid(row=1, column=0, sticky=tk.W, pady=10, padx=5)
        ttk.Entry(parent, textvariable=self.oss_endpoint, width=70).grid(row=1, column=1, padx=5)
        
        ttk.Label(parent, text="AccessKey ID:").grid(row=2, column=0, sticky=tk.W, pady=10, padx=5)
        ttk.Entry(parent, textvariable=self.oss_access_key_id, width=70).grid(row=2, column=1, padx=5)
        
        ttk.Label(parent, text="AccessKey Secret:").grid(row=3, column=0, sticky=tk.W, pady=10, padx=5)
        ttk.Entry(parent, textvariable=self.oss_access_key_secret, width=70, show="*").grid(row=3, column=1, padx=5)
    
    def update_llm_status(self):
        """更新LLM状态显示"""
        current_llm = self.get_current_llm_provider()
        self.llm_status_label.config(text=f"当前LLM: {current_llm}")
    
    def get_current_llm_provider(self):
        """获取当前使用的LLM提供商名称"""
        if self.aliyun_api_key.get():
            return "阿里云百炼"
        elif self.openai_api_key.get():
            return "OpenAI"
        elif self.dify_api_key.get():
            return "Dify"
        return "未配置"
    
    def select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel数据文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if file_path:
            self.file_path.set(file_path)
            self.log(f"已选择文件: {file_path}")
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def redirect_output(self):
        """重定向stdout到日志"""
        class LogWriter:
            def __init__(self, text_widget):
                self.text_widget = text_widget
            def write(self, message):
                if message.strip():
                    self.text_widget.insert(tk.END, message)
                    self.text_widget.see(tk.END)
            def flush(self):
                pass
        
        sys.stdout = LogWriter(self.log_text)
        sys.stderr = LogWriter(self.log_text)
    
    def save_to_env(self):
        """保存配置到.env文件（保留注释和其他配置）"""
        env_file = PROJECT_ROOT / '.env'
        
        try:
            # 读取现有文件内容（保留注释和空行）
            lines = []
            existing_keys = set()
            
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        lines.append(line)
                        if '=' in line and not line.strip().startswith('#'):
                            key = line.split('=')[0].strip()
                            existing_keys.add(key)
            
            # 准备要写入的配置
            config_to_write = {}
            
            # LLM配置
            if self.aliyun_api_key.get():
                config_to_write['ALIYUN_BAILIAN_API_KEY'] = self.aliyun_api_key.get()
            if self.aliyun_base_url.get():
                config_to_write['ALIYUN_BAILIAN_BASE_URL'] = self.aliyun_base_url.get()
            if self.openai_api_key.get():
                config_to_write['OPENAI_API_KEY'] = self.openai_api_key.get()
            if self.dify_api_key.get():
                config_to_write['DIFY_API_KEY'] = self.dify_api_key.get()
            if self.dify_base_url.get():
                config_to_write['DIFY_BASE_URL'] = self.dify_base_url.get()
            
            # 飞书配置
            if self.feishu_webhook.get():
                config_to_write['FEISHU_WEBHOOK_URL'] = self.feishu_webhook.get()
            if self.feishu_secret.get():
                config_to_write['FEISHU_WEBHOOK_SECRET'] = self.feishu_secret.get()
            
            # OSS配置
            if self.oss_bucket.get():
                config_to_write['OSS_BUCKET_NAME'] = self.oss_bucket.get()
            if self.oss_endpoint.get():
                config_to_write['OSS_ENDPOINT'] = self.oss_endpoint.get()
            if self.oss_access_key_id.get():
                config_to_write['OSS_ACCESS_KEY_ID'] = self.oss_access_key_id.get()
            if self.oss_access_key_secret.get():
                config_to_write['OSS_ACCESS_KEY_SECRET'] = self.oss_access_key_secret.get()
            
            # 写入文件：先写注释和空行，再写配置项（更新已存在的，追加新的）
            with open(env_file, 'w', encoding='utf-8') as f:
                # 写入注释和空行，以及不在我们要更新的配置项
                for line in lines:
                    if line.strip().startswith('#') or not line.strip():
                        f.write(line)
                    elif '=' in line:
                        key = line.split('=')[0].strip()
                        # 如果这个配置项不在我们要写入的列表中，保留原样
                        if key not in config_to_write:
                            f.write(line)
                
                # 写入配置项（分组写入）
                llm_keys = ['ALIYUN_BAILIAN_API_KEY', 'ALIYUN_BAILIAN_BASE_URL', 'OPENAI_API_KEY', 'DIFY_API_KEY', 'DIFY_BASE_URL']
                feishu_keys = ['FEISHU_WEBHOOK_URL', 'FEISHU_WEBHOOK_SECRET']
                oss_keys = ['OSS_BUCKET_NAME', 'OSS_ENDPOINT', 'OSS_ACCESS_KEY_ID', 'OSS_ACCESS_KEY_SECRET']
                
                if any(k in config_to_write for k in llm_keys):
                    f.write("\n# LLM配置\n")
                    for key in llm_keys:
                        if key in config_to_write:
                            f.write(f"{key}={config_to_write[key]}\n")
                
                if any(k in config_to_write for k in feishu_keys):
                    f.write("\n# 飞书配置\n")
                    for key in feishu_keys:
                        if key in config_to_write:
                            f.write(f"{key}={config_to_write[key]}\n")
                
                if any(k in config_to_write for k in oss_keys):
                    f.write("\n# OSS配置\n")
                    for key in oss_keys:
                        if key in config_to_write:
                            f.write(f"{key}={config_to_write[key]}\n")
            
            self.log("✅ 配置已保存到 .env 文件")
            messagebox.showinfo("成功", "配置已保存到 .env 文件")
        except Exception as e:
            self.log(f"❌ 保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def set_env_vars(self):
        """设置环境变量"""
        # LLM配置
        if self.aliyun_api_key.get():
            os.environ['ALIYUN_BAILIAN_API_KEY'] = self.aliyun_api_key.get()
        if self.aliyun_base_url.get():
            os.environ['ALIYUN_BAILIAN_BASE_URL'] = self.aliyun_base_url.get()
        if self.openai_api_key.get():
            os.environ['OPENAI_API_KEY'] = self.openai_api_key.get()
        if self.dify_api_key.get():
            os.environ['DIFY_API_KEY'] = self.dify_api_key.get()
        if self.dify_base_url.get():
            os.environ['DIFY_BASE_URL'] = self.dify_base_url.get()
        
        # 飞书配置
        if self.feishu_webhook.get():
            os.environ['FEISHU_WEBHOOK_URL'] = self.feishu_webhook.get()
        if self.feishu_secret.get():
            os.environ['FEISHU_WEBHOOK_SECRET'] = self.feishu_secret.get()
        
        # OSS配置
        if self.oss_bucket.get():
            os.environ['OSS_BUCKET_NAME'] = self.oss_bucket.get()
        if self.oss_endpoint.get():
            os.environ['OSS_ENDPOINT'] = self.oss_endpoint.get()
        if self.oss_access_key_id.get():
            os.environ['OSS_ACCESS_KEY_ID'] = self.oss_access_key_id.get()
        if self.oss_access_key_secret.get():
            os.environ['OSS_ACCESS_KEY_SECRET'] = self.oss_access_key_secret.get()
    
    def start_analysis(self):
        """开始分析"""
        if self.is_running:
            self.log("⚠️ 分析正在进行中，请等待...")
            return
        
        if not self.file_path.get():
            messagebox.showwarning("警告", "请先选择数据文件")
            return
        
        if not Path(self.file_path.get()).exists():
            messagebox.showerror("错误", f"文件不存在: {self.file_path.get()}")
            return
        
        # 验证必需配置
        if self.enable_llm.get():
            if not any([self.aliyun_api_key.get(), self.openai_api_key.get(), self.dify_api_key.get()]):
                messagebox.showwarning("警告", "启用LLM分析需要配置至少一个LLM API Key")
                return
        
        if self.enable_push.get() and not self.feishu_webhook.get():
            messagebox.showwarning("警告", "启用飞书推送需要配置Webhook URL")
            return
        
        if self.enable_oss.get():
            if not all([self.oss_bucket.get(), self.oss_endpoint.get(), 
                       self.oss_access_key_id.get(), self.oss_access_key_secret.get()]):
                messagebox.showwarning("警告", "启用OSS上传需要配置所有OSS参数")
                return
        
        self.is_running = True
        self.run_button.config(state=tk.DISABLED, text="分析中...")
        self.log("=" * 60)
        self.log("开始执行分析流程...")
        
        # 设置环境变量
        self.set_env_vars()
        
        # 在新线程中运行
        thread = threading.Thread(target=self.run_analysis, daemon=True)
        thread.start()
    
    def run_analysis(self):
        """执行分析（在后台线程中）"""
        try:
            from scripts.run_monthly import main as run_main
            import shutil
            
            file_path = Path(self.file_path.get())
            raw_file = file_path.name
            
            # 检测月份
            from src.utils.file_validator import detect_month_from_file
            month = detect_month_from_file(file_path)
            
            # 复制文件到raw目录（如果文件不在raw目录中）
            raw_dir = PROJECT_ROOT / "data" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            target_file = raw_dir / raw_file
            
            # 检查源文件和目标文件是否是同一个文件
            if file_path.resolve() != target_file.resolve():
                shutil.copy2(file_path, target_file)
                self.log(f"文件已复制到: {target_file}")
            else:
                self.log(f"文件已在raw目录中: {target_file}")
            
            # 构建命令行参数
            old_argv = sys.argv
            sys.argv = ['run_monthly.py', month, raw_file]
            
            if self.enable_llm.get():
                sys.argv.append('--include-llm')
            if self.enable_oss.get():
                sys.argv.append('--upload-oss')
            if not self.enable_push.get():
                sys.argv.append('--skip-push')
            
            # 运行主函数
            run_main()
            
            sys.argv = old_argv
            
            self.log("=" * 60)
            self.log("✅ 分析完成！")
            self.root.after(0, lambda: messagebox.showinfo("完成", "分析已完成！"))
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ 分析失败: {error_msg}")
            import traceback
            traceback_str = traceback.format_exc()
            self.log(traceback_str)
            # 使用默认参数捕获变量，避免作用域问题
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("错误", f"分析失败: {msg}"))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.run_button.config(state=tk.NORMAL, text="开始分析"))


def main():
    """主函数"""
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

