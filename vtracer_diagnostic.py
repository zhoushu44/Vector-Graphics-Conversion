import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image
import time

class VTracerDiagnosticTool:
    def __init__(self, root):
        self.root = root
        self.root.title("VTracer 转换失败诊断工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 初始化变量
        self.input_folder = tk.StringVar()
        self.diagnosing = False
        self.file_list = []
        self.failed_files = []
        self.diagnosis_results = []
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 1. 文件夹选择部分
        folder_frame = ttk.LabelFrame(main_frame, text="1. 选择文件夹", padding="10")
        folder_frame.pack(fill=tk.X, pady=10)
        
        # 输入文件夹
        ttk.Label(folder_frame, text="输入文件夹：").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=50).grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_folder).grid(row=0, column=2, pady=5)
        
        # 检测图像文件按钮
        ttk.Button(folder_frame, text="检测图像文件", command=self.detect_images).grid(row=1, column=1, sticky=tk.E, pady=10)
        
        # 文件列表
        self.file_tree = ttk.Treeview(folder_frame, columns=("文件名", "状态"), show="headings", height=8)
        self.file_tree.heading("文件名", text="文件名")
        self.file_tree.heading("状态", text="状态")
        self.file_tree.column("文件名", width=500)
        self.file_tree.column("状态", width=150, anchor=tk.CENTER)
        self.file_tree.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # 2. 诊断参数部分
        params_frame = ttk.LabelFrame(main_frame, text="2. 诊断参数", padding="10")
        params_frame.pack(fill=tk.X, pady=10)
        
        # 测试模式
        self.test_mode = tk.StringVar(value="quick")
        ttk.Radiobutton(params_frame, text="快速测试 (仅检查文件有效性)", variable=self.test_mode, value="quick").grid(row=0, column=0, sticky=tk.W, pady=5, padx=10)
        ttk.Radiobutton(params_frame, text="完整测试 (测试实际转换)", variable=self.test_mode, value="full").grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        
        # 3. 操作按钮部分
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        # 开始诊断按钮
        self.diagnose_btn = ttk.Button(action_frame, text="开始诊断", command=self.start_diagnosis, style="Accent.TButton")
        self.diagnose_btn.pack(side=tk.LEFT, padx=5)
        
        # 修复建议按钮
        self.fix_btn = ttk.Button(action_frame, text="显示修复建议", command=self.show_fix_suggestions)
        self.fix_btn.pack(side=tk.LEFT, padx=5)
        
        # 导出报告按钮
        self.export_btn = ttk.Button(action_frame, text="导出报告", command=self.export_report)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # 4. 诊断结果部分
        result_frame = ttk.LabelFrame(main_frame, text="3. 诊断结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 结果统计
        self.result_stats = tk.Label(result_frame, text="未开始诊断")
        self.result_stats.pack(anchor=tk.W, pady=5)
        
        # 结果日志
        self.result_text = tk.Text(result_frame, height=15, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 日志滚动条
        result_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.configure(yscrollcommand=result_scrollbar.set)
        
        # 清空结果按钮
        ttk.Button(result_frame, text="清空结果", command=self.clear_result).pack(side=tk.BOTTOM, pady=5)
        
        # 配置样式
        style = ttk.Style()
        style.configure("Accent.TButton", font=(None, 10, "bold"))
        style.configure("Error.Treeview.Cell", foreground="red")
        style.configure("Warning.Treeview.Cell", foreground="orange")
        style.configure("Success.Treeview.Cell", foreground="green")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择包含图像的文件夹")
        if folder:
            self.input_folder.set(folder)
    
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
                    self.file_list.append((filename, file_path))
                    self.file_tree.insert('', tk.END, values=(filename, "未检查"))
            
            self.log_result(f"已检测到 {len(self.file_list)} 个图像文件")
        except Exception as e:
            messagebox.showerror("错误", f"检测文件时出错：{str(e)}")
            self.log_result(f"检测文件时出错：{str(e)}")
    
    def start_diagnosis(self):
        if self.diagnosing:
            messagebox.showinfo("提示", "诊断正在进行中，请稍候")
            return
        
        input_folder = self.input_folder.get()
        if not input_folder:
            messagebox.showwarning("警告", "请选择输入文件夹")
            return
        
        if not self.file_list:
            self.detect_images()
            if not self.file_list:
                messagebox.showwarning("警告", "未检测到图像文件")
                return
        
        # 开始诊断（在新线程中执行）
        self.diagnosing = True
        self.diagnose_btn.configure(state=tk.DISABLED)
        self.fix_btn.configure(state=tk.DISABLED)
        self.export_btn.configure(state=tk.DISABLED)
        
        self.diagnosis_results = []
        self.failed_files = []
        
        threading.Thread(target=self.diagnose_files).start()
    
    def diagnose_files(self):
        self.log_result("开始诊断...")
        
        success_count = 0
        error_count = 0
        warning_count = 0
        
        for i, (filename, file_path) in enumerate(self.file_list):
            self.log_result(f"诊断进度：{i+1}/{len(self.file_list)}")
            
            # 更新文件列表状态
            self.root.after(0, lambda item=self.file_tree.get_children()[i]: 
                           self.file_tree.item(item, values=(filename, "检查中")))
            
            result = self.check_file(filename, file_path)
            self.diagnosis_results.append(result)
            
            if result["status"] == "success":
                success_count += 1
                self.root.after(0, lambda item=self.file_tree.get_children()[i]: 
                               self.file_tree.item(item, values=(filename, "正常"), tags=("success",)))
            elif result["status"] == "error":
                error_count += 1
                self.failed_files.append((filename, file_path, result["error"]))
                self.root.after(0, lambda item=self.file_tree.get_children()[i]: 
                               self.file_tree.item(item, values=(filename, "错误"), tags=("error",)))
            else:
                warning_count += 1
                self.root.after(0, lambda item=self.file_tree.get_children()[i]: 
                               self.file_tree.item(item, values=(filename, "警告"), tags=("warning",)))
        
        # 更新结果统计
        self.root.after(0, lambda: self.result_stats.configure(
            text=f"诊断完成：正常 {success_count} 个，警告 {warning_count} 个，错误 {error_count} 个"
        ))
        
        self.log_result("诊断完成！")
        self.log_result(f"正常：{success_count} 个文件")
        self.log_result(f"警告：{warning_count} 个文件")
        self.log_result(f"错误：{error_count} 个文件")
        
        if error_count > 0:
            self.log_result(f"\n失败文件列表：")
            for filename, _, error in self.failed_files[:10]:  # 只显示前10个
                self.log_result(f"- {filename}: {error[:50]}...")
            if error_count > 10:
                self.log_result(f"... 还有 {error_count-10} 个失败文件")
        
        # 恢复按钮状态
        self.root.after(0, self.enable_buttons)
    
    def check_file(self, filename, file_path):
        result = {
            "filename": filename,
            "path": file_path,
            "status": "success",
            "error": "",
            "warnings": [],
            "details": {}
        }
        
        try:
            # 1. 检查文件是否存在
            if not os.path.exists(file_path):
                result["status"] = "error"
                result["error"] = "文件不存在"
                return result
            
            # 2. 检查文件权限
            if not os.access(file_path, os.R_OK):
                result["status"] = "error"
                result["error"] = "无读取权限"
                return result
            
            # 3. 检查文件大小
            file_size = os.path.getsize(file_path)
            result["details"]["size"] = file_size
            
            if file_size == 0:
                result["status"] = "error"
                result["error"] = "文件为空"
                return result
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                result["warnings"].append("文件过大，可能导致转换失败")
            
            # 4. 使用PIL检查图像有效性
            try:
                with Image.open(file_path) as img:
                    img.verify()  # 验证文件格式
                    img_info = img.info
                    result["details"]["format"] = img.format
                    result["details"]["size"] = img.size
                    result["details"]["mode"] = img.mode
            except Exception as e:
                result["status"] = "error"
                result["error"] = f"图像文件损坏：{str(e)}"
                return result
            
            # 5. 快速测试模式下完成
            if self.test_mode.get() == "quick":
                return result
            
            # 6. 完整测试模式：实际执行转换测试
            try:
                # 创建临时输出文件
                temp_output = os.path.join(os.path.dirname(file_path), f"temp_{os.path.splitext(filename)[0]}.svg")
                
                # 构建简单的测试命令
                cmd = f"vtracer --input \"{file_path}\" --output \"{temp_output}\" --colormode color --mode spline --segment_length 5 --filter_speckle 10"
                
                # 执行转换测试
                process = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                
                if process.returncode != 0:
                    result["status"] = "error"
                    result["error"] = f"转换失败：{process.stderr[:100]}..."
                    
                    # 尝试分析错误原因
                    if "Out of Range Error" in process.stderr:
                        result["warnings"].append("参数值超出有效范围")
                    elif "memory" in process.stderr.lower():
                        result["warnings"].append("内存不足")
                    elif "format" in process.stderr.lower():
                        result["warnings"].append("图像格式不兼容")
                else:
                    # 清理临时文件
                    if os.path.exists(temp_output):
                        os.remove(temp_output)
            except subprocess.TimeoutExpired:
                result["status"] = "error"
                result["error"] = "转换超时"
            except Exception as e:
                result["status"] = "error"
                result["error"] = f"转换测试出错：{str(e)}"
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"检查时出错：{str(e)}"
        
        return result
    
    def enable_buttons(self):
        self.diagnosing = False
        self.diagnose_btn.configure(state=tk.NORMAL)
        self.fix_btn.configure(state=tk.NORMAL)
        self.export_btn.configure(state=tk.NORMAL)
    
    def show_fix_suggestions(self):
        if not self.diagnosis_results:
            messagebox.showinfo("提示", "请先运行诊断")
            return
        
        # 分析失败原因
        error_reasons = {}
        for result in self.diagnosis_results:
            if result["status"] == "error":
                error = result["error"]
                error_reasons[error] = error_reasons.get(error, 0) + 1
        
        # 生成修复建议
        suggestions = "# VTracer 转换失败修复建议\n\n"
        suggestions += "## 失败原因统计\n"
        for error, count in error_reasons.items():
            suggestions += f"- {error}: {count} 个文件\n"
        
        suggestions += "\n## 修复方案\n"
        
        if any("文件不存在" in error for error in error_reasons.keys()):
            suggestions += "1. 文件不存在：\n"
            suggestions += "   - 检查文件路径是否正确\n"
            suggestions += "   - 确保文件没有被移动或删除\n"
        
        if any("无读取权限" in error for error in error_reasons.keys()):
            suggestions += "2. 无读取权限：\n"
            suggestions += "   - 检查文件权限设置\n"
            suggestions += "   - 尝试以管理员身份运行程序\n"
        
        if any("文件为空" in error for error in error_reasons.keys()):
            suggestions += "3. 文件为空：\n"
            suggestions += "   - 删除空文件或重新下载\n"
        
        if any("图像文件损坏" in error for error in error_reasons.keys()):
            suggestions += "4. 图像文件损坏：\n"
            suggestions += "   - 使用图像查看器验证文件完整性\n"
            suggestions += "   - 尝试重新下载或恢复文件\n"
            suggestions += "   - 使用图像编辑软件修复损坏的文件\n"
        
        if any("参数值超出有效范围" in warning for result in self.diagnosis_results for warning in result["warnings"]):
            suggestions += "5. 参数超出范围：\n"
            suggestions += "   - 确保segment_length在3.5-10之间\n"
            suggestions += "   - 检查其他参数是否在有效范围内\n"
        
        if any("内存不足" in warning for result in self.diagnosis_results for warning in result["warnings"]):
            suggestions += "6. 内存不足：\n"
            suggestions += "   - 减少同时转换的文件数量\n"
            suggestions += "   - 增加系统内存\n"
            suggestions += "   - 降低图像分辨率\n"
        
        if any("图像格式不兼容" in warning for result in self.diagnosis_results for warning in result["warnings"]):
            suggestions += "7. 格式不兼容：\n"
            suggestions += "   - 确保文件格式为PNG、JPG、JPEG、BMP或GIF\n"
            suggestions += "   - 尝试将文件转换为PNG格式后再转换\n"
        
        if any("转换超时" in error for error in error_reasons.keys()):
            suggestions += "8. 转换超时：\n"
            suggestions += "   - 增加转换超时时间\n"
            suggestions += "   - 降低图像分辨率\n"
            suggestions += "   - 减少同时转换的文件数量\n"
        
        suggestions += "\n## 通用优化建议\n"
        suggestions += "1. 确保使用最新版本的VTracer\n"
        suggestions += "2. 尝试调整转换参数，特别是降低segment_length和path_precision\n"
        suggestions += "3. 对超大文件先进行缩放处理\n"
        suggestions += "4. 将文件按大小分批转换\n"
        suggestions += "5. 确保有足够的磁盘空间\n"
        
        # 显示建议
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, suggestions)
    
    def export_report(self):
        if not self.diagnosis_results:
            messagebox.showinfo("提示", "请先运行诊断")
            return
        
        # 导出报告文件
        file_path = filedialog.asksaveasfilename(
            title="导出诊断报告",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# VTracer 转换失败诊断报告\n")
                f.write(f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"检查文件总数：{len(self.diagnosis_results)}\n\n")
                
                # 统计信息
                success_count = sum(1 for r in self.diagnosis_results if r["status"] == "success")
                error_count = sum(1 for r in self.diagnosis_results if r["status"] == "error")
                warning_count = sum(1 for r in self.diagnosis_results if r["status"] == "warning")
                
                f.write("## 诊断结果统计\n")
                f.write(f"- 正常：{success_count} 个文件\n")
                f.write(f"- 警告：{warning_count} 个文件\n")
                f.write(f"- 错误：{error_count} 个文件\n\n")
                
                # 失败文件列表
                if error_count > 0:
                    f.write("## 失败文件列表\n")
                    for r in self.diagnosis_results:
                        if r["status"] == "error":
                            f.write(f"- {r['filename']}: {r['error']}\n")
                    f.write("\n")
                
                # 警告文件列表
                if warning_count > 0:
                    f.write("## 警告文件列表\n")
                    for r in self.diagnosis_results:
                        if r["status"] == "warning" and r["warnings"]:
                            f.write(f"- {r['filename']}: {', '.join(r['warnings'])}\n")
            
            messagebox.showinfo("成功", "诊断报告已导出")
        except Exception as e:
            messagebox.showerror("错误", f"导出报告失败：{str(e)}")
    
    def log_result(self, message):
        # 在结果文本框中添加消息
        self.root.after(0, lambda: self.result_text.insert(tk.END, f"{message}\n"))
        self.root.after(0, lambda: self.result_text.see(tk.END))
    
    def clear_result(self):
        # 清空结果
        self.result_text.delete(1.0, tk.END)
        self.result_stats.configure(text="未开始诊断")
        
        # 重置文件列表状态
        for i, item in enumerate(self.file_tree.get_children()):
            filename = self.file_list[i][0]
            self.file_tree.item(item, values=(filename, "未检查"), tags=())

if __name__ == "__main__":
    # 检查依赖
    try:
        import PIL
    except ImportError:
        messagebox.showerror("错误", "缺少PIL库，请安装：pip install pillow")
        sys.exit(1)
    
    try:
        result = subprocess.run("vtracer --version", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            messagebox.showerror("错误", "未检测到vtracer命令。请先安装：cargo install vtracer")
            sys.exit(1)
    except Exception as e:
        messagebox.showerror("错误", f"检查vtracer时出错：{str(e)}")
        sys.exit(1)
    
    # 创建主窗口
    root = tk.Tk()
    app = VTracerDiagnosticTool(root)
    root.mainloop()