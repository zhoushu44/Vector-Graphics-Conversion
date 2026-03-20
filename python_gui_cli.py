import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.messagebox import showinfo, showerror
import sys
import os
import subprocess
import tempfile
import shutil
import fitz  # PyMuPDF用于处理PDF/AI文件

class VTracerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VTracer 图形界面")
        self.root.geometry("800x500")
        
        self.input_path = ""
        self.output_path = ""
        self.is_processing = False
        
        # Find the vtracer executable
        self.vtracer_path = self.find_vtracer_executable()
        if not self.vtracer_path:
            showerror("错误", "找不到 vtracer 可执行文件。请先使用 'cargo build --release' 构建它")
            self.root.destroy()
            return
        
        self.create_widgets()
    
    def find_vtracer_executable(self):
        # Check in target/debug
        debug_path = os.path.join(os.path.dirname(__file__), 'target', 'debug', 'vtracer.exe')
        if os.path.exists(debug_path):
            return debug_path
        
        # Check in target/release
        release_path = os.path.join(os.path.dirname(__file__), 'target', 'release', 'vtracer.exe')
        if os.path.exists(release_path):
            return release_path
        
        return None
    
    def create_widgets(self):
        # Logo and title frame
        logo_frame = ttk.Frame(self.root, padding="5")
        logo_frame.pack(fill=tk.X)
        
        # Try to load and display logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'docs', 'assets', 'visioncortex-logo.svg')
            if os.path.exists(logo_path):
                self.logo = tk.PhotoImage(file=logo_path)
                logo_label = ttk.Label(logo_frame, image=self.logo)
                logo_label.pack(side=tk.LEFT, padx=5)
        except Exception as e:
            # If logo can't be loaded, just show text
            ttk.Label(logo_frame, text="VTracer", font=('Arial', 16, 'bold')).pack(side=tk.LEFT, padx=5)
        
        # Input folder selection
        input_frame = ttk.Frame(self.root, padding="5")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="输入文件夹:").pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(input_frame, width=55)
        self.input_entry.pack(side=tk.LEFT, padx=3)
        ttk.Button(input_frame, text="浏览", command=self.browse_input_folder, width=6).pack(side=tk.LEFT)
        
        # Output folder selection
        output_frame = ttk.Frame(self.root, padding="5")
        output_frame.pack(fill=tk.X)
        
        ttk.Label(output_frame, text="输出文件夹:").pack(side=tk.LEFT)
        self.output_entry = ttk.Entry(output_frame, width=55)
        self.output_entry.pack(side=tk.LEFT, padx=3)
        ttk.Button(output_frame, text="浏览", command=self.browse_output_folder, width=6).pack(side=tk.LEFT)
        
        # Output format selection
        format_frame = ttk.Frame(self.root, padding="5")
        format_frame.pack(fill=tk.X)
        
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="svg")
        format_options = ttk.Combobox(format_frame, textvariable=self.format_var, values=["svg", "png", "ai"], width=10)
        format_options.pack(side=tk.LEFT, padx=3)
        
        # Preset selection
        preset_frame = ttk.Frame(self.root, padding="5")
        preset_frame.pack(fill=tk.X)
        
        ttk.Label(preset_frame, text="预设:").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar(value="")
        preset_options = ttk.Combobox(preset_frame, textvariable=self.preset_var, values=["", "bw", "poster", "photo"], width=15)
        preset_options.pack(side=tk.LEFT, padx=3)
        
        # Conversion parameters
        params_frame = ttk.LabelFrame(self.root, text="参数设置", padding="5")
        params_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Color mode
        ttk.Label(params_frame, text="颜色模式:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        self.colormode_var = tk.StringVar(value="color")
        ttk.Radiobutton(params_frame, text="彩色", variable=self.colormode_var, value="color").grid(row=0, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(params_frame, text="黑白", variable=self.colormode_var, value="binary").grid(row=0, column=2, sticky=tk.W, pady=2)
        
        # Hierarchical
        ttk.Label(params_frame, text="分层模式:").grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)
        self.hierarchical_var = tk.StringVar(value="stacked")
        ttk.Radiobutton(params_frame, text="堆叠", variable=self.hierarchical_var, value="stacked").grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(params_frame, text="剪切", variable=self.hierarchical_var, value="cutout").grid(row=1, column=2, sticky=tk.W, pady=2)
        ttk.Label(params_frame, text="(堆叠: 形状堆叠在一起；剪切: 形状相互独立)", foreground="gray", font=('Arial', 7)).grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=2, pady=(0, 2))
        
        # Mode
        ttk.Label(params_frame, text="曲线拟合:").grid(row=3, column=0, sticky=tk.W, padx=2, pady=2)
        self.mode_var = tk.StringVar(value="spline")
        mode_options = ttk.Combobox(params_frame, textvariable=self.mode_var, values=["spline", "polygon", "none"], width=10)
        mode_options.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=2, pady=2)
        
        # Filter speckle
        ttk.Label(params_frame, text="滤镜斑点:").grid(row=4, column=0, sticky=tk.W, padx=2, pady=2)
        self.filter_speckle_var = tk.IntVar(value=4)
        ttk.Spinbox(params_frame, from_=0, to=128, textvariable=self.filter_speckle_var, width=8).grid(row=4, column=1, sticky=tk.W, padx=2, pady=2)
        
        # Color precision
        ttk.Label(params_frame, text="颜色精度:").grid(row=5, column=0, sticky=tk.W, padx=2, pady=2)
        self.color_precision_var = tk.IntVar(value=6)
        ttk.Spinbox(params_frame, from_=1, to=8, textvariable=self.color_precision_var, width=8).grid(row=5, column=1, sticky=tk.W, padx=2, pady=2)
        
        # Gradient step
        ttk.Label(params_frame, text="梯度步长:").grid(row=6, column=0, sticky=tk.W, padx=2, pady=2)
        self.gradient_step_var = tk.IntVar(value=16)
        ttk.Spinbox(params_frame, from_=0, to=255, textvariable=self.gradient_step_var, width=8).grid(row=6, column=1, sticky=tk.W, padx=2, pady=2)
        
        # Corner threshold
        ttk.Label(params_frame, text="角阈值:").grid(row=7, column=0, sticky=tk.W, padx=2, pady=2)
        self.corner_threshold_var = tk.IntVar(value=60)
        ttk.Spinbox(params_frame, from_=0, to=180, textvariable=self.corner_threshold_var, width=8).grid(row=7, column=1, sticky=tk.W, padx=2, pady=2)
        
        # Segment length
        ttk.Label(params_frame, text="段长度:").grid(row=8, column=0, sticky=tk.W, padx=2, pady=2)
        self.segment_length_var = tk.DoubleVar(value=4.0)
        ttk.Spinbox(params_frame, from_=3.5, to=10.0, increment=0.5, textvariable=self.segment_length_var, width=8).grid(row=8, column=1, sticky=tk.W, padx=2, pady=2)
        
        # Splice threshold
        ttk.Label(params_frame, text="拼接阈值:").grid(row=9, column=0, sticky=tk.W, padx=2, pady=2)
        self.splice_threshold_var = tk.IntVar(value=45)
        ttk.Spinbox(params_frame, from_=0, to=180, textvariable=self.splice_threshold_var, width=8).grid(row=9, column=1, sticky=tk.W, padx=2, pady=2)
        ttk.Label(params_frame, text="(曲线之间的最小角度位移，决定是否拼接为一条曲线)", foreground="gray", font=('Arial', 7)).grid(row=10, column=0, columnspan=3, sticky=tk.W, padx=2, pady=(0, 2))
        
        # Path precision
        ttk.Label(params_frame, text="路径精度:").grid(row=11, column=0, sticky=tk.W, padx=2, pady=2)
        self.path_precision_var = tk.IntVar(value=2)
        ttk.Spinbox(params_frame, from_=0, to=16, textvariable=self.path_precision_var, width=8).grid(row=11, column=1, sticky=tk.W, padx=2, pady=2)
        
        # Stroke width
        ttk.Label(params_frame, text="描边宽度:").grid(row=12, column=0, sticky=tk.W, padx=2, pady=2)
        self.stroke_width_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(params_frame, from_=0.0, to=20.0, increment=0.5, textvariable=self.stroke_width_var, width=8).grid(row=12, column=1, sticky=tk.W, padx=2, pady=2)
        
        # Stroke color
        ttk.Label(params_frame, text="描边颜色:").grid(row=13, column=0, sticky=tk.W, padx=2, pady=2)
        self.stroke_color_var = tk.StringVar(value="")
        stroke_color_frame = ttk.Frame(params_frame)
        stroke_color_frame.grid(row=13, column=1, sticky=tk.W, padx=2, pady=2)
        ttk.Entry(stroke_color_frame, textvariable=self.stroke_color_var, width=15).pack(side=tk.LEFT, padx=2)
        # 添加黑色和红色快速选择按钮
        ttk.Button(stroke_color_frame, text="黑色", command=lambda: self.stroke_color_var.set("black"), width=4).pack(side=tk.LEFT, padx=2)
        ttk.Button(stroke_color_frame, text="红色", command=lambda: self.stroke_color_var.set("red"), width=4).pack(side=tk.LEFT, padx=2)
        
        # Convert button
        button_frame = ttk.Frame(self.root, padding="5")
        button_frame.pack(fill=tk.X)
        
        self.convert_button = ttk.Button(button_frame, text="开始转换", command=self.convert, style="Accent.TButton", width=10)
        self.convert_button.pack(side=tk.RIGHT)
        
        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="转换日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Log text widget
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for log
        scrollbar = ttk.Scrollbar(self.log_text, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set) 
        
        # Make log text read-only
        self.log_text.config(state=tk.DISABLED)
    
    def browse_input_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.input_path = folder_path
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, folder_path)
    
    def browse_output_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_path = folder_path
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder_path)
    
    def log_message(self, message):
        """在日志框中添加消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)  # 自动滚动到最后一行
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()  # 更新界面
    
    def convert(self):
        if not self.input_path:
            showerror("错误", "请选择输入文件夹。")
            return
            
        if not self.output_path:
            showerror("错误", "请选择输出文件夹。")
            return
            
        if self.is_processing:
            showerror("错误", "转换正在进行中，请稍候。")
            return
            
        self.is_processing = True
        self.convert_button.config(text="转换中...", state=tk.DISABLED)
        
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        try:
            # 获取输出格式
            output_format = self.format_var.get()
            
            # 收集输入文件夹中的所有文件
            files_to_process = []
            ai_files = []
            
            for file_name in os.listdir(self.input_path):
                file_path = os.path.join(self.input_path, file_name)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file_name)[1].lower()
                    if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                        files_to_process.append((file_name, file_path, False))  # (文件名, 文件路径, 是否为AI文件)
                    elif ext in ['.ai']:
                        ai_files.append((file_name, file_path))
            
            # 检查是否有AI文件需要处理
            if ai_files:
                self.log_message(f"找到 {len(ai_files)} 个AI文件，尝试转换为PNG...")
                try:
                    # 检查PyMuPDF是否可用
                    import fitz
                    
                    # 为每个AI文件创建临时PNG文件
                    for file_name, file_path in ai_files:
                        try:
                            # 打开AI文件（本质上是PDF）
                            doc = fitz.open(file_path)
                            if doc.page_count > 0:
                                # 获取第一页
                                page = doc[0]
                                
                                # 设置图像分辨率
                                zoom = 2.0  # 200%分辨率
                                mat = fitz.Matrix(zoom, zoom)
                                pix = page.get_pixmap(matrix=mat)
                                
                                # 创建临时PNG文件
                                temp_png_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(file_name)[0]}.png")
                                pix.save(temp_png_path)
                                
                                # 添加到处理列表
                                files_to_process.append((file_name, temp_png_path, True))
                                self.log_message(f"✓ {file_name} 已转换为PNG临时文件")
                            else:
                                self.log_message(f"✗ {file_name} 没有页面")
                        except Exception as e:
                            self.log_message(f"✗ {file_name} 转换失败: {str(e)}")
                except ImportError:
                    self.log_message("错误: 无法处理AI文件，因为缺少PyMuPDF库。")
                    self.log_message("请运行 'pip install pymupdf' 安装所需库。")
                    self.log_message("AI文件将被跳过。")
            
            if len(files_to_process) == 0:
                self.log_message("错误: 输入文件夹中没有找到可处理的图像文件 (支持的格式: PNG, JPG, JPEG, BMP, GIF, AI)")
                return
            
            self.log_message(f"找到 {len(image_files)} 个图像文件，开始转换...")
            
            # 构建基本命令行参数
            base_cmd = [
                self.vtracer_path,
                "-t", output_format,
            ]
            
            # 添加预设或自定义参数
            if self.preset_var.get():
                base_cmd.extend(["--preset", self.preset_var.get()])
            else:
                base_cmd.extend([
                    "--colormode", self.colormode_var.get(),
                    "--hierarchical", self.hierarchical_var.get(),
                    "--mode", self.mode_var.get(),
                    "--filter_speckle", str(self.filter_speckle_var.get()),
                    "--color_precision", str(self.color_precision_var.get()),
                    "--gradient_step", str(self.gradient_step_var.get()),
                    "--corner_threshold", str(self.corner_threshold_var.get()),
                    "--segment_length", str(self.segment_length_var.get()),
                    "--splice_threshold", str(self.splice_threshold_var.get()),
                    "--path_precision", str(self.path_precision_var.get()),
                ])
                
                # 如果描边宽度大于0，则添加描边宽度参数
                if self.stroke_width_var.get() > 0:
                    base_cmd.extend(["--stroke_width", str(self.stroke_width_var.get())])
                
                # 如果指定了描边颜色，则添加描边颜色参数
                if self.stroke_color_var.get():
                    base_cmd.extend(["--stroke_color", self.stroke_color_var.get()])
            
            # 处理每个图像文件
            success_count = 0
            error_count = 0
            
            for file_name, input_file_path in image_files:
                self.log_message(f"正在处理: {file_name}")
                
                try:
                    # 构建输出文件名
                    base_name = os.path.splitext(file_name)[0]
                    output_file_path = os.path.join(self.output_path, f"{base_name}.{output_format}")
                    
                    # 构建完整命令
                    cmd = base_cmd.copy()
                    cmd.extend(["-i", input_file_path, "-o", output_file_path])
                    
                    # 执行命令
                    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    
                    self.log_message(f"✓ {file_name} 转换成功")
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    self.log_message(f"✗ {file_name} 转换失败: {e.stderr}")
                    error_count += 1
                except Exception as e:
                    self.log_message(f"✗ {file_name} 转换失败: {str(e)}")
                    error_count += 1
            
            self.log_message("")
            self.log_message(f"转换完成！")
            self.log_message(f"成功: {success_count} 个文件")
            self.log_message(f"失败: {error_count} 个文件")
            
            showinfo("成功", f"批量转换完成！\n成功: {success_count} 个文件\n失败: {error_count} 个文件")
            
        except Exception as e:
            self.log_message(f"发生错误: {str(e)}")
            showerror("错误", f"批量转换失败:\n{str(e)}")
        finally:
            self.is_processing = False
            self.convert_button.config(text="开始转换", state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    
    # Add custom style for accent button
    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="#00275D")
    
    app = VTracerGUI(root)
    root.mainloop()