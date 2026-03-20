# VTracerBatchGUI 打包说明

## 打包结果
已生成可分发版本：

- `E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/dist_batch_gui/VTracerBatchGUI/`

主程序：

- `VTracerBatchGUI.exe`

## 使用方法
1. 打开 `dist_batch_gui/VTracerBatchGUI/`
2. 双击运行 `VTracerBatchGUI.exe`
3. 在界面中选择：
   - 输入文件夹
   - 输出文件夹
   - 导出格式（`svg` 或 `png`）
4. 点击“检测图像文件”
5. 点击“批量转换”

## 分发给别人的时候
请**整个文件夹一起发**，不要只发单个 exe：

- `VTracerBatchGUI.exe`
- `_internal/`

原因：
- Python 运行时文件在 `_internal/` 里
- 已经把 `vtracer.exe` 一起打进 `_internal/`，目标电脑**不需要**安装 cargo，也**不需要**单独安装 vtracer

## 当前程序行为
- 支持批量读取这些输入格式：`png` `jpg` `jpeg` `bmp` `gif`
- 支持导出格式：`svg` `png`
- 会按照界面里选择的导出格式生成对应文件
- 可以导出/导入参数文本

## 这次顺手清理的内容
在 `vtracer_batch_gui.py` 里去掉了明显没用的部分：

- 删除了 `batch_convert()` 里未使用的 `input_folder`
- 删除了循环里未使用的 `file_size` 变量引用
- 启动报错弹窗后补了 `startup_root.destroy()`，避免隐藏根窗口残留

## 打包命令
本次使用的是 PyInstaller：

```bash
python -m PyInstaller --noconfirm --clean --windowed --name "VTracerBatchGUI" --distpath "E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/dist_batch_gui" --workpath "E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/build_pyinstaller" --specpath "E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/build_pyinstaller" --add-binary "E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/vtracer.exe;." "E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/vtracer_batch_gui.py"
```

## 如果打不开
优先检查：
1. 是否把整个 `VTracerBatchGUI` 文件夹完整复制到了目标电脑
2. `_internal/vtracer.exe` 是否还在
3. 是否被杀毒软件拦截
4. 目标电脑是否缺少系统运行库

## 源文件
- GUI 源码：`E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/vtracer_batch_gui.py`
- 打包输出：`E:/360MoveData/Users/Administrator/Desktop/svg/11/vtracer-master/dist_batch_gui/VTracerBatchGUI/`
