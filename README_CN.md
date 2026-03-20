# VTracer 图像转矢量工具使用指南

## 项目介绍

VTracer 是一个开源的光栅图像转矢量图形工具，能够将 JPG、PNG 等格式的图像转换为高质量的 SVG 矢量图形。它支持彩色和黑白图像，能够消除锯齿并保留图像细节。

## 主要功能

- ✅ 支持彩色和黑白图像转换
- ✅ 消除锯齿，生成平滑曲线
- ✅ 支持三种曲线拟合模式：像素、多边形、样条曲线
- ✅ **新增：轮廓线宽功能**（1pt、2pt、3pt等）
- ✅ 批量转换支持
- ✅ 直观的GUI操作界面
- ✅ 详细的参数调整选项
- ✅ 转换失败诊断工具

## 安装方法

### 1. 安装 Rust（必须）
```bash
# Windows 用户
winget install Rustlang.Rust.MSVC

# 或从官网下载安装器
https://www.rust-lang.org/tools/install
```

### 2. 安装 VTracer
```bash
# 从源代码安装
cd c:\Users\zs\Desktop\11\vtracer-master\cmdapp
cargo install --path .

# 或从 crates.io 安装
cargo install vtracer
```

### 3. 验证安装
```bash
vtracer --version
```

## 命令行使用

### 基本用法
```bash
vtracer --input 输入图像路径 --output 输出SVG路径
```

### 示例
```bash
# 基本转换
vtracer --input "C:\Users\zs\Desktop\横图png\横图png\1.png" --output "output.svg"

# 添加2pt黑色轮廓
vtracer --input "image.jpg" --output "vector.svg" --stroke_width 2 --stroke_color black

# 使用高细节参数
vtracer --input "photo.png" --output "vector.svg" --mode spline --segment_length 3.5 --splice_threshold 10 --filter_speckle 2
```

### 常用参数

| 参数 | 描述 | 默认值 |
|------|------|--------|
| `--input` | 输入图像路径 | 必填 |
| `--output` | 输出SVG路径 | 必填 |
| `--colormode` | 颜色模式：`color`(彩色) 或 `bw`(黑白) | `color` |
| `--mode` | 曲线拟合：`pixel`、`polygon`、`spline` | `spline` |
| `--segment_length` | 段长度（3.5-10） | 4.0 |
| `--stroke_width` | 轮廓线宽（新增） | 无 |
| `--stroke_color` | 轮廓颜色（新增） | `black` |
| `--filter_speckle` | 噪点过滤 | 4 |
| `--path_precision` | 路径精度 | 2 |

## 图形界面使用

### 启动GUI应用
```bash
cd c:\Users\zs\Desktop\11\vtracer-master
python vtracer_batch_gui.py
```

### 使用步骤

1. **选择文件夹**：
   - 点击"浏览..."选择输入图像文件夹
   - 选择输出SVG文件夹

2. **检测图像**：
   - 点击"检测图像文件"按钮
   - 应用会自动识别支持的图像文件

3. **调整参数**：
   - 在参数设置区域调整转换选项
   - 特别注意新增的"轮廓线宽"和"轮廓颜色"设置

4. **执行转换**：
   - 点击"批量转换"按钮
   - 查看转换日志了解进度

5. **查看结果**：
   - 在输出文件夹中找到生成的SVG文件

## 新功能：轮廓线宽

### 使用方法

1. **命令行**：
   ```bash
   vtracer --input image.png --output vector.svg --stroke_width 2 --stroke_color black
   ```

2. **GUI界面**：
   - 在参数设置面板找到"轮廓线宽"和"轮廓颜色"
   - 设置线宽为1、2、3等数值（0表示不添加轮廓）
   - 选择轮廓颜色

### 支持的轮廓颜色
- 颜色名称：`black`、`white`、`red`、`green`、`blue`
- 十六进制值：`#000000`、`#ffffff`、`#ff0000`

## 批量转换指南

### 方法一：使用GUI应用（推荐）
1. 启动GUI应用
2. 选择包含多个图像的文件夹
3. 设置统一的转换参数
4. 点击"批量转换"

### 方法二：使用命令行批处理
```bash
# Windows批处理命令
for %%f in ("C:\输入文件夹\*.png", "C:\输入文件夹\*.jpg") do (
    vtracer --input "%%f" --output "C:\输出文件夹\%%~nf.svg" --stroke_width 2
)
```

## 转换失败诊断

如果遇到大量文件转换失败，可以使用诊断工具：

```bash
cd c:\Users\zs\Desktop\11\vtracer-master
python vtracer_diagnostic.py
```

### 诊断工具功能
- 检查图像文件完整性
- 分析转换失败原因
- 提供修复建议
- 生成详细诊断报告

## 常见问题解决

### 1. 转换失败
- **原因**：文件损坏、格式不兼容、参数错误
- **解决**：使用诊断工具检查，调整参数

### 2. 轮廓不显示
- **原因**：轮廓线宽设置为0
- **解决**：设置线宽为大于0的值（如1、2、3）

### 3. 文件过大
- **原因**：参数设置过于精细
- **解决**：增大`segment_length`，减小`path_precision`

### 4. 锯齿严重
- **原因**：曲线拟合模式不当
- **解决**：使用`--mode spline`，减小`segment_length`

## 最佳参数组合

### 高细节转换
```bash
--mode spline --segment_length 3.5 --splice_threshold 10 --filter_speckle 2 --path_precision 5
```

### 平衡质量与速度
```bash
--mode spline --segment_length 5 --splice_threshold 30 --filter_speckle 5 --path_precision 3
```

### 添加轮廓效果
```bash
--stroke_width 2 --stroke_color black --mode spline --segment_length 4
```

## 技术支持

如果您在使用过程中遇到问题，可以：
1. 查看转换日志获取详细错误信息
2. 使用诊断工具分析问题
3. 尝试调整参数组合
4. 检查图像文件完整性

## 更新记录

### 新增功能（2026-03-18）
- ✅ 添加轮廓线宽功能，支持1pt、2pt、3pt等
- ✅ 支持自定义轮廓颜色
- ✅ 更新GUI应用，添加轮廓控制
- ✅ 优化转换失败诊断工具

---

**祝您使用愉快！** 🎉

如有任何问题或建议，请随时反馈。