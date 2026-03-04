import ezdxf
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread

class BlockExporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CAD块批量导出工具")
        self.root.geometry("600x450")  # 增加窗口高度
        self.root.resizable(True, True)
        
        # 设置字体
        self.font = ("微软雅黑", 10)
        
        # 初始化变量
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.is_exporting = False
        self.total_blocks = 0
        self.exported_blocks = 0
        self.log_queue = []  # 日志队列，减少UI更新频率
        self.log_update_timer = None
        
        # 创建UI组件
        self.create_widgets()
    
    def create_widgets(self):
        """创建所有UI组件，使用简单可靠的布局"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="CAD块批量导出工具", font=("微软雅黑", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10, sticky=tk.W)
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入DXF文件:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.input_file, font=self.font, width=40).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.browse_input_file, width=10).grid(row=1, column=2, padx=5, pady=5)
        
        # 输出目录选择
        ttk.Label(main_frame, text="输出目录:", font=self.font).grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.output_dir, font=self.font, width=40).grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.browse_output_dir, width=10).grid(row=2, column=2, padx=5, pady=5)
        
        # 进度条
        self.progress_label = ttk.Label(main_frame, text="准备导出...", font=self.font)
        self.progress_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate', maximum=100)
        self.progress_bar.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.progress_bar.grid_remove()  # 初始隐藏
        
        # 日志输出
        ttk.Label(main_frame, text="导出日志:", font=self.font).grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        
        # 日志框架
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        
        self.log_text = tk.Text(log_frame, height=10, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set, state=tk.DISABLED)
        
        # 按钮
        self.export_button = ttk.Button(main_frame, text="开始导出", command=self.start_export, width=15)
        self.export_button.grid(row=6, column=0, padx=5, pady=10)
        
        ttk.Button(main_frame, text="清空日志", command=self.clear_log, width=15).grid(row=6, column=1, padx=5, pady=10)
        
        ttk.Button(main_frame, text="退出", command=self.root.quit, width=15).grid(row=6, column=2, padx=5, pady=10)
        
        # 配置网格权重，使组件能够自适应窗口大小
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
    
    def browse_input_file(self):
        """浏览输入文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("DXF文件", "*.dxf"), ("所有文件", "*.*")],
            title="选择输入DXF文件"
        )
        if file_path:
            self.input_file.set(file_path)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir.set(dir_path)
    
    def log_message(self, message):
        """将消息添加到日志队列，减少UI更新频率"""
        self.log_queue.append(message)
        
        # 如果没有定时器，则启动定时器
        if not self.log_update_timer:
            self.schedule_log_update()
    
    def schedule_log_update(self):
        """安排日志更新"""
        self.log_update_timer = self.root.after(100, self.update_log)
    
    def update_log(self):
        """更新日志显示（批量处理，减少UI更新）"""
        if self.log_queue:
            self.log_text.config(state=tk.NORMAL)
            for message in self.log_queue:
                self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.log_queue.clear()
        self.log_update_timer = None
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log_queue.clear()
    
    def update_progress(self):
        """更新进度条"""
        if self.total_blocks > 0:
            progress = int((self.exported_blocks / self.total_blocks) * 100)
            self.progress_bar['value'] = progress
            self.progress_label.config(text=f"正在导出... {progress}%")
        self.root.update_idletasks()
    
    def start_export(self):
        """开始导出任务"""
        # 验证输入
        if not self.input_file.get():
            messagebox.showwarning("警告", "请选择输入DXF文件")
            return
        
        if not self.output_dir.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("错误", "输入文件不存在")
            return
        
        # 检查是否正在导出
        if self.is_exporting:
            messagebox.showinfo("提示", "导出任务正在进行中")
            return
        
        # 初始化导出状态
        self.is_exporting = True
        self.exported_blocks = 0
        self.total_blocks = 0
        
        self.export_button.config(state=tk.DISABLED)
        self.progress_label.config(text="正在准备...")
        self.progress_bar.grid()  # 显示进度条
        self.progress_bar['value'] = 0
        
        # 清空日志
        self.clear_log()
        self.log_message("开始导出块...")
        self.log_message(f"输入文件: {self.input_file.get()}")
        self.log_message(f"输出目录: {self.output_dir.get()}")
        
        # 启动导出线程
        export_thread = Thread(target=self.export_blocks_thread, 
                              args=(self.input_file.get(), self.output_dir.get()))
        export_thread.daemon = True
        export_thread.start()
    
    def export_blocks_thread(self, input_file, output_dir):
        """导出线程"""
        try:
            # 调用导出函数，传递进度更新回调
            export_blocks(input_file, output_dir, self.log_message, 
                         self.update_block_count)
            
            # 导出完成
            self.root.after(0, self.export_complete)
        except Exception as e:
            # 处理错误
            import traceback
            error_msg = f"导出失败: {str(e)}"
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.log_message(error_msg))
            self.root.after(0, lambda: self.log_message(f"错误详情: {error_detail}"))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            self.root.after(0, self.export_complete)
    
    def update_block_count(self, total, exported):
        """更新块计数"""
        self.total_blocks = total
        self.exported_blocks = exported
        self.root.after(0, self.update_progress)
    
    def export_complete(self):
        """导出完成处理"""
        self.is_exporting = False
        self.export_button.config(state=tk.NORMAL)
        self.progress_bar.grid_remove()  # 隐藏进度条
        self.progress_label.config(text="导出完成")
        self.log_message("导出完成！")
        
        # 确保所有日志都被更新
        if self.log_update_timer:
            self.root.after_cancel(self.log_update_timer)
            self.log_update_timer = None
        self.update_log()
        
        messagebox.showinfo("提示", "块导出完成！")

def export_blocks(input_file, output_dir, log_callback=None, progress_callback=None, reference_file=None):
    """将DXF文件中的块导出为单个文件"""
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log(f"创建输出目录: {output_dir}")
    
    # 如果提供参考文件，先构建参考文本映射（按文本前导数字匹配）
    ref_map = {}
    if reference_file and os.path.exists(reference_file):
        try:
            from cad_reader import CADReader
            reader_ref = CADReader(reference_file)
            if reader_ref.load_file():
                ref_texts = reader_ref.get_text_objects()
                import re
                for t in ref_texts:
                    content = t.get('content')
                    if not content:
                        continue
                    m = re.match(r"^\s*(\d+)", content)
                    if m:
                        ref_map[m.group(1)] = content
        except Exception as e:
            log(f"加载参考文件失败: {e}")

    # 读取输入的DXF文件
    log("读取DXF文件...")
    doc = ezdxf.readfile(input_file)
    
    # 获取所有块定义
    blocks = doc.blocks
    total_blocks = 0
    exported_blocks = 0
    
    # 统计可导出的块数量
    for block in blocks:
        if not block.name.startswith('*'):
            total_blocks += 1
    
    log(f"找到 {total_blocks} 个可导出的块")
    
    # 遍历所有块
    for block in blocks:
        # 跳过匿名块和布局块
        if block.name.startswith('*'):
            continue
        
        exported_blocks += 1
        log(f"导出块 {exported_blocks}/{total_blocks}: {block.name}")
        
        # 更新进度
        if progress_callback:
            progress_callback(total_blocks, exported_blocks)
        
        # 创建新的DXF文档
        new_doc = ezdxf.new(dxfversion=doc.dxfversion)
        new_msp = new_doc.modelspace()
        
        # 复制块内容到新文档
        entity_count = 0
        for entity in block:
            entity_count += 1
            # 获取实体类型
            entity_type = entity.dxftype()
            
            # 获取实体的公共属性
            def get_common_attribs():
                """获取实体的公共属性，如颜色"""
                attribs = {}
                # 复制颜色属性
                if hasattr(entity.dxf, 'color') and entity.dxf.color != 0:
                    attribs['color'] = entity.dxf.color
                # 复制图层属性
                if hasattr(entity.dxf, 'layer'):
                    attribs['layer'] = entity.dxf.layer
                # 复制线型属性
                if hasattr(entity.dxf, 'linetype') and entity.dxf.linetype != 'BYLAYER':
                    attribs['linetype'] = entity.dxf.linetype
                # 复制线宽属性
                if hasattr(entity.dxf, 'lineweight') and entity.dxf.lineweight != -1:
                    attribs['lineweight'] = entity.dxf.lineweight
                return attribs
            
            # 使用适当的方法复制不同类型的实体
            try:
                common_attribs = get_common_attribs()
                
                if entity_type == 'LWPOLYLINE':
                    # 复制多段线
                    points = list(entity.get_points())
                    new_msp.add_lwpolyline(points, close=entity.closed, dxfattribs=common_attribs)
                elif entity_type == 'CIRCLE':
                    # 复制圆形
                    new_msp.add_circle(
                        center=entity.dxf.center,
                        radius=entity.dxf.radius,
                        dxfattribs=common_attribs
                    )
                elif entity_type == 'TEXT':
                    # 复制文本
                    text_attribs = common_attribs.copy()
                    # 添加完整的文本属性，确保位置和对齐方式正确
                    text_attribs.update({
                        'insert': entity.dxf.insert,
                        'height': entity.dxf.height,
                        'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                        'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard',
                        'width': entity.dxf.width if hasattr(entity.dxf, 'width') else 1.0,
                        'oblique': entity.dxf.oblique if hasattr(entity.dxf, 'oblique') else 0.0,
                        'mirror': entity.dxf.mirror if hasattr(entity.dxf, 'mirror') else 0,
                        # TEXT实体支持的对齐属性
                        'attachment_point': entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 0,
                        'align_point': entity.dxf.align_point if hasattr(entity.dxf, 'align_point') else entity.dxf.insert
                    })
                    # 如果参考映射存在且当前文本以数字前缀开头，则使用参考文本为准
                    try:
                        cur_text = entity.dxf.text
                        import re
                        m = re.match(r"^\s*(\d+)", cur_text or '')
                        if m and m.group(1) in ref_map:
                            use_text = ref_map[m.group(1)]
                        else:
                            use_text = cur_text
                        
                        # 将Unicode转义序列转换为对应的 Unicode 字符
                        def _decode_unicode(m):
                            hexstr = m.group(1)
                            try:
                                # 支持4-6位十六进制数
                                cp = int(hexstr, 16)
                                return chr(cp)
                            except Exception:
                                return m.group(0)
                        
                        # 处理多种Unicode转义序列格式
                        use_text = re.sub(r'\\U\+([0-9A-Fa-f]{4,6})', _decode_unicode, use_text)
                        use_text = re.sub(r'\\U([0-9A-Fa-f]{4,6})', _decode_unicode, use_text)
                        use_text = re.sub(r'\\u\+([0-9A-Fa-f]{4})', _decode_unicode, use_text)
                        use_text = re.sub(r'\\u([0-9A-Fa-f]{4})', _decode_unicode, use_text)
                    except Exception:
                        use_text = entity.dxf.text
                    new_msp.add_text(use_text, dxfattribs=text_attribs)
                elif entity_type == 'LINE':
                    # 复制直线
                    new_msp.add_line(
                        start=entity.dxf.start,
                        end=entity.dxf.end,
                        dxfattribs=common_attribs
                    )
                elif entity_type == 'ARC':
                    # 复制圆弧
                    new_msp.add_arc(
                        center=entity.dxf.center,
                        radius=entity.dxf.radius,
                        start_angle=entity.dxf.start_angle,
                        end_angle=entity.dxf.end_angle,
                        dxfattribs=common_attribs
                    )
                elif entity_type == 'INSERT':
                    # 复制块引用
                    insert_attribs = common_attribs.copy()
                    insert_attribs.update({
                        'xscale': entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1,
                        'yscale': entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1,
                        'zscale': entity.dxf.zscale if hasattr(entity.dxf, 'zscale') else 1,
                        'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
                    })
                    new_msp.add_blockref(
                        entity.dxf.name,
                        insert=entity.dxf.insert,
                        dxfattribs=insert_attribs
                    )
                elif entity_type == 'ATTRIB':
                    # 复制属性（属性文本）
                    attrib_attribs = common_attribs.copy()
                    attrib_attribs.update({
                        'insert': entity.dxf.insert,
                        'height': entity.dxf.height,
                        'tag': entity.dxf.tag,
                        'text': entity.dxf.text,
                        'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                        'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard'
                    })
                    # 对于属性，我们可以将其转换为普通文本，或者添加为属性
                    # 这里我们添加为普通文本，确保文本内容可见
                    # 属性文本也尝试使用参考映射替换
                    try:
                        cur_text = entity.dxf.text
                        import re
                        m = re.match(r"^\s*(\d+)", cur_text or '')
                        if m and m.group(1) in ref_map:
                            use_text = ref_map[m.group(1)]
                        else:
                            use_text = cur_text
                    except Exception:
                        use_text = entity.dxf.text
                    new_msp.add_text(use_text, dxfattribs=attrib_attribs)
                elif entity_type == 'SOLID':
                    # 复制实体
                    new_msp.add_solid(
                        points=[entity.dxf.v0, entity.dxf.v1, entity.dxf.v2, entity.dxf.v3],
                        dxfattribs=common_attribs
                    )
                elif entity_type == '3DFACE':
                    # 复制3D面
                    new_msp.add_3dface(
                        points=[entity.dxf.v0, entity.dxf.v1, entity.dxf.v2, entity.dxf.v3],
                        dxfattribs=common_attribs
                    )
                elif entity_type == 'POINT':
                    # 复制点
                    new_msp.add_point(entity.dxf.location, dxfattribs=common_attribs)
                # 新增支持MTEXT（多行文本）
                elif entity_type == 'MTEXT':
                    # 复制多行文本
                    mtext_attribs = common_attribs.copy()
                    # MTEXT使用char_height属性，而不是height属性
                    # MTEXT不支持halign和valign属性，只支持attachment_point和flow_direction
                    mtext_attribs.update({
                        'insert': entity.dxf.insert,
                        'char_height': entity.dxf.char_height if hasattr(entity.dxf, 'char_height') else entity.dxf.height if hasattr(entity.dxf, 'height') else 2.5,
                        'width': entity.dxf.width if hasattr(entity.dxf, 'width') else 0,
                        'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                        'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard',
                        # MTEXT只支持这些对齐属性
                        'attachment_point': entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 1,
                        'flow_direction': entity.dxf.flow_direction if hasattr(entity.dxf, 'flow_direction') else 0
                    })
                    # 将Unicode转义序列转换为对应的 Unicode 字符
                    mtext_content = entity.dxf.text
                    try:
                        import re
                        def _decode_unicode(m):
                            hexstr = m.group(1)
                            try:
                                # 支持4-6位十六进制数
                                cp = int(hexstr, 16)
                                return chr(cp)
                            except Exception:
                                return m.group(0)
                        
                        # 处理多种Unicode转义序列格式
                        mtext_content = re.sub(r'\\U\+([0-9A-Fa-f]{4,6})', _decode_unicode, mtext_content)
                        mtext_content = re.sub(r'\\U([0-9A-Fa-f]{4,6})', _decode_unicode, mtext_content)
                        mtext_content = re.sub(r'\\u\+([0-9A-Fa-f]{4})', _decode_unicode, mtext_content)
                        mtext_content = re.sub(r'\\u([0-9A-Fa-f]{4})', _decode_unicode, mtext_content)
                        
                        # 将多行文本转换为单行文本，替换DXF中的换行符\P和普通换行符
                        mtext_content = re.sub(r'(\\P|\\n|\n|\r\n)', ' ', mtext_content)
                        # 替换连续的空格为单个空格
                        mtext_content = re.sub(r'\s+', ' ', mtext_content)
                        mtext_content = mtext_content.strip()
                    except Exception as e:
                        log(f"  警告: 处理MTEXT文本时出错: {e}")
                        pass
                    new_msp.add_mtext(mtext_content, dxfattribs=mtext_attribs)
                # 新增支持属性定义
                elif entity_type == 'ATTDEF':
                    # 复制属性定义
                    attdef_attribs = common_attribs.copy()
                    attdef_attribs.update({
                        'insert': entity.dxf.insert,
                        'height': entity.dxf.height,
                        'tag': entity.dxf.tag,
                        'prompt': entity.dxf.prompt if hasattr(entity.dxf, 'prompt') else '',
                        'default': entity.dxf.default if hasattr(entity.dxf, 'default') else '',
                        'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                        'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard'
                    })
                    new_msp.add_attdef(**attdef_attribs)
                else:
                    # 其他实体类型，记录警告
                    log(f'警告: 不支持的实体类型 {entity_type}，块 {block.name}')
            except Exception as e:
                # 单个实体处理失败，继续处理下一个实体
                log(f'  警告: 处理实体 {entity_type} 失败: {str(e)}')
                continue
        
        # 保存新文件
        try:
            output_file = os.path.join(output_dir, f'{block.name}.dxf')
            new_doc.saveas(output_file)
            log(f'  包含 {entity_count} 个实体，保存到 {output_file}')
        except Exception as e:
            log(f'  保存文件失败: {str(e)}')
    
    log(f"成功导出 {exported_blocks} 个块")

if __name__ == '__main__':
    # 创建主窗口
    root = tk.Tk()
    
    # 设置窗口图标（如果有的话）
    try:
        # 这里可以添加图标设置
        pass
    except:
        pass
    
    # 创建应用实例
    app = BlockExporterGUI(root)
    
    # 运行主循环
    root.mainloop()