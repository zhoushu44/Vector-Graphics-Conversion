import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.messagebox import showinfo, showerror
import sys
import os

# Add the cmdapp directory to the path so we can import vtracer
sys.path.append(os.path.join(os.path.dirname(__file__), 'cmdapp'))

from vtracer import convert_image_to_format

class VTracerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VTracer GUI")
        self.root.geometry("600x400")
        
        self.input_path = ""
        self.output_path = ""
        
        self.create_widgets()
    
    def create_widgets(self):
        # Input file selection
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="Input Image:").pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(input_frame, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_input).pack(side=tk.LEFT)
        
        # Output file selection
        output_frame = ttk.Frame(self.root, padding="10")
        output_frame.pack(fill=tk.X)
        
        ttk.Label(output_frame, text="Output File:").pack(side=tk.LEFT)
        self.output_entry = ttk.Entry(output_frame, width=50)
        self.output_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(output_frame, text="Browse", command=self.browse_output).pack(side=tk.LEFT)
        
        # Output format selection
        format_frame = ttk.Frame(self.root, padding="10")
        format_frame.pack(fill=tk.X)
        
        ttk.Label(format_frame, text="Output Format:").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="svg")
        format_options = ttk.Combobox(format_frame, textvariable=self.format_var, values=["svg", "png", "ai"])
        format_options.pack(side=tk.LEFT, padx=5)
        format_options.bind("<<ComboboxSelected>>", self.update_output_extension)
        
        # Conversion parameters
        params_frame = ttk.LabelFrame(self.root, text="Parameters", padding="10")
        params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Color mode
        ttk.Label(params_frame, text="Color Mode:").grid(row=0, column=0, sticky=tk.W)
        self.colormode_var = tk.StringVar(value="color")
        ttk.Radiobutton(params_frame, text="Color", variable=self.colormode_var, value="color").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(params_frame, text="Binary", variable=self.colormode_var, value="binary").grid(row=0, column=2, sticky=tk.W)
        
        # Hierarchical
        ttk.Label(params_frame, text="Hierarchical:").grid(row=1, column=0, sticky=tk.W)
        self.hierarchical_var = tk.StringVar(value="stacked")
        ttk.Radiobutton(params_frame, text="Stacked", variable=self.hierarchical_var, value="stacked").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(params_frame, text="Cutout", variable=self.hierarchical_var, value="cutout").grid(row=1, column=2, sticky=tk.W)
        
        # Mode
        ttk.Label(params_frame, text="Curve Fitting:").grid(row=2, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="spline")
        mode_options = ttk.Combobox(params_frame, textvariable=self.mode_var, values=["spline", "polygon", "none"])
        mode_options.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Filter speckle
        ttk.Label(params_frame, text="Filter Speckle:").grid(row=3, column=0, sticky=tk.W)
        self.filter_speckle_var = tk.IntVar(value=4)
        ttk.Spinbox(params_frame, from_=0, to=128, textvariable=self.filter_speckle_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Convert button
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Convert", command=self.convert, style="Accent.TButton").pack(side=tk.RIGHT)
    
    def browse_input(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            self.input_path = file_path
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, file_path)
            
            # Auto-set output path with .svg extension
            output_path = os.path.splitext(file_path)[0] + ".svg"
            self.output_path = output_path
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, output_path)
    
    def browse_output(self):
        format = self.format_var.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=[
                ("SVG Files", "*.svg"),
                ("PNG Files", "*.png"),
                ("AI Files", "*.ai"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.output_path = file_path
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, file_path)
    
    def update_output_extension(self, event=None):
        if not self.output_path:
            return
            
        format = self.format_var.get()
        base_name, _ = os.path.splitext(self.output_path)
        new_output_path = f"{base_name}.{format}"
        self.output_path = new_output_path
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, new_output_path)
    
    def convert(self):
        if not self.input_path:
            showerror("Error", "Please select an input image.")
            return
            
        if not self.output_path:
            showerror("Error", "Please select an output file.")
            return
            
        try:
            convert_image_to_format(
                self.input_path,
                self.output_path,
                self.format_var.get(),
                self.colormode_var.get(),
                self.hierarchical_var.get(),
                self.mode_var.get(),
                self.filter_speckle_var.get(),
                None,  # color_precision
                None,  # layer_difference
                None,  # corner_threshold
                None,  # length_threshold
                None,  # max_iterations
                None,  # splice_threshold
                None,  # path_precision
            )
            showinfo("Success", f"Conversion completed successfully!\nOutput saved to: {self.output_path}")
        except Exception as e:
            showerror("Error", f"Conversion failed:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    
    # Add custom style for accent button
    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="#00275D")
    
    app = VTracerGUI(root)
    root.mainloop()