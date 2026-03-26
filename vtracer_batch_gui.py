import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import shutil
import subprocess
import threading
import sys


def get_app_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_base_dir():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return get_app_base_dir()


def find_vtracer_executable():
    candidate_paths = [
        os.path.join(get_app_base_dir(), 'vtracer.exe'),
        os.path.join(get_app_base_dir(), 'tools', 'vtracer.exe'),
        os.path.join(get_resource_base_dir(), 'vtracer.exe'),
        os.path.join(get_resource_base_dir(), 'tools', 'vtracer.exe'),
    ]

    for path in candidate_paths:
        if os.path.isfile(path):
            return path

    return shutil.which('vtracer')


class VTracerBatchConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("VTracer 批量图像转矢量工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 初始化变量
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.converting = False
        self.file_list = []
        self.vtracer_path = find_vtracer_executable()

        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 文件夹选择部分
        folder_frame = ttk.LabelFrame(main_frame, text="1. 文件夹选择", padding="10")
        folder_frame.pack(fill=tk.X, pady=10)
        
        # 输入文件夹
        ttk.Label(folder_frame, text="输入文件夹：").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_input_folder).grid(row=0, column=2, pady=5)
        
        # 输出文件夹
        ttk.Label(folder_frame, text="输出文件夹：").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=50).grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_output_folder).grid(row=1, column=2, pady=5)
        
        # 检测图像文件按钮
        ttk.Button(folder_frame, text="检测图像文件", command=self.detect_images).grid(row=2, column=1, sticky=tk.E, pady=10)
        
        # 文件列表
        self.file_tree = ttk.Treeview(folder_frame, columns=("文件名", "大小"), show="headings", height=5)
        self.file_tree.heading("文件名", text="文件名")
        self.file_tree.heading("大小", text="大小 (KB)")
        self.file_tree.column("文件名", width=400)
        self.file_tree.column("大小", width=100, anchor=tk.CENTER)
        self.file_tree.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # 2. 参数设置部分
        params_frame = ttk.LabelFrame(main_frame, text="2. 转换参数", padding="10")
        params_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建参数网格
        param_grid = ttk.Frame(params_frame)
        param_grid.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # 参数变量
        self.params = {
            "colormode": tk.StringVar(value="color"),
            "mode": tk.StringVar(value="spline"),
            "hierarchical": tk.StringVar(value="stacked"),
            "format": tk.StringVar(value="svg"),
            "segment_length": tk.DoubleVar(value=3.5),
            "splice_threshold": tk.IntVar(value=10),
            "corner_threshold": tk.IntVar(value=30),
            "filter_speckle": tk.IntVar(value=2),
            "path_precision": tk.IntVar(value=5),
            "color_precision": tk.IntVar(value=8),
            "gradient_step": tk.IntVar(value=10),
            "stroke_width": tk.DoubleVar(value=0),
            "stroke_color": tk.StringVar(value="black"),
            "expand_stroke": tk.BooleanVar(value=False)
        }
        
        # 参数标签和控件
        row = 0
        
        # 颜色模式
        ttk.Label(param_grid, text="颜色模式：").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(param_grid, textvariable=self.params["colormode"], values=["color", "bw"], width=15).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(param_grid, text="曲线拟合：").grid(row=row, column=2, sticky=tk.W, pady=5, padx=20)
        ttk.Combobox(param_grid, textvariable=self.params["mode"], values=["pixel", "polygon", "spline"], width=15).grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1
        
        # 分层聚类
        ttk.Label(param_grid, text="分层聚类：").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(param_grid, textvariable=self.params["hierarchical"], values=["stacked", "cutout"], width=15).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(param_grid, text="导出格式：").grid(row=row, column=2, sticky=tk.W, pady=5, padx=20)
        ttk.Combobox(param_grid, textvariable=self.params["format"], values=["svg", "png"], width=15, state="readonly").grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1

        # 段长度
        ttk.Label(param_grid, text="段长度：").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(param_grid, from_=3.5, to=10.0, increment=0.5, textvariable=self.params["segment_length"], width=13).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # 样条拼接阈值
        ttk.Label(param_grid, text="样条拼接阈值：").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(param_grid, from_=0, to=180, increment=5, textvariable=self.params["splice_threshold"], width=13).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(param_grid, text="角点阈值：").grid(row=row, column=2, sticky=tk.W, pady=5, padx=20)
        ttk.Spinbox(param_grid, from_=0, to=180, increment=5, textvariable=self.params["corner_threshold"], width=13).grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1
        
        # 噪点过滤
        ttk.Label(param_grid, text="噪点过滤：").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(param_grid, from_=0, to=100, increment=1, textvariable=self.params["filter_speckle"], width=13).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(param_grid, text="路径精度：").grid(row=row, column=2, sticky=tk.W, pady=5, padx=20)
        ttk.Spinbox(param_grid, from_=0, to=8, increment=1, textvariable=self.params["path_precision"], width=13).grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1
        
        # 颜色精度
        ttk.Label(param_grid, text="颜色精度：").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(param_grid, from_=1, to=8, increment=1, textvariable=self.params["color_precision"], width=13).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(param_grid, text="渐变步长：").grid(row=row, column=2, sticky=tk.W, pady=5, padx=20)
        ttk.Spinbox(param_grid, from_=1, to=100, increment=1, textvariable=self.params["gradient_step"], width=13).grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1
        
        # 轮廓线宽
        ttk.Label(param_grid, text="轮廓线宽：").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(param_grid, from_=0, to=10, increment=0.5, textvariable=self.params["stroke_width"], width=13).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Label(param_grid, text="轮廓颜色：").grid(row=row, column=2, sticky=tk.W, pady=5, padx=20)
        ttk.Combobox(param_grid, textvariable=self.params["stroke_color"], values=["black", "white", "red", "green", "blue", "#000000", "#ffffff"], width=13).grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1

        ttk.Checkbutton(
            param_grid,
            text="将描边转为轮廓填充（移除原描边属性）",
            variable=self.params["expand_stroke"],
        ).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=5)
        row += 1

        # 3. 操作按钮部分
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        # 批量转换按钮
        self.convert_btn = ttk.Button(action_frame, text="批量转换", command=self.start_batch_conversion, style="Accent.TButton")
        self.convert_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出参数按钮
        self.export_btn = ttk.Button(action_frame, text="导出参数", command=self.export_params)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # 导入参数按钮
        self.import_btn = ttk.Button(action_frame, text="导入参数", command=self.import_params)
        self.import_btn.pack(side=tk.LEFT, padx=5)
        
        # 4. 日志输出部分
        log_frame = ttk.LabelFrame(main_frame, text="3. 转换日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 日志滚动条
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # 清空日志按钮
        ttk.Button(log_frame, text="清空日志", command=self.clear_log).pack(side=tk.BOTTOM, pady=5)
        
        # 配置样式
        style = ttk.Style()
        style.configure("Accent.TButton", font=(None, 10, "bold"))
    
    def browse_input_folder(self):
        folder = filedialog.askdirectory(title="选择输入文件夹")
        if folder:
            self.input_folder.set(folder)
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
    
    def detect_images(self):
        input_folder = self.input_folder.get()
        if not input_folder:
            messagebox.showwarning("警告", "请先选择输入文件夹")
            return
        
        # 清空文件列表
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        self.file_list = []
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        
        try:
            for filename in os.listdir(input_folder):
                ext = os.path.splitext(filename)[1].lower()
                if ext in supported_extensions:
                    file_path = os.path.join(input_folder, filename)
                    file_size = os.path.getsize(file_path) // 1024  # KB
                    self.file_list.append((filename, file_path, file_size))
                    self.file_tree.insert('', tk.END, values=(filename, file_size))
            
            self.log(f"已检测到 {len(self.file_list)} 个图像文件")
        except Exception as e:
            messagebox.showerror("错误", f"检测文件时出错：{str(e)}")
            self.log(f"检测文件时出错：{str(e)}")
    
    def start_batch_conversion(self):
        if self.converting:
            messagebox.showinfo("提示", "转换正在进行中，请稍候")
            return
        
        # 验证输入
        input_folder = self.input_folder.get()
        output_folder = self.output_folder.get()
        
        if not input_folder:
            messagebox.showwarning("警告", "请选择输入文件夹")
            return
        
        if not output_folder:
            messagebox.showwarning("警告", "请选择输出文件夹")
            return
        
        if not self.file_list:
            self.detect_images()
            if not self.file_list:
                messagebox.showwarning("警告", "未检测到图像文件")
                return
        
        # 创建输出文件夹（如果不存在）
        if not os.path.exists(output_folder):
            try:
                os.makedirs(output_folder)
                self.log(f"已创建输出文件夹：{output_folder}")
            except Exception as e:
                messagebox.showerror("错误", f"创建输出文件夹失败：{str(e)}")
                return
        
        # 开始转换（在新线程中执行）
        self.converting = True
        self.convert_btn.configure(state=tk.DISABLED)
        self.export_btn.configure(state=tk.DISABLED)
        self.import_btn.configure(state=tk.DISABLED)

        if not self.vtracer_path:
            messagebox.showerror("错误", "未找到 vtracer 可执行文件。请将 vtracer.exe 放到程序同目录或 tools 子目录后再试。")
            self.enable_buttons()
            return

        threading.Thread(target=self.batch_convert).start()
    
    def batch_convert(self):
        output_folder = self.output_folder.get()
        output_format = self.params['format'].get()

        self.log(f"开始批量转换，共 {len(self.file_list)} 个文件，输出格式：{output_format.upper()}")

        success_count = 0
        error_count = 0

        for i, (filename, file_path, _) in enumerate(self.file_list):
            self.log(f"转换进度：{i+1}/{len(self.file_list)}")
            self.log(f"正在转换：{filename}")

            # 生成输出路径
            output_filename = os.path.splitext(filename)[0] + f'.{output_format}'
            output_path = os.path.join(output_folder, output_filename)

            try:
                # 构建命令
                cmd = self.build_vtracer_command(file_path, output_path)
                self.log(f"执行命令：{cmd}")

                # 执行命令
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if result.returncode == 0:
                    self.log(f"✓ 转换成功：{filename} -> {output_filename}")
                    success_count += 1
                else:
                    self.log(f"✗ 转换失败：{filename}")
                    self.log(f"错误信息：{result.stderr}")
                    error_count += 1
            except Exception as e:
                self.log(f"✗ 转换出错：{filename}")
                self.log(f"异常信息：{str(e)}")
                error_count += 1

        # 转换完成
        self.log("批量转换完成！")
        self.log(f"成功：{success_count} 个文件")
        self.log(f"失败：{error_count} 个文件")

        # 恢复按钮状态
        self.root.after(0, self.enable_buttons)
    
    def build_vtracer_command(self, input_path, output_path):
        # 构建vtracer命令
        cmd = [
            f'"{self.vtracer_path}"',
            f"--input \"{input_path}\"",
            f"--output \"{output_path}\"",
            f"--colormode {self.params['colormode'].get()}",
            f"--mode {self.params['mode'].get()}",
            f"--hierarchical {self.params['hierarchical'].get()}",
            f"--format {self.params['format'].get()}",
            f"--segment_length {self.params['segment_length'].get()}",
            f"--splice_threshold {self.params['splice_threshold'].get()}",
            f"--corner_threshold {self.params['corner_threshold'].get()}",
            f"--filter_speckle {self.params['filter_speckle'].get()}",
            f"--path_precision {self.params['path_precision'].get()}",
            f"--color_precision {self.params['color_precision'].get()}",
            f"--gradient_step {self.params['gradient_step'].get()}"
        ]

        # 添加轮廓线参数（如果线宽大于0）
        stroke_width = self.params['stroke_width'].get()
        if stroke_width > 0:
            cmd.append(f"--stroke_width {stroke_width}")
            cmd.append(f"--stroke_color {self.params['stroke_color'].get()}")
            if self.params['expand_stroke'].get():
                cmd.append("--expand_stroke")

        return " ".join(cmd)
    
    def enable_buttons(self):
        self.converting = False
        self.convert_btn.configure(state=tk.NORMAL)
        self.export_btn.configure(state=tk.NORMAL)
        self.import_btn.configure(state=tk.NORMAL)
    
    def export_params(self):
        # 导出参数为文本文件
        file_path = filedialog.asksaveasfilename(
            title="导出参数",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# VTracer 批量转换参数配置\n")
                f.write("\n# 基本设置\n")
                f.write(f"--colormode {self.params['colormode'].get()}\n")
                f.write(f"--mode {self.params['mode'].get()}\n")
                f.write(f"--hierarchical {self.params['hierarchical'].get()}\n")
                f.write(f"--format {self.params['format'].get()}\n")

                f.write("\n# 曲线设置\n")
                f.write(f"--segment_length {self.params['segment_length'].get()}\n")
                f.write(f"--splice_threshold {self.params['splice_threshold'].get()}\n")
                f.write(f"--corner_threshold {self.params['corner_threshold'].get()}\n")

                f.write("\n# 精度设置\n")
                f.write(f"--filter_speckle {self.params['filter_speckle'].get()}\n")
                f.write(f"--path_precision {self.params['path_precision'].get()}\n")
                f.write(f"--color_precision {self.params['color_precision'].get()}\n")
                f.write(f"--gradient_step {self.params['gradient_step'].get()}\n")

                f.write("\n# 描边设置\n")
                f.write(f"--stroke_width {self.params['stroke_width'].get()}\n")
                f.write(f"--stroke_color {self.params['stroke_color'].get()}\n")
                if self.params['expand_stroke'].get():
                    f.write("--expand_stroke\n")

            self.log(f"参数已导出到：{file_path}")
            messagebox.showinfo("成功", "参数导出成功")
        except Exception as e:
            messagebox.showerror("错误", f"导出参数失败：{str(e)}")
            self.log(f"导出参数失败：{str(e)}")
    
    def import_params(self):
        # 导入参数文件
        file_path = filedialog.askopenfilename(
            title="导入参数",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if line.startswith('--expand_stroke'):
                            self.params['expand_stroke'].set(True)
                            continue

                        if line.startswith('--'):
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                param_name = parts[0][2:]
                                param_value = parts[1]

                                if param_name in self.params:
                                    param_var = self.params[param_name]
                                    if isinstance(param_var, tk.IntVar):
                                        param_var.set(int(param_value))
                                    elif isinstance(param_var, tk.DoubleVar):
                                        param_var.set(float(param_value))
                                    elif isinstance(param_var, tk.BooleanVar):
                                        param_var.set(param_value.lower() in ('1', 'true', 'yes', 'on'))
                                    else:
                                        param_var.set(param_value)
            
            self.log(f"参数已从：{file_path} 导入")
            messagebox.showinfo("成功", "参数导入成功")
        except Exception as e:
            messagebox.showerror("错误", f"导入参数失败：{str(e)}")
            self.log(f"导入参数失败：{str(e)}")
    
    def log(self, message):
        # 在日志中添加消息
        self.root.after(0, lambda: self.log_text.insert(tk.END, f"{message}\n"))
        self.root.after(0, lambda: self.log_text.see(tk.END))
    
    def clear_log(self):
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空")

if __name__ == "__main__":
    if not find_vtracer_executable():
        startup_root = tk.Tk()
        startup_root.withdraw()
        messagebox.showerror("错误", "未找到 vtracer 可执行文件。请将 vtracer.exe 放到程序同目录或 tools 子目录后再启动。")
        startup_root.destroy()
        sys.exit(1)

    # 创建主窗口
    root = tk.Tk()
    app = VTracerBatchConverter(root)
    root.mainloop()