import ezdxf
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
import logging
from cad_reader import CADReader
from cad_block_creator import process_cad_file

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CADToolkitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CAD工具包")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置字体
        self.font = ("微软雅黑", 10)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建三个功能选项卡
        self.create_export_blocks_tab()
        self.create_cad_reader_tab()
        self.create_block_creator_tab()
    
    def create_export_blocks_tab(self):
        """创建块导出选项卡"""
        self.export_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.export_tab, text="块批量导出")
        
        # 初始化块导出变量
        self.export_input_file = tk.StringVar()
        self.export_output_dir = tk.StringVar()
        self.is_exporting = False
        self.total_blocks = 0
        self.exported_blocks = 0
        self.log_queue = []
        self.log_update_timer = None
        
        # 主框架
        main_frame = ttk.Frame(self.export_tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入DXF文件:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.export_input_file, font=self.font, width=50).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.export_browse_input_file, width=10).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出目录选择
        ttk.Label(main_frame, text="输出目录:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.export_output_dir, font=self.font, width=50).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.export_browse_output_dir, width=10).grid(row=1, column=2, padx=5, pady=5)
        
        # 进度条
        self.export_progress_label = ttk.Label(main_frame, text="准备导出...", font=self.font)
        self.export_progress_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.export_progress_bar = ttk.Progressbar(main_frame, mode='determinate', maximum=100)
        self.export_progress_bar.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.export_progress_bar.grid_remove()  # 初始隐藏
        
        # 日志输出
        ttk.Label(main_frame, text="导出日志:", font=self.font).grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        # 日志框架
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        
        self.export_log_text = tk.Text(log_frame, height=15, font=("Consolas", 9))
        self.export_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.export_log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.export_log_text.config(yscrollcommand=scrollbar.set, state=tk.DISABLED)
        
        # 按钮
        self.export_button = ttk.Button(main_frame, text="开始导出", command=self.export_start_export, width=15)
        self.export_button.grid(row=5, column=0, padx=5, pady=10)
        
        ttk.Button(main_frame, text="清空日志", command=self.export_clear_log, width=15).grid(row=5, column=1, padx=5, pady=10)
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
    
    def create_cad_reader_tab(self):
        """创建CAD读取器选项卡"""
        self.reader_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reader_tab, text="CAD文件读取")
        
        # 初始化读取器变量
        self.reader_input_file = tk.StringVar()
        
        # 主框架
        main_frame = ttk.Frame(self.reader_tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入DXF文件:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.reader_input_file, font=self.font, width=50).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.reader_browse_input_file, width=10).grid(row=0, column=2, padx=5, pady=5)
        
        # 分析按钮
        ttk.Button(main_frame, text="分析文件", command=self.reader_analyze_file, width=15).grid(row=1, column=1, padx=5, pady=10)
        
        # 结果框架
        result_frame = ttk.LabelFrame(main_frame, text="文件分析结果", padding="10")
        result_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        
        # 文本对象结果
        text_frame = ttk.LabelFrame(result_frame, text="文本对象", padding="10")
        text_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        self.reader_text_list = tk.Listbox(text_frame, height=10, font=("Consolas", 9))
        self.reader_text_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar1 = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.reader_text_list.yview)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        self.reader_text_list.config(yscrollcommand=scrollbar1.set)
        
        # 几何实体结果
        geom_frame = ttk.LabelFrame(result_frame, text="几何实体统计", padding="10")
        geom_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        self.reader_geom_text = tk.Text(geom_frame, height=10, width=30, font=("Consolas", 9))
        self.reader_geom_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.reader_geom_text.config(state=tk.DISABLED)
        
        scrollbar2 = ttk.Scrollbar(geom_frame, orient=tk.VERTICAL, command=self.reader_geom_text.yview)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.reader_geom_text.config(yscrollcommand=scrollbar2.set)
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(1, weight=1)
    
    def create_block_creator_tab(self):
        """创建块创建器选项卡"""
        self.creator_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.creator_tab, text="CAD块创建")
        
        # 初始化创建器变量
        self.creator_input_file = tk.StringVar()
        self.creator_output_file = tk.StringVar()
        self.creator_output_dir = tk.StringVar()
        self.creator_strategy = tk.StringVar(value="first_valid")
        
        # 主框架
        main_frame = ttk.Frame(self.creator_tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入DXF文件:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.creator_input_file, font=self.font, width=50).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.creator_browse_input_file, width=10).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出文件选择
        ttk.Label(main_frame, text="输出文件:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.creator_output_file, font=self.font, width=50).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.creator_browse_output_file, width=10).grid(row=1, column=2, padx=5, pady=5)
        
        # 输出目录选择
        ttk.Label(main_frame, text="输出目录:", font=self.font).grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        ttk.Entry(main_frame, textvariable=self.creator_output_dir, font=self.font, width=50).grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(main_frame, text="浏览", command=self.creator_browse_output_dir, width=10).grid(row=2, column=2, padx=5, pady=5)
        
        # 文本策略选择
        ttk.Label(main_frame, text="文本策略:", font=self.font).grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        strategy_frame = ttk.Frame(main_frame)
        strategy_frame.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Radiobutton(strategy_frame, text="第一个有效文本", variable=self.creator_strategy, value="first_valid").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(strategy_frame, text="组合所有文本", variable=self.creator_strategy, value="combine").pack(side=tk.LEFT, padx=5)
        
        # 处理按钮
        self.creator_process_button = ttk.Button(main_frame, text="创建块", command=self.creator_process_file, width=15)
        self.creator_process_button.grid(row=4, column=1, padx=5, pady=10)
        
        # 日志输出
        ttk.Label(main_frame, text="处理日志:", font=self.font).grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        
        # 日志框架
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        
        self.creator_log_text = tk.Text(log_frame, height=15, font=("Consolas", 9))
        self.creator_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.creator_log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.creator_log_text.config(yscrollcommand=scrollbar.set, state=tk.DISABLED)
        
        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
    
    # 块导出功能的辅助方法
    def export_browse_input_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("DXF文件", "*.dxf"), ("所有文件", "*.*")],
            title="选择输入DXF文件"
        )
        if file_path:
            self.export_input_file.set(file_path)
    
    def export_browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.export_output_dir.set(dir_path)
    
    def export_log_message(self, message):
        self.log_queue.append(message)
        if not self.log_update_timer:
            self.export_schedule_log_update()
    
    def export_schedule_log_update(self):
        self.log_update_timer = self.root.after(100, self.export_update_log)
    
    def export_update_log(self):
        if self.log_queue:
            self.export_log_text.config(state=tk.NORMAL)
            for message in self.log_queue:
                self.export_log_text.insert(tk.END, message + "\n")
            self.export_log_text.see(tk.END)
            self.export_log_text.config(state=tk.DISABLED)
            self.log_queue.clear()
        self.log_update_timer = None
    
    def export_clear_log(self):
        self.export_log_text.config(state=tk.NORMAL)
        self.export_log_text.delete(1.0, tk.END)
        self.export_log_text.config(state=tk.DISABLED)
        self.log_queue.clear()
    
    def export_update_progress(self):
        if self.total_blocks > 0:
            progress = int((self.exported_blocks / self.total_blocks) * 100)
            self.export_progress_bar['value'] = progress
            self.export_progress_label.config(text=f"正在导出... {progress}%")
        self.root.update_idletasks()
    
    def export_start_export(self):
        # 验证输入
        if not self.export_input_file.get():
            messagebox.showwarning("警告", "请选择输入DXF文件")
            return
        
        if not self.export_output_dir.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        if not os.path.exists(self.export_input_file.get()):
            messagebox.showerror("错误", "输入文件不存在")
            return
        
        if self.is_exporting:
            messagebox.showinfo("提示", "导出任务正在进行中")
            return
        
        # 初始化导出状态
        self.is_exporting = True
        self.exported_blocks = 0
        self.total_blocks = 0
        
        self.export_button.config(state=tk.DISABLED)
        self.export_progress_label.config(text="正在准备...")
        self.export_progress_bar.grid()
        self.export_progress_bar['value'] = 0
        
        # 清空日志
        self.export_clear_log()
        self.export_log_message("开始导出块...")
        self.export_log_message(f"输入文件: {self.export_input_file.get()}")
        self.export_log_message(f"输出目录: {self.export_output_dir.get()}")
        
        # 启动导出线程
        export_thread = Thread(target=self.export_blocks_thread, 
                              args=(self.export_input_file.get(), self.export_output_dir.get()))
        export_thread.daemon = True
        export_thread.start()
    
    def export_blocks_thread(self, input_file, output_dir):
        try:
            # 调用导出函数
            self.export_blocks(input_file, output_dir, self.export_log_message, 
                         self.export_update_block_count)
            
            # 导出完成
            self.root.after(0, self.export_complete)
        except Exception as e:
            import traceback
            error_msg = f"导出失败: {str(e)}"
            error_detail = traceback.format_exc()
            self.root.after(0, lambda: self.export_log_message(error_msg))
            self.root.after(0, lambda: self.export_log_message(f"错误详情: {error_detail}"))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            self.root.after(0, self.export_complete)
    
    def export_update_block_count(self, total, exported):
        self.total_blocks = total
        self.exported_blocks = exported
        self.root.after(0, self.export_update_progress)
    
    def export_complete(self):
        self.is_exporting = False
        self.export_button.config(state=tk.NORMAL)
        self.export_progress_bar.grid_remove()
        self.export_progress_label.config(text="导出完成")
        self.export_log_message("导出完成！")
        
        if self.log_update_timer:
            self.root.after_cancel(self.log_update_timer)
            self.log_update_timer = None
        self.export_update_log()
        
        messagebox.showinfo("提示", "块导出完成！")
    
    def export_blocks(self, input_file, output_dir, log_callback=None, progress_callback=None, reference_file=None):
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
        
        # 如果指定了参考文件（文件A），先构建参考文本映射：
        ref_map = {}
        ref_file = reference_file
        if ref_file and os.path.exists(ref_file):
            try:
                reader_ref = CADReader(ref_file)
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
                        points = list(entity.get_points())
                        new_msp.add_lwpolyline(points, close=entity.closed, dxfattribs=common_attribs)
                    elif entity_type == 'CIRCLE':
                        new_msp.add_circle(
                            center=entity.dxf.center,
                            radius=entity.dxf.radius,
                            dxfattribs=common_attribs
                        )
                    elif entity_type == 'TEXT':
                        text_attribs = common_attribs.copy()
                        text_attribs.update({
                            'insert': entity.dxf.insert,
                            'height': entity.dxf.height,
                            'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                            'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard',
                            'width': entity.dxf.width if hasattr(entity.dxf, 'width') else 1.0,
                            'oblique': entity.dxf.oblique if hasattr(entity.dxf, 'oblique') else 0.0,
                            'mirror': entity.dxf.mirror if hasattr(entity.dxf, 'mirror') else 0,
                            'attachment_point': entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 0,
                            'align_point': entity.dxf.align_point if hasattr(entity.dxf, 'align_point') else entity.dxf.insert
                        })
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
                        new_msp.add_text(use_text, dxfattribs=text_attribs)
                    elif entity_type == 'LINE':
                        new_msp.add_line(
                            start=entity.dxf.start,
                            end=entity.dxf.end,
                            dxfattribs=common_attribs
                        )
                    elif entity_type == 'ARC':
                        new_msp.add_arc(
                            center=entity.dxf.center,
                            radius=entity.dxf.radius,
                            start_angle=entity.dxf.start_angle,
                            end_angle=entity.dxf.end_angle,
                            dxfattribs=common_attribs
                        )
                    elif entity_type == 'INSERT':
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
                        attrib_attribs = common_attribs.copy()
                        attrib_attribs.update({
                            'insert': entity.dxf.insert,
                            'height': entity.dxf.height,
                            'tag': entity.dxf.tag,
                            'text': entity.dxf.text,
                            'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                            'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard'
                        })
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
                        new_msp.add_solid(
                            points=[entity.dxf.v0, entity.dxf.v1, entity.dxf.v2, entity.dxf.v3],
                            dxfattribs=common_attribs
                        )
                    elif entity_type == '3DFACE':
                        new_msp.add_3dface(
                            points=[entity.dxf.v0, entity.dxf.v1, entity.dxf.v2, entity.dxf.v3],
                            dxfattribs=common_attribs
                        )
                    elif entity_type == 'POINT':
                        new_msp.add_point(entity.dxf.location, dxfattribs=common_attribs)
                    elif entity_type == 'MTEXT':
                        mtext_attribs = common_attribs.copy()
                        mtext_attribs.update({
                            'insert': entity.dxf.insert,
                            'char_height': entity.dxf.char_height if hasattr(entity.dxf, 'char_height') else entity.dxf.height if hasattr(entity.dxf, 'height') else 2.5,
                            'width': entity.dxf.width if hasattr(entity.dxf, 'width') else 0,
                            'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                            'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard',
                            'attachment_point': entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 1,
                            'flow_direction': entity.dxf.flow_direction if hasattr(entity.dxf, 'flow_direction') else 0
                        })
                        new_msp.add_mtext(entity.dxf.text, dxfattribs=mtext_attribs)
                    elif entity_type == 'ATTDEF':
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
                        log(f'警告: 不支持的实体类型 {entity_type}，块 {block.name}')
                except Exception as e:
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
    
    # CAD读取器功能的辅助方法
    def reader_browse_input_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("DXF文件", "*.dxf"), ("所有文件", "*.*")],
            title="选择输入DXF文件"
        )
        if file_path:
            self.reader_input_file.set(file_path)
    
    def reader_analyze_file(self):
        input_file = self.reader_input_file.get()
        if not input_file:
            messagebox.showwarning("警告", "请选择输入DXF文件")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("错误", "输入文件不存在")
            return
        
        # 清空之前的结果
        self.reader_text_list.delete(0, tk.END)
        self.reader_geom_text.config(state=tk.NORMAL)
        self.reader_geom_text.delete(1.0, tk.END)
        self.reader_geom_text.config(state=tk.DISABLED)
        
        try:
            # 创建CADReader实例并分析文件
            cad_reader = CADReader(input_file)
            
            if not cad_reader.load_file():
                messagebox.showerror("错误", "无法加载CAD文件")
                return
            
            # 获取文本对象
            text_objects = cad_reader.get_text_objects()
            
            # 显示文本对象
            if text_objects:
                for i, text_obj in enumerate(text_objects):
                    self.reader_text_list.insert(tk.END, f"{i+1}. {text_obj['content']} (位置: {text_obj['position']})")
            else:
                self.reader_text_list.insert(tk.END, "未找到文本对象")
            
            # 获取几何实体
            geom_entities = cad_reader.get_geometric_entities()
            
            # 显示几何实体统计
            self.reader_geom_text.config(state=tk.NORMAL)
            self.reader_geom_text.insert(tk.END, f"找到 {len(geom_entities)} 个几何实体\n\n")
            
            # 统计实体类型
            entity_counts = {}
            for entity in geom_entities:
                entity_type = entity.dxftype()
                if entity_type in entity_counts:
                    entity_counts[entity_type] += 1
                else:
                    entity_counts[entity_type] = 1
            
            for entity_type, count in entity_counts.items():
                self.reader_geom_text.insert(tk.END, f"{entity_type}: {count} 个\n")
            
            self.reader_geom_text.config(state=tk.DISABLED)
            
            messagebox.showinfo("提示", "文件分析完成！")
        except Exception as e:
            messagebox.showerror("错误", f"分析文件时出错: {str(e)}")
    
    # CAD块创建功能的辅助方法
    def creator_browse_input_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("DXF文件", "*.dxf"), ("所有文件", "*.*")],
            title="选择输入DXF文件"
        )
        if file_path:
            self.creator_input_file.set(file_path)
            # 自动填充输出文件名建议
            base_name, ext = os.path.splitext(file_path)
            self.creator_output_file.set(f"{base_name}_block{ext}")
            # 自动填充输出目录
            self.creator_output_dir.set(os.path.dirname(file_path))
    
    def creator_browse_output_file(self):
        file_path = filedialog.asksaveasfilename(
            filetypes=[("DXF文件", "*.dxf"), ("所有文件", "*.*")],
            title="选择输出文件"
        )
        if file_path:
            self.creator_output_file.set(file_path)
    
    def creator_browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.creator_output_dir.set(dir_path)
    
    def creator_log_message(self, message):
        self.creator_log_text.config(state=tk.NORMAL)
        self.creator_log_text.insert(tk.END, message + "\n")
        self.creator_log_text.see(tk.END)
        self.creator_log_text.config(state=tk.DISABLED)
    
    def creator_process_file(self):
        input_file = self.creator_input_file.get()
        output_file = self.creator_output_file.get()
        output_dir = self.creator_output_dir.get()
        text_strategy = self.creator_strategy.get()
        
        # 验证输入
        if not input_file:
            messagebox.showwarning("警告", "请选择输入DXF文件")
            return
        
        if not output_file:
            messagebox.showwarning("警告", "请选择输出文件")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("错误", "输入文件不存在")
            return
        
        # 清空日志
        self.creator_log_text.config(state=tk.NORMAL)
        self.creator_log_text.delete(1.0, tk.END)
        self.creator_log_text.config(state=tk.DISABLED)
        
        # 记录处理信息
        self.creator_log_message("=== CAD块创建工具 ===")
        self.creator_log_message(f"输入文件: {input_file}")
        self.creator_log_message(f"输出文件: {output_file}")
        self.creator_log_message(f"输出目录: {output_dir}")
        self.creator_log_message(f"文本策略: {text_strategy}")
        self.creator_log_message("\n开始处理...")
        
        # 启动处理线程
        process_thread = Thread(target=self.creator_process_thread, 
                              args=(input_file, output_file, text_strategy, output_dir))
        process_thread.daemon = True
        process_thread.start()
    
    def creator_process_thread(self, input_file, output_file, text_strategy, output_dir):
        try:
            # 调用处理函数
            success = process_cad_file(input_file, output_file, text_strategy, output_dir)
            
            if success:
                self.root.after(0, lambda: self.creator_log_message("\n✅ 处理成功！"))
                self.root.after(0, lambda: messagebox.showinfo("提示", "块创建完成！"))
            else:
                self.root.after(0, lambda: self.creator_log_message("\n❌ 处理失败！"))
                self.root.after(0, lambda: messagebox.showerror("错误", "块创建失败！"))
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            self.root.after(0, lambda: self.creator_log_message(f"\n❌ {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

if __name__ == '__main__':
    # 创建主窗口
    root = tk.Tk()
    
    # 创建应用实例
    app = CADToolkitGUI(root)
    
    # 运行主循环
    root.mainloop()
