import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import openpyxl  # 用于处理Excel文件

def process_excel(file_path):
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 确保必要的列存在
        required_columns = ['序号', '数量', '总数量']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Excel文件缺少必要的列: {', '.join(missing_cols)}")
        
        # 创建一个字典来存储每个序号的总数量
        total_quantities = {}
        errors = []

        # 辅助函数：校验序号格式与父链完整性
        def validate_sequence_ids(id_pairs):
            """检查序号格式、父链完整性与行内层级顺序，返回错误/警告信息列表。
            规则：
            - 每个段应为数字（如 16 或 2），不允许空段或非数字段
            - 检测重复序号并记录警告
            - 父级必须存在于整个表中（存在性检查）
            - 父级若出现在子级之后或已被‘关闭’（即层级已切换到其他分支后又重现），则记录为不合逻辑的顺序警告
            """
            msgs = []
            # id_pairs 是 (row_index, raw_sid) 的列表
            id_set = set([sid for _, sid in id_pairs])
            seen = {}

            # 维护上一行的分段列表，用于检测层级何时被关闭
            prev_parts = []
            # 已关闭的前缀集合；一旦某个前缀的分支结束（切换到别的分支），它被标记为已关闭
            closed_prefixes = set()

            # 记录每个父级下最后看到的子序号数字，用于检测同级序号的单调性（同父级下序号应呈上升趋势）
            last_seen = {}

            for _, pair in enumerate(id_pairs):
                row_idx, raw_sid = pair
                sid = raw_sid if isinstance(raw_sid, str) else str(raw_sid)
                if sid is None or sid.strip() == '':
                    msgs.append(f"行{row_idx+2}: 序号 '{sid}' - 序号为空或格式不正确")
                    continue
                sid = sid.strip()

                # 重复检查
                if sid in seen:
                    prev_row = seen[sid]
                    msgs.append(f"行{row_idx+2}: 序号 '{sid}' - 重复，之前在行{prev_row+2}出现")
                else:
                    seen[sid] = row_idx

                # 格式检查：段必须为纯数字
                parts = sid.split('.')
                bad_part = False
                for p in parts:
                    if p == '' or not p.isdigit():
                        msgs.append(f"行{row_idx+2}: 序号 '{sid}' 包含非法段: '{p}'")
                        bad_part = True
                        break
                if bad_part:
                    # 不再进行后续的层级/父链检查
                    prev_parts = parts
                    continue

                # 父级存在性检查（全表范围）
                if len(parts) > 1:
                    # 生成逐级父级，例如 16.2.3 -> ['16.2','16']
                    for i in range(1, len(parts)):
                        parent = '.'.join(parts[:len(parts)-i])
                        if parent not in id_set:
                            msgs.append(f"行{row_idx+2}: 序号 '{sid}' 的父级序号 '{parent}' 缺失或未定义")

                # 层级顺序检测：如果当前序号的任意父前缀之前已被标为 closed，则说明父级被关闭后又出现子项——这是不合逻辑的
                for i in range(1, len(parts)):
                    prefix = '.'.join(parts[:i])
                    if prefix in closed_prefixes:
                        msgs.append(f"行{row_idx+2}: 序号 '{sid}' - 父级 '{prefix}' 在之前已结束，当前出现子级属于不合逻辑的顺序")

                # 同级顺序检测：在同一父级下，子序号应大致呈非下降趋势（如果出现比之前的小的同级序号，往往表示顺序异常）
                try:
                    parent_key = '.'.join(parts[:-1]) if len(parts) > 1 else ''
                    child_index = int(parts[-1])
                    if parent_key in last_seen and child_index < last_seen[parent_key]:
                        display_parent = parent_key if parent_key != '' else '顶级'
                        msgs.append(f"行{row_idx+2}: 序号 '{sid}' - 在父级 '{display_parent}' 下的顺序异常：之前出现同级序号 {last_seen[parent_key]}，现在出现较小的同级序号 {child_index}")
                    # 更新最后看到的子序号
                    last_seen[parent_key] = child_index
                except ValueError:
                    # 如果子段无法转换为整数（格式问题），已在前面对段格式进行了报错，这里忽略
                    pass

                # 更新 closed_prefixes：比较 prev_parts 与 当前 parts，较深的 prev_parts 分支在 lcp 之后都会被关闭
                # 计算最长公共前缀长度
                lcp = 0
                for a, b in zip(prev_parts, parts):
                    if a == b:
                        lcp += 1
                    else:
                        break
                # prev_parts 中在 lcp 之后的每一层其前缀都被关闭
                for j in range(len(prev_parts), lcp, -1):
                    prefix_closed = '.'.join(prev_parts[:j])
                    if prefix_closed:
                        closed_prefixes.add(prefix_closed)

                prev_parts = parts

            return msgs
        
        # 确保序号列为字符串类型
        df['序号'] = df['序号'].astype(str).str.strip()

        # 在处理前先做一次全局的序号格式与父链校验（包括行号信息，方便定位）
        sequence_pairs = list(zip(df.index.tolist(), df['序号'].tolist()))
        seq_warnings = validate_sequence_ids(sequence_pairs)
        errors.extend(seq_warnings)
        
        # 处理所有行，确保顶级项目有总数量
        for index, row in df.iterrows():
            current_id = str(row['序号']).strip()
            
            # 尝试处理数量值
            try:
                # 如果总数量不为空，使用它
                if pd.notna(row['总数量']):
                    total_quantities[current_id] = float(row['总数量'])
                # 否则如果是顶级项目，使用数量作为总数量
                elif '.' not in current_id:
                    quantity = float(row['数量'])
                    total_quantities[current_id] = quantity
            except (ValueError, TypeError) as e:
                errors.append(f"第{index+2}行数据格式错误: {str(e)}")
        
        # 再次循环处理子项目，按层级顺序处理
        # 先处理层级较浅的项目
        rows_with_level = []
        for index, row in df.iterrows():
            current_id = str(row['序号']).strip()
            level = current_id.count('.')
            rows_with_level.append((index, current_id, level))
        
        # 按层级升序排序
        rows_with_level.sort(key=lambda x: x[2])
        
        # 处理每个行，按层级顺序
        for index, current_id, level in rows_with_level:
            # 对所有有层级的项目，都检查父级是否存在（即使该行已填写总数量，也应警告父级缺失）
            if level > 0:
                parent_id = '.'.join(current_id.split('.')[:-1])
                # 尝试读取数量（但不强制必须有数量）
                try:
                    quantity = float(df.at[index, '数量']) if pd.notna(df.at[index, '数量']) else None
                except (ValueError, TypeError) as e:
                    errors.append(f"序号 {current_id} 的数量格式错误: {str(e)}")
                    quantity = None

                # 若父级没有计算到 total_quantities，记录错误（但继续处理，尽量回退）
                if parent_id not in total_quantities:
                    errors.append(f"序号 {current_id} 的父级序号 {parent_id} 没有有效的总数量")

                # 如果该行没有总数量，尝试基于父级计算或使用数量本身
                if pd.isna(df.at[index, '总数量']):
                    if parent_id in total_quantities and quantity is not None:
                        total_quantities[current_id] = quantity * total_quantities[parent_id]
                    else:
                        # 无法基于父级计算，回退为使用数量（或0 如果数量为空）
                        total_quantities[current_id] = quantity if quantity is not None else 0
                else:
                    # 如果用户填写了总数量，仍然使用该值，但如果父级缺失会有警告
                    try:
                        total_quantities[current_id] = float(df.at[index, '总数量'])
                    except (ValueError, TypeError) as e:
                        errors.append(f"序号 {current_id} 的总数量格式错误: {str(e)}")
                        # 回退为基于父级或数量的近似
                        if parent_id in total_quantities and quantity is not None:
                            total_quantities[current_id] = quantity * total_quantities[parent_id]
                        else:
                            total_quantities[current_id] = quantity if quantity is not None else 0
        
        # 更新DataFrame中的总数量列
        for index, row in df.iterrows():
            current_id = str(row['序号']).strip()
            if current_id in total_quantities:
                df.at[index, '总数量'] = total_quantities[current_id]
        
        # 保存结果到新的Excel文件
        output_file = 'processed_' + os.path.basename(file_path)
        output_path = os.path.join(os.path.dirname(file_path), output_file)
        df.to_excel(output_path, index=False)
        
        # 如果有错误，将它们添加到结果消息中（显示全部警告）
        result_msg = output_path
        if errors:
            result_msg += "\n警告信息:\n" + "\n".join(errors)
        
        return True, result_msg
    except Exception as e:
        return False, str(e)

class ExcelProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BOM数量计算器")
        self.root.geometry("600x300")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 文件选择部分
        ttk.Label(main_frame, text="选择Excel文件：").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.file_path, width=60).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Button(main_frame, text="浏览", command=self.browse_file).grid(row=1, column=1, padx=5)
        
        # 处理按钮
        ttk.Button(main_frame, text="开始处理", command=self.process_file).grid(row=2, column=0, columnspan=2, pady=20)
        
        # 状态标签
        self.status_label = ttk.Label(main_frame, text="", wraplength=550)
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, length=550, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=2, pady=5)
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls")]
        )
        if filename:
            self.file_path.set(filename)

    def copy_to_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("复制", "已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {e}")

    def save_warnings_to_file(self, text):
        fn = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt"),("All files","*.*")])
        if fn:
            try:
                with open(fn, 'w', encoding='utf-8') as f:
                    f.write(text)
                messagebox.showinfo("保存", f"已保存到 {fn}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")

    def show_warnings(self, text):
        win = tk.Toplevel(self.root)
        win.title("警告信息")
        win.geometry("800x500")
        frame = ttk.Frame(win, padding=4)
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        win.grid_rowconfigure(0, weight=1)
        win.grid_columnconfigure(0, weight=1)

        txt = tk.Text(frame, wrap='none')
        vsb = ttk.Scrollbar(frame, orient='vertical', command=txt.yview)
        hsb = ttk.Scrollbar(frame, orient='horizontal', command=txt.xview)
        txt.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        txt.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        txt.insert('1.0', text)

        btn_frame = ttk.Frame(win)
        btn_frame.grid(row=1, column=0, sticky='ew', padx=6, pady=6)
        ttk.Button(btn_frame, text="复制到剪贴板", command=lambda: self.copy_to_clipboard(text)).pack(side='left', padx=6)
        ttk.Button(btn_frame, text="保存到文件", command=lambda: self.save_warnings_to_file(text)).pack(side='left', padx=6)
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side='right', padx=6)
    
    def process_file(self):
        file_path = self.file_path.get()
        if not file_path:
            messagebox.showerror("错误", "请先选择Excel文件")
            return
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return
            
        # 检查文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.xlsx', '.xls']:
            messagebox.showerror("错误", "请选择有效的Excel文件 (.xlsx 或 .xls)")
            return
        
        self.progress['value'] = 10
        self.status_label.config(text="正在处理...")
        self.root.update()
        
        try:
            # 分阶段更新进度条
            self.progress['value'] = 30
            self.root.update()
            
            success, result = process_excel(file_path)
            
            self.progress['value'] = 70
            self.root.update()
            
            if success:
                self.progress['value'] = 100
                self.status_label.config(text=f"处理完成！结果已保存。")
                # 对于长消息，分开发送
                if '\n警告信息:' in result:
                    output_path = result.split('\n警告信息:')[0]
                    messagebox.showinfo("成功", f"处理完成！\n结果已保存到：\n{output_path}")
                    # 如果有警告，可以选择是否显示
                    if messagebox.askyesno("警告信息", "处理过程中有一些警告，是否查看？"):
                        warning_text = result.split('\n警告信息:')[1]
                        self.show_warnings(warning_text)
                else:
                    messagebox.showinfo("成功", f"处理完成！\n结果已保存到：\n{result}")
            else:
                self.progress['value'] = 0
                self.status_label.config(text=f"处理失败")
                messagebox.showerror("错误", f"处理失败：{result}")
        except Exception as e:
            self.progress['value'] = 0
            self.status_label.config(text=f"处理过程中发生错误")
            messagebox.showerror("错误", f"处理过程中发生错误：{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelProcessorApp(root)
    root.mainloop() 