import sys
import os
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, 
    QComboBox, QMessageBox, QProgressBar, QGroupBox, QFormLayout, 
    QStatusBar, QCheckBox, QTabWidget, QTreeWidget, QTreeWidgetItem, 
    QSplitter, QTextBrowser, QListWidget, QMenuBar, QAction, QSpinBox, QDoubleSpinBox,
    QGridLayout, QStackedWidget, QDialog, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QIcon, QTextCursor

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 仅在开发环境（虚拟环境存在时）添加虚拟环境路径
try:
    # 尝试新创建的虚拟环境
    venv_site_packages = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new_venv', 'Lib', 'site-packages')
    if not os.path.exists(venv_site_packages):
        # 尝试旧的虚拟环境
        venv_site_packages = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Lib', 'site-packages')
    
    if os.path.exists(venv_site_packages):
        sys.path.append(venv_site_packages)
        # 尝试设置Qt平台插件路径
        qt_plugins_path = os.path.join(venv_site_packages, 'PyQt5', 'Qt5', 'plugins')
        if os.path.exists(qt_plugins_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugins_path
            print(f"已设置Qt平台插件路径: {qt_plugins_path}")
        else:
            print(f"未找到Qt平台插件路径: {qt_plugins_path}")
except Exception as e:
    print(f"设置环境路径时出错: {e}")

# 导入各个功能模块
# 注意：为减少程序启动时的导入开销，下面几个大型/延迟使用的库不在模块顶层导入，
# 而是在需要时局部导入（例如在线程的 run/process 方法中）。

# 导入消息推送和更新系统
try:
    from notification_system import NotificationManager, NotificationWidget, NotificationFetcher
    from update_system import UpdateChecker, UpdateDialog
    from system_config import NOTIFICATION_CONFIG, UPDATE_CONFIG, APP_VERSION
    NOTIFICATION_ENABLED = True
except ImportError as e:
    print(f"消息推送和更新系统未安装: {e}")
    NOTIFICATION_ENABLED = False
    APP_VERSION = "3.8"

def _find_local_exe(filename):
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, filename),
        os.path.join(os.getcwd(), filename),
    ]
    meipass = getattr(sys, '_MEIPASS', '')
    if meipass:
        candidates.insert(1, os.path.join(meipass, filename))
    for p in candidates:
        try:
            if p and os.path.exists(p):
                return p
        except Exception:
            continue
    return ""

class ExcelWorker(QThread):
    """Excel处理线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            self.progress.emit(10)
            self.log.emit("开始处理Excel文件...")
            
            # 调用处理函数
            success, result = self.process_excel(self.file_path)
            
            self.progress.emit(100)
            self.finished.emit(success, result)
        except Exception as e:
            self.log.emit(f"处理失败: {str(e)}")
            self.finished.emit(False, str(e))
    
    def process_excel(self, file_path):
        """处理Excel文件"""
        # 延迟导入，避免程序启动时就加载大型库（如 pandas）
        import pandas as pd
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
                """检查序号格式、父链完整性与行内层级顺序，返回错误/警告信息列表。"""
                msgs = []
                # id_pairs 是 (row_index, raw_sid) 的列表
                id_set = set([sid for _, sid in id_pairs])
                seen = {}

                # 维护上一行的分段列表，用于检测层级何时被关闭
                prev_parts = []
                # 已关闭的前缀集合；一旦某个前缀的分支结束（切换到别的分支），它被标记为已关闭
                closed_prefixes = set()

                # 记录每个父级下最后看到的子序号数字，用于检测同级序号的单调性
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
                        prev_parts = parts
                        continue

                    # 父级存在性检查（全表范围）
                    if len(parts) > 1:
                        # 生成逐级父级，例如 16.2.3 -> ['16.2','16']
                        for i in range(1, len(parts)):
                            parent = '.'.join(parts[:len(parts)-i])
                            if parent not in id_set:
                                msgs.append(f"行{row_idx+2}: 序号 '{sid}' 的父级序号 '{parent}' 缺失或未定义")

                    # 层级顺序检测
                    for i in range(1, len(parts)):
                        prefix = '.'.join(parts[:i])
                        if prefix in closed_prefixes:
                            msgs.append(f"行{row_idx+2}: 序号 '{sid}' - 父级 '{prefix}' 在之前已结束，当前出现子级属于不合逻辑的顺序")

                    # 同级顺序检测
                    try:
                        parent_key = '.'.join(parts[:-1]) if len(parts) > 1 else ''
                        child_index = int(parts[-1])
                        if parent_key in last_seen and child_index < last_seen[parent_key]:
                            display_parent = parent_key if parent_key != '' else '顶级'
                            msgs.append(f"行{row_idx+2}: 序号 '{sid}' - 在父级 '{display_parent}' 下的顺序异常：之前出现同级序号 {last_seen[parent_key]}，现在出现较小的同级序号 {child_index}")
                        # 更新最后看到的子序号
                        last_seen[parent_key] = child_index
                    except ValueError:
                        pass

                    # 更新 closed_prefixes
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

            # 在处理前先做一次全局的序号格式与父链校验
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
            rows_with_level = []
            for index, row in df.iterrows():
                current_id = str(row['序号']).strip()

# Removed misplaced code

                level = current_id.count('.')
                rows_with_level.append((index, current_id, level))
            
            # 按层级升序排序
            rows_with_level.sort(key=lambda x: x[2])
            
            # 处理每个行，按层级顺序
            for index, current_id, level in rows_with_level:
                # 对所有有层级的项目，都检查父级是否存在
                if level > 0:
                    parent_id = '.'.join(current_id.split('.')[:-1])
                    # 尝试读取数量（但不强制必须有数量）
                    try:
                        quantity = float(df.at[index, '数量']) if pd.notna(df.at[index, '数量']) else None
                    except (ValueError, TypeError) as e:
                        errors.append(f"序号 {current_id} 的数量格式错误: {str(e)}")
                        quantity = None

                    # 若父级没有计算到 total_quantities，记录错误
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
            
            # 如果有错误，将它们添加到结果消息中
            result_msg = output_path
            if errors:
                result_msg += "\n警告信息:\n" + "\n".join(errors)
            
            return True, result_msg
        except Exception as e:
            return False, str(e)

class ExportBlocksWorker(QThread):
    """块导出线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    block_count = pyqtSignal(int, int)
    
    def __init__(self, input_file, output_dir, reference_file=None):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        # 可选参考文件（用作文本来源的文件A）
        self.reference_file = reference_file
    
    def run(self):
        try:
            self.export_blocks(self.input_file, self.output_dir, reference_file=self.reference_file)
            self.finished.emit(True, "导出完成")
        except Exception as e:
            self.progress.emit(f"导出失败: {str(e)}")
            self.finished.emit(False, str(e))
    
    def export_blocks(self, input_file, output_dir, log_callback=None, progress_callback=None, reference_file=None):
        """将DXF文件中的块导出为单个文件"""
        # 延迟导入 ezdxf，避免应用程序主窗口启动时加载它
        import ezdxf
        from ezdxf.math import Matrix44
        import math
        def log(msg):
            if log_callback:
                log_callback(msg)
            else:
                self.progress.emit(msg)
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            log(f"创建输出目录: {output_dir}")
        
        # 导入TextProcessor用于处理文本
        try:
            from text_processor import TextProcessor
            text_processor = TextProcessor()
        except Exception as e:
            log(f"加载TextProcessor失败: {e}")
            text_processor = None
        
        # 如果指定了参考文件（文件A），先构建参考文本映射：
        ref_map = {}
        ref_file = reference_file if reference_file is not None else self.reference_file
        if ref_file and os.path.exists(ref_file):
            try:
                from cad_reader import CADReader
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
                            key = m.group(1)
                            ref_map[key] = content
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
            else:
                self.block_count.emit(total_blocks, exported_blocks)
            
            # 创建新的DXF文档
            new_doc = ezdxf.new(dxfversion=doc.dxfversion)
            new_msp = new_doc.modelspace()
            base = getattr(block.dxf, 'base_point', (0, 0, 0))
            bx, by = base[0], base[1]
            
            # 收集块中的文本内容
            block_texts = []
            
            # 复制块内容到新文档
            entity_count = 0
            for entity in block:
                entity_count += 1
                # 获取实体类型
                entity_type = entity.dxftype()
                
                # 收集文本内容
                if entity_type in ['TEXT', 'MTEXT', 'ATTRIB']:
                    try:
                        if entity_type == 'TEXT':
                            text_content = entity.dxf.text
                        elif entity_type == 'MTEXT':
                            text_content = entity.dxf.text
                        elif entity_type == 'ATTRIB':
                            text_content = entity.dxf.text
                        
                        if text_content:
                            block_texts.append({'content': text_content, 'type': entity_type})
                    except Exception:
                        pass
                
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
                        pts = []
                        for p in list(entity.get_points()):
                            if isinstance(p, tuple):
                                if len(p) >= 2:
                                    pts.append((p[0] - bx, p[1] - by) + p[2:])
                                else:
                                    pts.append(p)
                            else:
                                pts.append(p)
                        new_msp.add_lwpolyline(pts, close=entity.closed, dxfattribs=common_attribs)
                    elif entity_type == 'CIRCLE':
                        cx, cy = entity.dxf.center[0] - bx, entity.dxf.center[1] - by
                        new_msp.add_circle((cx, cy), entity.dxf.radius, dxfattribs=common_attribs)
                    elif entity_type == 'TEXT':
                        text_attribs = common_attribs.copy()
                        text_attribs.update({
                            'insert': (entity.dxf.insert[0] - bx, entity.dxf.insert[1] - by),
                            'height': entity.dxf.height,
                            'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                            'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard',
                            'width': entity.dxf.width if hasattr(entity.dxf, 'width') else 1.0,
                            'oblique': entity.dxf.oblique if hasattr(entity.dxf, 'oblique') else 0.0,
                            'mirror': entity.dxf.mirror if hasattr(entity.dxf, 'mirror') else 0,
                            'attachment_point': entity.dxf.attachment_point if hasattr(entity.dxf, 'attachment_point') else 0,
                            'align_point': (entity.dxf.align_point[0] - bx, entity.dxf.align_point[1] - by) if hasattr(entity.dxf, 'align_point') else (entity.dxf.insert[0] - bx, entity.dxf.insert[1] - by)
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
                        except Exception:
                            use_text = entity.dxf.text
                        new_msp.add_text(use_text, dxfattribs=text_attribs)
                    elif entity_type == 'LINE':
                        sx, sy = entity.dxf.start[0] - bx, entity.dxf.start[1] - by
                        ex, ey = entity.dxf.end[0] - bx, entity.dxf.end[1] - by
                        new_msp.add_line((sx, sy), (ex, ey), dxfattribs=common_attribs)
                    elif entity_type == 'ARC':
                        cx, cy = entity.dxf.center[0] - bx, entity.dxf.center[1] - by
                        new_msp.add_arc((cx, cy), entity.dxf.radius, entity.dxf.start_angle, entity.dxf.end_angle, dxfattribs=common_attribs)
                    elif entity_type == 'INSERT':
                        try:
                            ref_name = entity.dxf.name
                            if ref_name in doc.blocks:
                                ref_block = doc.blocks.get(ref_name)
                                tx = entity.dxf.insert[0] - bx
                                ty = entity.dxf.insert[1] - by
                                sx = entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1.0
                                sy = entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1.0
                                rz = math.radians(entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0)
                                m = Matrix44.scale(sx, sy, 1.0) @ Matrix44.z_rotate(rz) @ Matrix44.translate(tx, ty, 0)
                                for sub in ref_block:
                                    try:
                                        cp = sub.copy()
                                        cp.transform(m)
                                        new_msp.add_entity(cp)
                                    except Exception:
                                        continue
                            else:
                                cp = entity.copy()
                                cp.transform(Matrix44.translate(-bx, -by, 0))
                                new_msp.add_entity(cp)
                        except Exception:
                            cp = entity.copy()
                            try:
                                cp.transform(Matrix44.translate(-bx, -by, 0))
                            except Exception:
                                pass
                            new_msp.add_entity(cp)
                    elif entity_type == 'ATTRIB':
                        attrib_attribs = common_attribs.copy()
                        attrib_attribs.update({
                            'insert': (entity.dxf.insert[0] - bx, entity.dxf.insert[1] - by),
                            'height': entity.dxf.height,
                            'tag': entity.dxf.tag,
                            'text': entity.dxf.text,
                            'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                            'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard'
                        })
                        new_msp.add_text(entity.dxf.text, dxfattribs=attrib_attribs)
                    elif entity_type == 'SOLID':
                        v0 = (entity.dxf.v0[0] - bx, entity.dxf.v0[1] - by)
                        v1 = (entity.dxf.v1[0] - bx, entity.dxf.v1[1] - by)
                        v2 = (entity.dxf.v2[0] - bx, entity.dxf.v2[1] - by)
                        v3 = (entity.dxf.v3[0] - bx, entity.dxf.v3[1] - by)
                        new_msp.add_solid([v0, v1, v2, v3], dxfattribs=common_attribs)
                    elif entity_type == '3DFACE':
                        v0 = (entity.dxf.v0[0] - bx, entity.dxf.v0[1] - by)
                        v1 = (entity.dxf.v1[0] - bx, entity.dxf.v1[1] - by)
                        v2 = (entity.dxf.v2[0] - bx, entity.dxf.v2[1] - by)
                        v3 = (entity.dxf.v3[0] - bx, entity.dxf.v3[1] - by)
                        new_msp.add_3dface([v0, v1, v2, v3], dxfattribs=common_attribs)
                    elif entity_type == 'POINT':
                        px, py = entity.dxf.location[0] - bx, entity.dxf.location[1] - by
                        new_msp.add_point((px, py), dxfattribs=common_attribs)
                    elif entity_type == 'MTEXT':
                        mtext_attribs = common_attribs.copy()
                        mtext_attribs.update({
                            'insert': (entity.dxf.insert[0] - bx, entity.dxf.insert[1] - by),
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
                            'insert': (entity.dxf.insert[0] - bx, entity.dxf.insert[1] - by),
                            'height': entity.dxf.height if hasattr(entity.dxf, 'height') else 2.5,
                            'tag': entity.dxf.tag,
                            'prompt': entity.dxf.prompt if hasattr(entity.dxf, 'prompt') else '',
                            'default': entity.dxf.default if hasattr(entity.dxf, 'default') else '',
                            'rotation': entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0,
                            'style': entity.dxf.style if hasattr(entity.dxf, 'style') else 'Standard'
                        })
                        new_msp.add_attdef(**attdef_attribs)
                    else:
                        try:
                            cp = entity.copy()
                            cp.transform(Matrix44.translate(-bx, -by, 0))
                            new_msp.add_entity(cp)
                        except Exception:
                            log(f'警告: 不支持的实体类型 {entity_type}，块 {block.name}')
                except Exception as e:
                    log(f'  警告: 处理实体 {entity_type} 失败: {str(e)}')
                    continue
            
            # 生成更准确的块名称
            final_block_name = block.name
            if text_processor and block_texts:
                try:
                    # 使用combine策略，组合所有文本
                    generated_name = text_processor.generate_block_name_from_texts(block_texts, 'combine')
                    if generated_name and generated_name != 'Block':
                        final_block_name = generated_name
                        log(f'  从块内容生成新名称: {final_block_name}')
                except Exception as e:
                    log(f'  生成块名称时出错: {e}')
            
            # 保存新文件
            try:
                output_file = os.path.join(output_dir, f'{final_block_name}.dxf')
                new_doc.saveas(output_file)
                log(f'  包含 {entity_count} 个实体，保存到 {output_file}')
            except Exception as e:
                log(f'  保存文件失败: {str(e)}')
        
        log(f"成功导出 {exported_blocks} 个块")

class BlockCreatorWorker(QThread):
    """块创建线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, block_creator, input_files, output_dir, strategy, clear_existing_blocks, excel_file=None, write_material_thickness_attrib=True, write_id_drawing_name_attrib=True):
        super().__init__()
        self.block_creator = block_creator
        self.input_files = input_files
        self.output_dir = output_dir
        self.strategy = strategy
        self.clear_existing_blocks = clear_existing_blocks
        self.excel_file = excel_file
        self.write_material_thickness_attrib = write_material_thickness_attrib
        self.write_id_drawing_name_attrib = write_id_drawing_name_attrib
    
    def run(self):
        try:
            self.progress.emit(f"开始批量处理 {len(self.input_files)} 个CAD文件...")
            self.progress.emit(f"文本策略: {self.strategy}")
            self.progress.emit(f"清理现有块: {'是' if self.clear_existing_blocks else '否'}")
            self.progress.emit(f"写入材质/厚度属性: {'是' if self.write_material_thickness_attrib else '否'}")
            self.progress.emit(f"写入物料ID/图号/名称属性: {'是' if self.write_id_drawing_name_attrib else '否'}")
            
            success_count = 0
            failure_count = 0
            failed_files = []
            processed_block_names = set()  # 跟踪已处理的块名
            
            # 批量处理每个文件
            for i, input_file in enumerate(self.input_files, 1):
                file_basename = os.path.basename(input_file)
                self.progress.emit(f"\n{'-'*60}")
                self.progress.emit(f"[{i}/{len(self.input_files)}] 处理文件: {file_basename}")
                
                # 执行处理
                try:
                    # 首先设置CAD读取器的文件路径并加载文件，获取文本对象以生成块名
                    self.block_creator.cad_reader.file_path = input_file
                    if not self.block_creator.cad_reader.load_file():
                        self.progress.emit(f"❌ 文件加载失败")
                        failure_count += 1
                        failed_files.append(file_basename)
                        continue
                    
                    # 获取文本对象
                    text_objects = self.block_creator.cad_reader.get_text_objects()
                    
                    row_data = None
                    # 如果提供了Excel文件，根据Excel文件更新CAD文本
                    if self.excel_file and os.path.exists(self.excel_file):
                        self.block_creator.excel_reader.file_path = self.excel_file
                        if self.block_creator.excel_reader.load_file():
                            success, updated_count = self.block_creator.excel_reader.update_cad_texts_based_on_excel(text_objects, self.block_creator.cad_reader.doc)
                            if success:
                                # 尝试获取匹配的行数据
                                identifier = self.block_creator.excel_reader.find_identifier_in_texts(text_objects)
                                if identifier:
                                    row_data = self.block_creator.excel_reader.get_row_data(identifier)
                                    if row_data:
                                        self.progress.emit(f"✅ 已匹配Excel数据: {identifier}")
                                    else:
                                        self.progress.emit(f"⚠️ 匹配到标识符 {identifier} 但未找到行数据")
                                
                                # 重新获取文本对象，确保使用更新后的文本内容
                                text_objects = self.block_creator.cad_reader.get_text_objects()
                    
                    # 生成块名
                    if not text_objects:
                        block_name = "DEFAULT_BLOCK"
                    else:
                        block_name = self.block_creator.text_processor.generate_block_name_from_texts(text_objects, self.strategy)
                        if not block_name:
                            block_name = "DEFAULT_BLOCK"
                    
                    # 检查块名是否已经处理过
                    if block_name in processed_block_names:
                        self.progress.emit(f"⚠️  跳过处理：块名 '{block_name}' 已经处理过")
                        self.progress.emit(f"✅ 文件跳过成功")
                        continue
                    
                    # 标记块名为已处理
                    processed_block_names.add(block_name)
                    
                    # 执行实际的文件处理
                    result = self.block_creator.process_cad_file(
                        input_file, 
                        None,  # 不指定输出文件，让process_cad_file自动生成
                        self.strategy,
                        self.clear_existing_blocks,
                        self.output_dir,  # 传递输出目录
                        self.excel_file,  # 传递Excel文件路径
                        write_material_thickness_attrib=self.write_material_thickness_attrib,
                        write_id_drawing_name_attrib=self.write_id_drawing_name_attrib,
                        row_data=row_data # 传递Excel行数据
                    )
                    
                    if result:
                        # 显示生成的输出文件名
                        self.progress.emit(f"输出文件: {os.path.basename(result)}")
                        self.progress.emit(f"✅ 文件处理成功")
                        success_count += 1
                    else:
                        self.progress.emit(f"❌ 文件处理失败")
                        failure_count += 1
                        failed_files.append(file_basename)
                        # 从已处理集合中移除，因为处理失败
                        processed_block_names.remove(block_name)
                except Exception as e:
                    self.progress.emit(f"❌ 文件处理异常: {str(e)}")
                    failure_count += 1
                    failed_files.append(file_basename)
                    # 如果块名已经添加到集合中，移除它
                    if 'block_name' in locals() and block_name in processed_block_names:
                        processed_block_names.remove(block_name)
            
            # 汇总结果
            self.progress.emit(f"\n{'-'*60}")
            self.progress.emit(f"批量处理完成")
            self.progress.emit(f"成功: {success_count} 个文件")
            if failure_count > 0:
                self.progress.emit(f"失败: {failure_count} 个文件")
                if failed_files:
                    self.progress.emit(f"失败文件列表: {', '.join(failed_files)}")
            
            if success_count > 0:
                self.finished.emit(True, f"成功处理 {success_count} 个文件")
            else:
                self.finished.emit(False, f"所有 {len(self.input_files)} 个文件处理失败")
                
        except Exception as e:
            self.finished.emit(False, f"程序异常: {str(e)}")

class TextUpdaterWorker(QThread):
    """文本内容更改线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, excel_file, dxf_files, output_dir=None, refactor_enabled=False, refactor_attrs=None, append_suffix=True):
        super().__init__()
        self.excel_file = excel_file
        self.dxf_files = dxf_files
        self.output_dir = output_dir
        self.refactor_enabled = refactor_enabled
        self.refactor_attrs = refactor_attrs if refactor_attrs else []
        self.append_suffix = append_suffix
    
    def run(self):
        try:
            self.progress.emit(f"开始处理文本内容更改...")
            self.progress.emit(f"Excel文件: {os.path.basename(self.excel_file)}")
            self.progress.emit(f"DXF文件数量: {len(self.dxf_files)}")
            
            if self.refactor_enabled:
                self.progress.emit(f"模式: 文本重构 (包含: {', '.join(self.refactor_attrs)})")
            
            if self.append_suffix:
                 self.progress.emit("模式: 追加数量后缀")
            
            if not self.refactor_enabled and not self.append_suffix:
                 self.progress.emit("警告: 未启用任何修改模式！")
            
            # 延迟导入所需库
            import pandas as pd
            import ezdxf
            import re
            
            # 读取Excel文件
            df = pd.read_excel(self.excel_file)
            
            quantity_map = {}
            quantity_details = {}
            refactor_map = {} # ID -> formatted_string

            if self.refactor_enabled:
                # 文本重构模式
                # 定义属性键名到Excel列名的可能映射 (支持别名)
                possible_cols_map = {
                    'thickness': ['板厚', '厚度'],
                    'material': ['材质'],
                    'material_id': ['物料ID'],
                    'name': ['名称'],
                    'drawing_no': ['图号'],
                    'total_quantity': ['总数量']
                }

                # 确定实际使用的列名
                key_to_col = {}
                for key, candidates in possible_cols_map.items():
                    for col in candidates:
                        if col in df.columns:
                            key_to_col[key] = col
                            break

                # 检查必要的匹配列 (物料ID 或 图号)
                if 'material_id' not in key_to_col and 'drawing_no' not in key_to_col:
                     raise ValueError("Excel文件必须包含 '物料ID' 或 '图号' 列以用于匹配")
                
                # 检查用户选择的属性列是否存在
                attrs_to_use = self.refactor_attrs if self.refactor_attrs else ['thickness', 'material', 'material_id', 'name', 'drawing_no']
                
                missing_info = []
                for key in attrs_to_use:
                    if key not in key_to_col:
                        # 记录缺失的列名描述
                        candidates = possible_cols_map.get(key, [key])
                        missing_info.append(f"{'/'.join(candidates)}")
                
                if missing_info:
                    raise ValueError(f"Excel文件缺少选定的列: {', '.join(missing_info)}")
                
                # 辅助函数：安全获取并格式化值
                def get_formatted_val(row, key):
                    col = key_to_col.get(key)
                    if not col or col not in row or pd.isna(row[col]):
                        return ""
                    
                    val = str(row[col]).strip()
                    
                    # 过滤掉 "组件" 文本 (针对材质和板厚)
                    if key in ['thickness', 'material'] and val == "组件":
                        return ""
                        
                    # 特殊格式处理
                    if key == 'thickness':
                        if val.endswith('.0'):
                            val = val[:-2]
                    
                    return val

                # 创建重构映射
                for index, row in df.iterrows():
                    try:
                        # 提取匹配键
                        material_id_col = key_to_col.get('material_id')
                        drawing_no_col = key_to_col.get('drawing_no')
                        
                        material_id = str(row[material_id_col]).strip() if material_id_col and pd.notna(row[material_id_col]) else ""
                        drawing_no = str(row[drawing_no_col]).strip() if drawing_no_col and pd.notna(row[drawing_no_col]) else ""
                        
                        # 根据 attrs_to_use 构建文本
                        parts = []
                        for key in attrs_to_use:
                            val = get_formatted_val(row, key)
                            if val:
                                parts.append(val)
                        
                        formatted_text = " ".join(parts)
                        
                        # 使用物料ID或图号作为键
                        if material_id:
                            refactor_map[material_id] = formatted_text
                        if drawing_no:
                            refactor_map[drawing_no] = formatted_text
                            
                    except Exception as e:
                        self.progress.emit(f"  读取行 {index+1} 时出错: {str(e)}")
                
                self.progress.emit(f"  生成的重构映射包含了 {len(refactor_map)} 个条目")
                
            else:
                # 添加数量模式 (原有逻辑)
                if '总数量' not in df.columns:
                    raise ValueError("Excel文件缺少必要的列: 总数量")
                
                # 检查是否有物料ID和图号列
                has_material_id = '物料ID' in df.columns
                has_drawing_no = '图号' in df.columns
                
                if not has_material_id and not has_drawing_no:
                    raise ValueError("Excel文件缺少必要的列: 物料ID 或 图号")
                
                # 创建物料ID/图号到总数量的映射
                for index, row in df.iterrows():
                    try:
                        total_quantity = int(row['总数量'])
                        
                        # 如果有物料ID列，添加物料ID映射
                        if has_material_id and pd.notna(row['物料ID']):
                            material_id = str(row['物料ID']).strip()
                            if material_id in quantity_map:
                                quantity_map[material_id] += total_quantity
                                if material_id not in quantity_details:
                                    quantity_details[material_id] = []
                                quantity_details[material_id].append(total_quantity)
                                self.progress.emit(f"  物料ID {material_id} 已存在，叠加数量: {total_quantity}，总数量: {quantity_map[material_id]}")
                            else:
                                quantity_map[material_id] = total_quantity
                                quantity_details[material_id] = [total_quantity]
                                self.progress.emit(f"  读取到物料ID: {material_id}, 总数量: {total_quantity}")
                        
                        # 如果有图号列，添加图号映射
                        if has_drawing_no and pd.notna(row['图号']):
                            drawing_no = str(row['图号']).strip()
                            if drawing_no in quantity_map:
                                quantity_map[drawing_no] += total_quantity
                                if drawing_no not in quantity_details:
                                    quantity_details[drawing_no] = []
                                quantity_details[drawing_no].append(total_quantity)
                                self.progress.emit(f"  图号 {drawing_no} 已存在，叠加数量: {total_quantity}，总数量: {quantity_map[drawing_no]}")
                            else:
                                quantity_map[drawing_no] = total_quantity
                                quantity_details[drawing_no] = [total_quantity]
                                self.progress.emit(f"  读取到图号: {drawing_no}, 总数量: {total_quantity}")
                                
                    except (ValueError, TypeError) as e:
                        self.progress.emit(f"  读取行 {index+1} 时出错: {str(e)}")
                
                self.progress.emit(f"  生成的映射: {quantity_map}")
            
            # 处理每个DXF文件
            processed_files = 0
            for dxf_file in self.dxf_files:
                self.progress.emit(f"处理文件: {os.path.basename(dxf_file)}")
                
                # 读取DXF文件
                doc = ezdxf.readfile(dxf_file)
                
                # 收集所有需要处理的实体
                entities_to_process = []
                # 模型空间
                entities_to_process.extend(doc.modelspace())
                # 块定义
                for block in doc.blocks:
                    if not block.name.startswith('*'):
                        entities_to_process.extend(block)
                
                updated_count = 0
                for entity in entities_to_process:
                    if entity.dxftype() in ['TEXT', 'MTEXT']:
                        try:
                            # 获取文本内容
                            text_content = entity.dxf.text
                            
                            if self.refactor_enabled:
                                # 重构模式
                                for id_key, new_text in refactor_map.items():
                                    if id_key in text_content:
                                        # 直接替换
                                        entity.dxf.text = new_text
                                        self.progress.emit(f"  [重构] 匹配到: {id_key}, 原文本: {text_content}, 替换为: {new_text}")
                                        updated_count += 1
                                        break
                            else:
                                # 数量模式
                                # 检查文本是否包含物料ID或图号
                                for id_key, total_quantity in quantity_map.items():
                                    if id_key in text_content:
                                        # 生成数量显示文本
                                        quantity_list = quantity_details.get(id_key, [total_quantity])
                                        if len(quantity_list) > 1:
                                            quantity_str = "+" .join(map(str, quantity_list))
                                        else:
                                            quantity_str = str(total_quantity)
                                        
                                        # 检查是否已经添加了数量信息
                                        if '共' in text_content:
                                            new_text = re.sub(r'共\s*[\d\s+]+' + r'(\s*件)?', f'共{quantity_str}件' if '件' in text_content else f'共{quantity_str}', text_content)
                                            self.progress.emit(f"  匹配到ID: {id_key}, 文本: {text_content}, 替换为: {new_text}")
                                        else:
                                            new_text = f"{text_content} 共{quantity_str}件"
                                            self.progress.emit(f"  匹配到ID: {id_key}, 文本: {text_content}, 数量: {quantity_str}")
                                        
                                        entity.dxf.text = new_text
                                        updated_count += 1
                                        break
                                        
                        except Exception as e:
                            pass # 忽略单个实体的错误
                
                # 保存修改后的文件
                if self.output_dir:
                    output_file = os.path.join(self.output_dir, os.path.basename(dxf_file))
                else:
                    output_file = dxf_file
                doc.saveas(output_file)
                self.progress.emit(f"  更新了 {updated_count} 个文本，保存到: {os.path.basename(output_file)}")
                processed_files += 1
            
            self.progress.emit(f"\n处理完成！")
            self.progress.emit(f"成功处理 {processed_files} 个DXF文件")
            self.finished.emit(True, f"成功处理 {processed_files} 个DXF文件")
        except Exception as e:
            self.progress.emit(f"处理异常: {str(e)}")
            self.finished.emit(False, f"程序异常: {str(e)}")

class CadMergeWorker(QThread):
    """CAD文件合并线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, input_files, output_path, spacing, show_filenames):
        super().__init__()
        self.input_files = input_files
        self.output_path = output_path
        self.spacing = spacing
        self.show_filenames = show_filenames
    
    def run(self):
        try:
            self.progress.emit(f"开始合并 {len(self.input_files)} 个文件...")
            
            # 延迟导入merge_dxf_files
            from cad_merge import merge_dxf_files
            
            # 执行合并
            merge_dxf_files(
                self.input_files, 
                self.output_path, 
                self.spacing,
                show_filenames=self.show_filenames
            )
            
            # 记录完成日志
            self.progress.emit(f"合并完成！输出文件: {self.output_path}")
            self.progress.emit(f"总图纸数量: {len(self.input_files)}")
            
            self.finished.emit(True, f"成功合并 {len(self.input_files)} 个CAD文件")
        except Exception as e:
            self.progress.emit(f"合并失败: {str(e)}")
            self.finished.emit(False, f"合并失败: {str(e)}")

class BOMCalculatorTab(QWidget):
    """BOM数量计算器选项卡"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 文件设置组
        file_group = QGroupBox("文件设置")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setMinimumWidth(300)
        self.input_btn = QPushButton('选择Excel文件')
        self.input_btn.clicked.connect(self.select_input_file)
        self.input_btn.setMinimumWidth(100)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.input_btn)
        file_layout.addRow("输入Excel文件:", input_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 处理设置组
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout()
        
        # 按钮组
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton('开始处理')
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.run_bom_calculator)
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_log_btn)

        # 布局选项：只保留按钮布局
        settings_layout.addLayout(btn_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)
        
        # 日志输出
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setAcceptRichText(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)  # 占用剩余空间
        
        self.setLayout(main_layout)
    
    def select_input_file(self):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Excel文件", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.input_edit.setText(file_path)
    
    def clear_log(self):
        """清空日志"""
        self.log_output.clear()
    
    def add_log(self, text):
        """添加日志信息"""
        self.log_output.append(text)
        self.log_output.moveCursor(self.log_output.textCursor().End)
    
    def run_bom_calculator(self):
        """运行BOM数量计算器"""
        input_file = self.input_edit.text().strip()
        if not input_file:
            QMessageBox.warning(self, "输入错误", "请选择Excel文件！")
            return
        
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "输入错误", f"文件不存在: {input_file}")
            return
        
        # 禁用按钮
        self.run_btn.setEnabled(False)
        self.input_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        
        # 清空日志和更新状态
        self.log_output.clear()
        self.progress.setValue(0)
        self.progress.setFormat("准备处理...")
        
        # 创建工作线程
        self.worker = ExcelWorker(input_file)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.add_log)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()
    
    def on_process_finished(self, success, result):
        """处理完成回调"""
        # 恢复按钮状态
        self.run_btn.setEnabled(True)
        self.input_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(True)
        
        if success:
            self.progress.setValue(100)
            self.progress.setFormat("处理完成")
            
            # 对于长消息，分开发送
            if '\n警告信息:' in result:
                output_path = result.split('\n警告信息:')[0]
                QMessageBox.information(self, "成功", f"处理完成！\n结果已保存到：\n{output_path}")
                # 如果有警告，可以选择是否显示
                if QMessageBox.question(self, "警告信息", "处理过程中有一些警告，是否查看？") == QMessageBox.Yes:
                    warning_text = result.split('\n警告信息:')[1]
                    self.show_warnings(warning_text)
            else:
                QMessageBox.information(self, "成功", f"处理完成！\n结果已保存到：\n{result}")
        else:
            self.progress.setValue(0)
            self.progress.setFormat("处理失败")
            QMessageBox.critical(self, "处理失败", f"处理失败：{result}")
    
    def show_warnings(self, text):
        """显示警告信息"""
        from PyQt5.QtWidgets import QDialog
        
        # 使用QDialog代替QWidget，并设置为模态对话框
        win = QDialog(self)
        win.setWindowTitle("警告信息")
        win.resize(800, 500)
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(text)
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("复制到剪贴板")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(text))
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(win.close)
        
        btn_layout.addWidget(copy_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        win.setLayout(layout)
        
        # 使用exec_()显示模态对话框，这样窗口不会被立即回收
        win.exec_()

class BlockFinderTab(QWidget):
    """块筛寻和合并选项卡"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 文件设置组
        file_group = QGroupBox("文件设置")
        file_layout = QFormLayout()
        
        # Excel文件
        excel_layout = QHBoxLayout()
        self.excel_edit = QLineEdit()
        self.excel_edit.setMinimumWidth(300)
        self.excel_btn = QPushButton('选择Excel文件')
        self.excel_btn.clicked.connect(self.select_excel_file)
        self.excel_btn.setMinimumWidth(100)
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_btn)
        file_layout.addRow("Excel文件:", excel_layout)
        
        # DXF文件列表
        dxf_layout = QVBoxLayout()
        dxf_file_layout = QHBoxLayout()
        self.dxf_edit = QLineEdit()
        self.dxf_edit.setMinimumWidth(300)
        self.dxf_btn = QPushButton('选择DXF文件')
        self.dxf_btn.clicked.connect(self.select_dxf_files)
        self.dxf_btn.setMinimumWidth(100)
        dxf_file_layout.addWidget(self.dxf_edit)
        dxf_file_layout.addWidget(self.dxf_btn)
        dxf_layout.addLayout(dxf_file_layout)
        
        # DXF文件列表显示
        self.dxf_list = QListWidget()
        self.dxf_list.setMinimumHeight(100)
        dxf_layout.addWidget(self.dxf_list)
        
        # 清除DXF文件列表按钮
        clear_dxf_btn = QPushButton('清除DXF文件列表')
        clear_dxf_btn.clicked.connect(self.clear_dxf_list)
        dxf_layout.addWidget(clear_dxf_btn)
        
        file_layout.addRow("DXF文件列表:", dxf_layout)
        
        # 输出目录
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setMinimumWidth(300)
        self.output_btn = QPushButton('选择输出目录')
        self.output_btn.clicked.connect(self.select_output_dir)
        self.output_btn.setMinimumWidth(100)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_btn)
        file_layout.addRow("输出目录:", output_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 处理设置组
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout()
        
        # 按钮组
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton('开始筛寻和合并')
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.run_block_finder)
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.clicked.connect(self.clear_log)

        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_log_btn)

        # 布局选项：对齐方式与间距设置
        layout_opts = QHBoxLayout()
        self.align_combo = QComboBox()
        self.align_combo.addItem("底部对齐", "bottom")
        self.align_combo.addItem("中心对齐", "center")
        self.align_combo.setCurrentIndex(0)  # 默认底部对齐
        layout_opts.addWidget(QLabel("对齐方式:"))
        layout_opts.addWidget(self.align_combo)

        # 边到边距离启用按钮
        self.edge_spacing_checkbox = QCheckBox("使用块边到边距离")
        self.edge_spacing_checkbox.setChecked(True)
        layout_opts.addWidget(self.edge_spacing_checkbox)

        layout_opts.addStretch()

        layout_opts.addWidget(QLabel('块间距'))
        self.block_spacing_spin = QSpinBox()
        self.block_spacing_spin.setRange(50, 5000)
        self.block_spacing_spin.setValue(600)
        self.block_spacing_spin.setSingleStep(50)
        layout_opts.addWidget(self.block_spacing_spin)

        layout_opts.addWidget(QLabel('块边到边距离'))
        self.edge_spacing_spin = QSpinBox()
        self.edge_spacing_spin.setRange(0, 2000)
        self.edge_spacing_spin.setValue(100)
        self.edge_spacing_spin.setSingleStep(10)
        layout_opts.addWidget(self.edge_spacing_spin)

        layout_opts.addWidget(QLabel('组间距'))
        self.group_spacing_spin = QSpinBox()
        self.group_spacing_spin.setRange(50, 10000)
        self.group_spacing_spin.setValue(800)
        self.group_spacing_spin.setSingleStep(50)
        layout_opts.addWidget(self.group_spacing_spin)

        # 文本策略选择
        text_strategy_layout = QHBoxLayout()
        text_strategy_layout.addWidget(QLabel('文本策略:'))
        self.text_strategy_combo = QComboBox()
        self.text_strategy_combo.addItem('first_valid', 'first_valid')
        self.text_strategy_combo.addItem('combine', 'combine')
        self.text_strategy_combo.setCurrentIndex(0)
        text_strategy_layout.addWidget(self.text_strategy_combo)
        text_strategy_layout.addStretch()
        
        # 合并属性配置（使用分组框代替原有布局）
        attrib_group = QGroupBox("合并属性配置")
        attrib_layout = QGridLayout()
        
        # 定义属性及其标签
        # 结构：(键名, 显示标签, 行, 列)
        self.attrib_checkboxes = {}
        attribs_config = [
            ('material', '材质', 0, 0),
            ('thickness', '板厚', 0, 1),
            ('material_id', '物料ID', 0, 2),
            ('name', '名称', 1, 0),
            ('drawing_num', '图号', 1, 1),
            ('total_qty', '总数量', 1, 2)
        ]
        
        for key, label, r, c in attribs_config:
            cb = QCheckBox(label)
            cb.setChecked(True)  # 默认全部选中
            self.attrib_checkboxes[key] = cb
            attrib_layout.addWidget(cb, r, c)
            
        # 添加Excel总数量统计显示
        # “在合并属性表格最右侧新增固定列...数字每三位加千位分隔符”
        # 我们在这里添加一个Label来显示统计结果
        self.excel_stats_label = QLabel("Excel总记录数: —")
        self.excel_stats_label.setAlignment(Qt.AlignCenter)
        self.excel_stats_label.setStyleSheet("font-weight: bold; color: #333; border: 1px solid #ccc; padding: 5px; min-width: 120px;")
        
        # 将统计标签放在Grid的右侧，或者单独一行
        # 按照“最右侧新增固定列”的要求，我们可以把它放在第3列（如果只有2列属性），或者单独作为一个大控件
        # 这里我们放在第0行第3列，跨2行
        attrib_layout.addWidget(self.excel_stats_label, 0, 3, 2, 1)
        
        attrib_group.setLayout(attrib_layout)
        settings_layout.addWidget(attrib_group)

        # 删除重复线选项
        cleanup_layout = QHBoxLayout()
        self.remove_duplicates_checkbox = QCheckBox("删除重复线")
        self.remove_duplicates_checkbox.setChecked(True)
        self.remove_duplicates_checkbox.setToolTip("合并后检查并删除重叠或重复的线条（可能增加处理时间）")
        cleanup_layout.addWidget(self.remove_duplicates_checkbox)
        cleanup_layout.addStretch()

        settings_layout.addLayout(layout_opts)
        settings_layout.addLayout(text_strategy_layout)
        settings_layout.addLayout(attrib_layout)
        settings_layout.addLayout(cleanup_layout)
        settings_layout.addLayout(btn_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)

        self.audit_tip_label = QLabel("图形不能复制粘贴，输入 AUDIT 命令")
        self.audit_tip_label.setStyleSheet("color: red; font-weight: bold;")
        self.audit_tip_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.audit_tip_label)
        
        # 日志输出
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setAcceptRichText(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)  # 占用剩余空间
        
        self.setLayout(main_layout)

        # 连接Excel文件选择变更信号，用于实时更新行数统计
        self.excel_edit.textChanged.connect(self.on_excel_file_changed)
    
    def on_excel_file_changed(self, file_path):
        """Excel文件路径变更处理"""
        if not file_path or not os.path.exists(file_path):
            self.excel_stats_label.setText("Excel总记录数: —")
            return
            
        # 启动后台线程统计行数
        self.stats_worker = ExcelStatsWorker(file_path)
        self.stats_worker.finished.connect(self.update_excel_stats)
        self.stats_worker.start()
        
    def update_excel_stats(self, count, is_estimate):
        """更新Excel行数统计显示"""
        if count < 0:
            self.excel_stats_label.setText("Excel总记录数: 读取失败")
            return
            
        # 格式化数字（千位分隔符）
        formatted_count = "{:,}".format(count)
        text = f"Excel总记录数: {formatted_count}"
        if is_estimate:
            text += " (估算)"
            
        self.excel_stats_label.setText(text)
    
    def select_excel_file(self):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Excel文件", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.excel_edit.setText(file_path)
    
    def select_dxf_files(self):
        """选择多个DXF文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "选择DXF文件", 
            "", 
            "DXF Files (*.dxf);;All Files (*)"
        )
        if file_paths:
            # 更新文本框显示选中的文件数量
            self.dxf_edit.setText(f"已选择 {len(file_paths)} 个文件")
            # 更新文件列表
            self.dxf_list.clear()
            for file_path in file_paths:
                self.dxf_list.addItem(file_path)
    
    def clear_dxf_list(self):
        """清除DXF文件列表"""
        self.dxf_edit.clear()
        self.dxf_list.clear()
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择输出目录", 
            ""
        )
        if dir_path:
            self.output_edit.setText(dir_path)
    
    def clear_log(self):
        """清空日志"""
        self.log_output.clear()
    
    def add_log(self, text):
        """添加日志信息"""
        self.log_output.append(text)
        self.log_output.moveCursor(self.log_output.textCursor().End)
    
    def run_block_finder(self):
        """运行块筛寻和合并"""
        excel_file = self.excel_edit.text().strip()
        dxf_files = [self.dxf_list.item(i).text() for i in range(self.dxf_list.count())]
        output_dir = self.output_edit.text().strip()
        
        if not excel_file:
            QMessageBox.warning(self, "输入错误", "请选择Excel文件！")
            return
        
        if not dxf_files:
            QMessageBox.warning(self, "输入错误", "请选择至少一个DXF文件！")
            return
        
        if not output_dir:
            QMessageBox.warning(self, "输入错误", "请选择输出目录！")
            return
        
        # 检查文件是否存在
        if not os.path.exists(excel_file):
            QMessageBox.warning(self, "输入错误", f"Excel文件不存在: {excel_file}")
            return
        
        for dxf_file in dxf_files:
            if not os.path.exists(dxf_file):
                QMessageBox.warning(self, "输入错误", f"DXF文件不存在: {dxf_file}")
                return
        
        # 禁用按钮
        self.run_btn.setEnabled(False)
        self.excel_btn.setEnabled(False)
        self.dxf_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        
        # 清空日志和更新状态
        self.log_output.clear()
        self.progress.setValue(0)
        self.progress.setFormat("准备处理...")
        # 从 UI 获取布局设置
        align_mode = self.align_combo.currentData()
        center_align = (align_mode == "center")
        use_edge_spacing = self.edge_spacing_checkbox.isChecked()
        block_spacing = float(self.block_spacing_spin.value())
        edge_spacing = float(self.edge_spacing_spin.value())
        group_spacing = float(self.group_spacing_spin.value())
        text_strategy = self.text_strategy_combo.currentData()
        
        # 获取合并属性配置
        # 构建一个字典：{ key: is_checked }
        attribs_config = {}
        for key, cb in self.attrib_checkboxes.items():
            attribs_config[key] = cb.isChecked()
            
        remove_duplicates = self.remove_duplicates_checkbox.isChecked()

        # 创建工作线程
        self.worker = BlockFinderWorker(excel_file, dxf_files, output_dir,
                                        center_align=center_align,
                                        use_edge_spacing=use_edge_spacing,
                                        block_spacing=block_spacing,
                                        edge_spacing=edge_spacing,
                                        group_spacing=group_spacing,
                                        text_strategy=text_strategy,
                                        attribs_config=attribs_config, # 传递细粒度的属性配置
                                        remove_duplicates=remove_duplicates)
        self.worker.progress.connect(self.add_log)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()
    
    def on_process_finished(self, success, result):
        """处理完成回调"""
        # 恢复按钮状态
        self.run_btn.setEnabled(True)
        self.excel_btn.setEnabled(True)
        self.dxf_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(True)
        
        if success:
            self.progress.setValue(100)
            self.progress.setFormat("处理完成")
            QMessageBox.information(self, "成功", f"处理完成！\n{result}")
        else:
            self.progress.setValue(0)
            self.progress.setFormat("处理失败")
            QMessageBox.critical(self, "处理失败", f"处理失败：{result}")

class ExcelStatsWorker(QThread):
    """Excel行数统计后台线程"""
    finished = pyqtSignal(int, bool)  # (count, is_estimate)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        try:
            # 快速统计行数
            # 如果文件较小，使用 pandas；如果较大，使用 openpyxl read_only
            # 这里为了简单和复用，先尝试 pandas (header only) 来估算，或者直接读取
            # 考虑到性能要求 "10万行 < 1秒"，我们使用 openpyxl 的 read_only 模式
            import openpyxl
            
            # 使用 openpyxl 的只读模式打开，不加载数据到内存
            wb = openpyxl.load_workbook(self.file_path, read_only=True, data_only=True)
            sheet = wb.active
            
            # 获取最大行数
            # 注意：max_row 在某些情况下可能不准确（如空行被视为已使用），但在只读模式下通常是元数据
            # 如果要精确，需要遍历。
            # 这里先使用 max_row 作为快速估算
            max_row = sheet.max_row
            
            # 减去表头（假设第1行是表头）
            count = max(0, max_row - 1)
            
            # 如果行数非常大（>10万），我们标记为估算值（虽然这里 max_row 是精确的，但为了符合需求描述）
            # 实际上 openpyxl read_only 获取 max_row 是非常快的 O(1) 或 O(N) depending on implementation
            is_estimate = False
            if count > 100000:
                 # 对于超大文件，我们直接返回 max_row，但标记为“可能包含空行”的估算性质
                 # 实际上对于 Excel，max_row 包含了所有曾被编辑过的行
                 is_estimate = True
            
            wb.close()
            self.finished.emit(count, is_estimate)
            
        except Exception as e:
            print(f"Excel统计失败: {e}")
            self.finished.emit(-1, False)

class ExportBlocksTab(QWidget):
    """块批量导出选项卡"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 文件设置组
        file_group = QGroupBox("文件设置")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setMinimumWidth(300)
        self.input_btn = QPushButton('选择DXF文件')
        self.input_btn.clicked.connect(self.select_input_file)
        self.input_btn.setMinimumWidth(100)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.input_btn)
        file_layout.addRow("输入DXF文件:", input_layout)
        
        # 输出目录
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setMinimumWidth(300)
        self.output_btn = QPushButton('选择输出目录')
        self.output_btn.clicked.connect(self.select_output_dir)
        self.output_btn.setMinimumWidth(100)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_btn)
        file_layout.addRow("输出目录:", output_layout)

    # （已移除参考文件 UI，导出将使用仓库中固定的文件A作为文本来源）
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 处理设置组
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout()
        
        # 按钮组
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton('开始导出')
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.run_export_blocks)
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_log_btn)
        
        settings_layout.addLayout(btn_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)
        
        # 日志输出
        log_group = QGroupBox("导出日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setAcceptRichText(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)  # 占用剩余空间
        
        self.setLayout(main_layout)
    
    def select_input_file(self):
        """选择DXF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择DXF文件", 
            "", 
            "DXF Files (*.dxf);;All Files (*)"
        )
        if file_path:
            self.input_edit.setText(file_path)
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择输出目录", 
            ""
        )
        if dir_path:
            self.output_edit.setText(dir_path)

    # 参考文件选择功能已移除；导出时会自动使用项目内的默认文件A作为文本来源。
    
    def clear_log(self):
        """清空日志"""
        self.log_output.clear()
    
    def add_log(self, text):
        """添加日志信息"""
        self.log_output.append(text)
        self.log_output.moveCursor(self.log_output.textCursor().End)
    
    def run_export_blocks(self):
        """运行块导出工具"""
        input_file = self.input_edit.text().strip()
        output_dir = self.output_edit.text().strip()
        
        if not input_file:
            QMessageBox.warning(self, "输入错误", "请选择DXF文件！")
            return
        
        if not output_dir:
            QMessageBox.warning(self, "输入错误", "请选择输出目录！")
            return
        
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "输入错误", f"文件不存在: {input_file}")
            return
        
        # 禁用按钮
        self.run_btn.setEnabled(False)
        self.input_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        
        # 清空日志和更新状态
        self.log_output.clear()
        self.progress.setValue(0)
        self.progress.setFormat("准备导出...")
        
        # 创建工作线程：使用仓库内固定的文件A作为参考文本来源（若存在）
        default_ref = os.path.join(os.path.dirname(__file__), 'cad', 'DWG合并163101002008077-2_网板-.dxf')
        reference_file = default_ref if os.path.exists(default_ref) else None
        self.worker = ExportBlocksWorker(input_file, output_dir, reference_file=reference_file)
        self.worker.progress.connect(self.add_log)
        self.worker.block_count.connect(self.update_progress)
        self.worker.finished.connect(self.on_export_finished)
        self.worker.start()
    
    def update_progress(self, total, exported):
        """更新进度条"""
        if total > 0:
            progress = int((exported / total) * 100)
            self.progress.setValue(progress)
            self.progress.setFormat(f"正在导出... {progress}%")
    
    def on_export_finished(self, success, result):
        """导出完成回调"""
        # 恢复按钮状态
        self.run_btn.setEnabled(True)
        self.input_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(True)
        
        if success:
            self.progress.setValue(100)
            self.progress.setFormat("导出完成")
            QMessageBox.information(self, "成功", "块导出完成！")
        else:
            self.progress.setValue(0)
            self.progress.setFormat("导出失败")
            QMessageBox.critical(self, "失败", f"块导出失败: {result}")

class BlockCreatorTab(QWidget):
    """CAD块创建选项卡"""
    def __init__(self):
        super().__init__()
        from block_creator import BlockCreator
        self.block_creator = BlockCreator()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 文件设置组
        file_group = QGroupBox("文件设置")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setMinimumWidth(300)
        self.input_btn = QPushButton('选择输入文件')
        self.input_btn.clicked.connect(self.select_input_file)
        self.input_btn.setMinimumWidth(100)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.input_btn)
        file_layout.addRow("输入DXF文件:", input_layout)
        
        # Excel文件（可选）
        excel_layout = QHBoxLayout()
        self.excel_edit = QLineEdit()
        self.excel_edit.setMinimumWidth(300)
        self.excel_btn = QPushButton('选择Excel文件')
        self.excel_btn.clicked.connect(self.select_excel_file)
        self.excel_btn.setMinimumWidth(100)
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_btn)
        file_layout.addRow("Excel文件（可选）:", excel_layout)
        
        # 输出目录
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setMinimumWidth(300)
        self.output_btn = QPushButton('选择输出目录')
        self.output_btn.clicked.connect(self.select_output_file)
        self.output_btn.setMinimumWidth(100)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_btn)
        file_layout.addRow("输出目录:", output_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 处理设置组
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout()
        
        # 策略选择
        strategy_layout = QVBoxLayout()
        strategy_label = QLabel("文本策略:")
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['first_valid', 'combine'])
        self.strategy_combo.currentIndexChanged.connect(self.update_strategy_description)
        strategy_desc_label = QLabel()
        self.strategy_desc_label = strategy_desc_label
        self.strategy_desc_label.setWordWrap(True)
        self.strategy_desc_label.setMinimumHeight(40)
        self.update_strategy_description(0)  # 初始化显示说明
        
        strategy_layout.addWidget(strategy_label)
        strategy_layout.addWidget(self.strategy_combo)
        strategy_layout.addWidget(self.strategy_desc_label)
        
        # 添加清理块选项
        self.clear_blocks_checkbox = QCheckBox("清理现有块")
        self.clear_blocks_checkbox.setChecked(False)  # 默认不清理
        self.clear_blocks_checkbox.setToolTip("选择是否在创建新块前清理文件中现有的自定义块")
        strategy_layout.addWidget(self.clear_blocks_checkbox)
        
        # 属性写入选项
        attrib_layout = QHBoxLayout()
        self.write_material_thickness_checkbox = QCheckBox("写入材质/厚度属性")
        self.write_material_thickness_checkbox.setChecked(True)
        attrib_layout.addWidget(self.write_material_thickness_checkbox)
        self.write_id_drawing_name_checkbox = QCheckBox("写入物料ID/图号/名称属性")
        self.write_id_drawing_name_checkbox.setChecked(True)
        attrib_layout.addWidget(self.write_id_drawing_name_checkbox)
        attrib_layout.addStretch()
        
        strategy_layout.addLayout(attrib_layout)
        
        # 按钮组
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton('开始处理')
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.run_block_creator)
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_log_btn)
        
        settings_layout.addLayout(strategy_layout)
        settings_layout.addLayout(btn_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)
        
        # 日志输出
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setAcceptRichText(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)  # 占用剩余空间
        
        self.setLayout(main_layout)
        
        # 初始化输入文件列表
        self.input_files = []
    
    def update_strategy_description(self, index):
        """更新策略说明文本"""
        descriptions = {
            'first_valid': "第一个有效文本：使用文件中找到的第一个有效的文本内容作为块名。\n适合：只有一个主要文本标签的图纸。",
            'combine': "组合所有文本：将文件中所有文本内容合并后作为块名。\n适合：需要包含多个信息标签的图纸。"
        }
        current_strategy = self.strategy_combo.currentText()
        self.strategy_desc_label.setText(descriptions.get(current_strategy, "选择文本处理策略"))
    
    def select_input_file(self):
        """选择输入DXF文件（支持多选）"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "选择DXF文件", 
            "", 
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if files:
            # 存储选择的文件列表
            self.input_files = files
            
            # 更新显示
            if len(files) == 1:
                # 单个文件直接显示完整路径
                self.input_edit.setText(files[0])
                self.input_edit.setToolTip(files[0])
            else:
                # 多个文件显示数量和部分文件名
                self.input_edit.setText(f"已选择 {len(files)} 个文件")
                # 设置tooltip显示所有文件路径
                tooltip_text = "\n".join(files)
                self.input_edit.setToolTip(tooltip_text)
                
                # 确保第一个文件的输出路径设置合理
                if files:
                    first_file = files[0]
                    # 默认输出路径为第一个文件的目录
                    output_dir = os.path.dirname(first_file)
                    # 只有当输出编辑框为空时才设置默认值
                    if not self.output_edit.text().strip():
                        self.output_edit.setText(output_dir)
    
    def select_output_file(self):
        """选择输出目录"""
        # 总是显示选择目录对话框
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择输出目录", 
            ""
        )
        
        if dir_path:
            self.output_edit.setText(dir_path)
    
    def select_excel_file(self):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Excel文件", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.excel_edit.setText(file_path)
    
    def clear_log(self):
        """清空日志"""
        self.log_output.clear()
    
    def add_log(self, text):
        """添加日志信息"""
        self.log_output.append(text)
        self.log_output.moveCursor(self.log_output.textCursor().End)
    
    def run_block_creator(self):
        """运行块创建工具（支持批量处理）"""
        # 使用input_files列表而不是单个文件
        if not hasattr(self, 'input_files') or not self.input_files:
            QMessageBox.warning(self, "输入错误", "请正确选择至少一个DXF文件！")
            return
        
        # 验证所有输入文件是否存在
        invalid_files = []
        for file_path in self.input_files:
            if not os.path.isfile(file_path):
                invalid_files.append(file_path)
        
        if invalid_files:
            QMessageBox.warning(self, "输入错误", f"以下文件不存在:\n{chr(10).join(invalid_files)}")
            return
        
        # 确定输出目录
        output_path = self.output_edit.text().strip()
        output_dir = None
        if output_path:
            # 检查是目录还是文件
            if os.path.isdir(output_path):
                output_dir = output_path
            else:
                # 如果是文件，提取目录部分
                output_dir = os.path.dirname(output_path)
            
            # 验证输出目录
            if output_dir and not os.path.exists(output_dir):
                QMessageBox.warning(self, "输出错误", f"输出目录不存在: {output_dir}")
                return
        else:
            # 如果用户没有选择输出目录，使用第一个输入文件的目录作为默认输出目录
            if self.input_files:
                first_file = self.input_files[0]
                output_dir = os.path.dirname(first_file)
            else:
                QMessageBox.warning(self, "输出错误", "请选择输出目录！")
                return
        
        strategy = self.strategy_combo.currentText()
        clear_existing_blocks = self.clear_blocks_checkbox.isChecked()
        write_material_thickness_attrib = self.write_material_thickness_checkbox.isChecked()
        write_id_drawing_name_attrib = self.write_id_drawing_name_checkbox.isChecked()
        
        # 禁用按钮防止重复点击
        self.run_btn.setEnabled(False)
        self.input_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        self.strategy_combo.setEnabled(False)
        self.clear_blocks_checkbox.setEnabled(False)  # 禁用清理块复选框
        self.write_material_thickness_checkbox.setEnabled(False)
        self.write_id_drawing_name_checkbox.setEnabled(False)
        
        # 清空日志和更新状态
        self.log_output.clear()
        self.progress.setValue(0)
        self.progress.setFormat("准备批量处理...")
        
        # 获取Excel文件路径
        excel_file = self.excel_edit.text().strip() if hasattr(self, 'excel_edit') else None
        
        # 创建工作线程
        self.worker = BlockCreatorWorker(
            self.block_creator, 
            self.input_files,  # 传递文件列表
            output_dir,        # 传递输出目录
            strategy,
            clear_existing_blocks,
            excel_file,  # 传递Excel文件路径
            write_material_thickness_attrib,
            write_id_drawing_name_attrib
        )
        self.worker.progress.connect(self.add_log)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()
    
    def on_process_finished(self, success, message):
        """处理完成回调"""
        # 恢复按钮状态
        self.run_btn.setEnabled(True)
        self.input_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(True)
        self.strategy_combo.setEnabled(True)
        self.clear_blocks_checkbox.setEnabled(True)  # 启用清理块复选框
        self.write_material_thickness_checkbox.setEnabled(True)
        self.write_id_drawing_name_checkbox.setEnabled(True)
        
        if success:
            self.progress.setValue(100)
            self.progress.setFormat("处理完成")
            QMessageBox.information(self, "处理完成", message)
        else:
            self.progress.setValue(0)
            self.progress.setFormat("处理失败")
            QMessageBox.critical(self, "处理失败", message)

class BlockFinderWorker(QThread):
    """块筛寻和合并线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, excel_file, dxf_files, output_dir,
                 center_align=True, use_edge_spacing=True, block_spacing=600.0, edge_spacing=100.0, group_spacing=800.0,
                 text_strategy='first_valid', attribs_config=None, remove_duplicates=False):
        super().__init__()
        self.excel_file = excel_file
        self.dxf_files = dxf_files
        self.output_dir = output_dir
        # 布局选项
        self.center_align = center_align
        self.use_edge_spacing = use_edge_spacing
        self.block_spacing = float(block_spacing)
        self.edge_spacing = float(edge_spacing)
        self.group_spacing = float(group_spacing)
        self.text_strategy = text_strategy
        self.attribs_config = attribs_config
        self.remove_duplicates = remove_duplicates
    
    def run(self):
        try:
            self.progress.emit(f"开始处理块筛寻和合并...")
            self.progress.emit(f"Excel文件: {os.path.basename(self.excel_file)}")
            self.progress.emit(f"DXF文件数量: {len(self.dxf_files)}")
            self.progress.emit(f"输出目录: {self.output_dir}")
            self.progress.emit(f"文本策略: {self.text_strategy}")
            self.progress.emit(f"使用块边到边距离: {self.use_edge_spacing}")
            self.progress.emit(f"删除重复线: {self.remove_duplicates}")
            if self.use_edge_spacing:
                self.progress.emit(f"块边到边距离: {self.edge_spacing}")
            else:
                self.progress.emit(f"块间距: {self.block_spacing}")
            
            # 延迟导入BlockFinder
            from block_finder import BlockFinder
            finder = BlockFinder(text_strategy=self.text_strategy)
            
            # 执行处理，传递布局参数和进度回调
            success = finder.process_files(self.excel_file, self.dxf_files, self.output_dir,
                                           center_align=self.center_align,
                                           use_edge_spacing=self.use_edge_spacing,
                                           block_spacing=self.block_spacing,
                                           edge_spacing=self.edge_spacing,
                                           group_spacing=self.group_spacing,
                                           attribs_config=self.attribs_config,
                                           text_strategy=self.text_strategy,
                                           remove_duplicates=self.remove_duplicates,
                                           progress_callback=self.progress.emit)
            
            if success:
                merged_file = os.path.join(self.output_dir, 'merged_blocks.dxf')
                updated_excel_file = os.path.join(self.output_dir, 'updated_' + os.path.basename(self.excel_file))
                self.progress.emit(f"\n{'-'*60}")
                self.progress.emit(f"处理完成！")
                self.progress.emit(f"合并后的块文件: {merged_file}")
                self.progress.emit(f"更新后的Excel文件: {updated_excel_file}")
                self.finished.emit(True, f"成功完成块筛寻和合并操作")
            else:
                self.finished.emit(False, "块筛寻和合并操作失败")
                
        except Exception as e:
            self.progress.emit(f"处理异常: {str(e)}")
            self.finished.emit(False, f"程序异常: {str(e)}")

class TextUpdaterTab(QWidget):
    """文本内容更改选项卡"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 文件设置组
        file_group = QGroupBox("文件设置")
        file_layout = QFormLayout()
        
        # Excel文件
        excel_layout = QHBoxLayout()
        self.excel_edit = QLineEdit()
        self.excel_edit.setMinimumWidth(300)
        self.excel_btn = QPushButton('选择Excel文件')
        self.excel_btn.clicked.connect(self.select_excel_file)
        self.excel_btn.setMinimumWidth(100)
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(self.excel_btn)
        file_layout.addRow("Excel文件:", excel_layout)
        
        # DXF文件列表
        dxf_layout = QVBoxLayout()
        dxf_file_layout = QHBoxLayout()
        self.dxf_edit = QLineEdit()
        self.dxf_edit.setMinimumWidth(300)
        self.dxf_btn = QPushButton('选择DXF文件')
        self.dxf_btn.clicked.connect(self.select_dxf_files)
        self.dxf_btn.setMinimumWidth(100)
        dxf_file_layout.addWidget(self.dxf_edit)
        dxf_file_layout.addWidget(self.dxf_btn)
        dxf_layout.addLayout(dxf_file_layout)
        
        # DXF文件列表显示
        self.dxf_list = QListWidget()
        self.dxf_list.setMinimumHeight(100)
        dxf_layout.addWidget(self.dxf_list)
        
        # 清除DXF文件列表按钮
        clear_dxf_btn = QPushButton('清除DXF文件列表')
        clear_dxf_btn.clicked.connect(self.clear_dxf_list)
        dxf_layout.addWidget(clear_dxf_btn)
        
        file_layout.addRow("DXF文件列表:", dxf_layout)
        
        # 输出目录
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setMinimumWidth(300)
        self.output_btn = QPushButton('选择输出目录')
        self.output_btn.clicked.connect(self.select_output_dir)
        self.output_btn.setMinimumWidth(100)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_btn)
        file_layout.addRow("输出目录:", output_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 处理设置组
        settings_group = QGroupBox("处理设置")
        settings_layout = QVBoxLayout()
        
        # 1. 文本重构设置
        self.refactor_group = QGroupBox("文本重构模式 (完全替换原有文本)")
        self.refactor_group.setCheckable(True)
        self.refactor_group.setChecked(False)
        self.refactor_group.setToolTip("启用此模式将根据Excel属性重新构建文本内容")
        
        refactor_layout = QGridLayout()
        self.attr_checkboxes = {}
        # 定义属性及其位置 (标签, 键名, 行, 列)
        attrs = [
            ('板厚', 'thickness', 0, 0),
            ('材质', 'material', 0, 1),
            ('物料ID', 'material_id', 0, 2),
            ('名称', 'name', 1, 0),
            ('图号', 'drawing_no', 1, 1),
            ('总数量', 'total_quantity', 1, 2)
        ]
        
        for label, key, r, c in attrs:
            cb = QCheckBox(label)
            # 默认除了总数量外都选中，或者全部选中？用户之前要求的是前5个。
            if key != 'total_quantity':
                cb.setChecked(True)
            else:
                cb.setChecked(False) 
            self.attr_checkboxes[key] = cb
            refactor_layout.addWidget(cb, r, c)
            
        self.refactor_group.setLayout(refactor_layout)
        settings_layout.addWidget(self.refactor_group)
        
        # 2. 追加后缀设置
        self.append_suffix_checkbox = QCheckBox("保留/追加数量后缀 (格式: '共X件')")
        self.append_suffix_checkbox.setChecked(True)
        self.append_suffix_checkbox.setToolTip("选中此项将在文本末尾追加'共X件'。\n如果未启用重构，则在原文后追加。\n如果启用了重构，则在重构后的文本后追加。")
        settings_layout.addWidget(self.append_suffix_checkbox)
        
        # 按钮组
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton('开始更改文本内容')
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.run_text_updater)
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.clicked.connect(self.clear_log)

        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_log_btn)

        settings_layout.addLayout(btn_layout)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)
        
        # 日志输出
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setAcceptRichText(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)  # 占用剩余空间
        
        self.setLayout(main_layout)
    
    def select_excel_file(self):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Excel文件", 
            "", 
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.excel_edit.setText(file_path)
    
    def select_dxf_files(self):
        """选择多个DXF文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "选择DXF文件", 
            "", 
            "DXF Files (*.dxf);;All Files (*)"
        )
        if file_paths:
            # 更新文本框显示选中的文件数量
            self.dxf_edit.setText(f"已选择 {len(file_paths)} 个文件")
            # 更新文件列表
            self.dxf_list.clear()
            for file_path in file_paths:
                self.dxf_list.addItem(file_path)
    
    def clear_dxf_list(self):
        """清除DXF文件列表"""
        self.dxf_edit.clear()
        self.dxf_list.clear()
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            "选择输出目录", 
            ""
        )
        if dir_path:
            self.output_edit.setText(dir_path)
    
    def clear_log(self):
        """清空日志"""
        self.log_output.clear()
    
    def add_log(self, text):
        """添加日志信息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {text}"
        self.log_output.append(log_text)
        self.log_output.moveCursor(self.log_output.textCursor().End)
    
    def run_text_updater(self):
        """运行文本内容更改工具"""
        excel_file = self.excel_edit.text().strip()
        dxf_files = [self.dxf_list.item(i).text() for i in range(self.dxf_list.count())]
        
        if not excel_file:
            QMessageBox.warning(self, "输入错误", "请选择Excel文件！")
            return
        
        if not dxf_files:
            QMessageBox.warning(self, "输入错误", "请选择至少一个DXF文件！")
            return
        
        # 检查文件是否存在
        if not os.path.exists(excel_file):
            QMessageBox.warning(self, "输入错误", f"Excel文件不存在: {excel_file}")
            return
        
        for dxf_file in dxf_files:
            if not os.path.exists(dxf_file):
                QMessageBox.warning(self, "输入错误", f"DXF文件不存在: {dxf_file}")
                return
        
        # 禁用按钮
        self.run_btn.setEnabled(False)
        self.excel_btn.setEnabled(False)
        self.dxf_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        
        # 清空日志和更新状态
        self.log_output.clear()
        self.progress.setValue(0)
        self.progress.setFormat("准备处理...")

        # 获取输出目录
        output_dir = self.output_edit.text().strip()
        
        # 获取模式参数
        refactor_enabled = self.refactor_group.isChecked()
        refactor_attrs = []
        if refactor_enabled:
            # 按特定顺序收集选中的属性
            attr_keys = ['thickness', 'material', 'material_id', 'name', 'drawing_no', 'total_quantity']
            for key in attr_keys:
                if key in self.attr_checkboxes and self.attr_checkboxes[key].isChecked():
                    refactor_attrs.append(key)
        
        append_suffix = self.append_suffix_checkbox.isChecked()
        
        # 创建工作线程
        self.worker = TextUpdaterWorker(excel_file, dxf_files, output_dir, 
                                        refactor_enabled=refactor_enabled,
                                        refactor_attrs=refactor_attrs,
                                        append_suffix=append_suffix)
        self.worker.progress.connect(self.add_log)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.start()
    
    def on_process_finished(self, success, result):
        """处理完成回调"""
        # 恢复按钮状态
        self.run_btn.setEnabled(True)
        self.excel_btn.setEnabled(True)
        self.dxf_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(True)
        
        if success:
            self.progress.setValue(100)
            self.progress.setFormat("处理完成")
            QMessageBox.information(self, "成功", f"处理完成！\n{result}")
        else:
            self.progress.setValue(0)
            self.progress.setFormat("处理失败")
            QMessageBox.critical(self, "处理失败", f"处理失败：{result}")

class CadMergeTab(QWidget):
    """CAD文件合并选项卡"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # 文件设置组
        file_group = QGroupBox("输入文件")
        file_layout = QVBoxLayout()
        
        # 文件列表显示
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(150)
        file_layout.addWidget(self.file_list)
        
        # 文件操作按钮
        button_layout = QHBoxLayout()
        self.add_files_btn = QPushButton('添加文件')
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_dir_btn = QPushButton('添加目录')
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.remove_selected_btn = QPushButton('移除选中')
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        self.clear_list_btn = QPushButton('清空列表')
        self.clear_list_btn.clicked.connect(self.clear_list)
        
        button_layout.addWidget(self.add_files_btn)
        button_layout.addWidget(self.add_dir_btn)
        button_layout.addWidget(self.remove_selected_btn)
        button_layout.addWidget(self.clear_list_btn)
        file_layout.addLayout(button_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 设置组
        settings_group = QGroupBox("设置")
        settings_layout = QFormLayout()
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        try:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            default_path = os.path.join(desktop_dir, "merged.dxf")
        except Exception:
            default_path = "merged.dxf"
        self.output_edit.setText(default_path)
        self.output_edit.setMinimumWidth(300)
        self.browse_output_btn = QPushButton('浏览')
        self.browse_output_btn.clicked.connect(self.browse_output_file)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.browse_output_btn)
        settings_layout.addRow("输出文件:", output_layout)
        
        # 间距设置
        spacing_layout = QHBoxLayout()
        self.spacing_spin = QDoubleSpinBox()
        self.spacing_spin.setRange(0.0, 10000.0)
        self.spacing_spin.setValue(100.0)
        self.spacing_spin.setSingleStep(10.0)
        spacing_layout.addWidget(self.spacing_spin)
        spacing_layout.addWidget(QLabel('mm'))
        settings_layout.addRow("图纸间距:", spacing_layout)
        
        # 文件名显示设置
        self.show_filenames_checkbox = QCheckBox("显示文件名标注")
        settings_layout.addRow("", self.show_filenames_checkbox)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 执行按钮组
        action_layout = QHBoxLayout()
        self.merge_btn = QPushButton('合并CAD文件')
        self.merge_btn.setMinimumHeight(40)
        self.merge_btn.clicked.connect(self.merge_files)
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.clicked.connect(self.clear_log)
        
        action_layout.addWidget(self.merge_btn)
        action_layout.addWidget(self.clear_log_btn)
        main_layout.addLayout(action_layout)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)
        
        # 日志输出
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setAcceptRichText(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)  # 占用剩余空间
        
        self.setLayout(main_layout)
        
        # 初始化输入文件列表
        self.input_files = []
    
    def add_files(self):
        """添加文件到列表"""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "选择DXF文件", 
            "", 
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if files:
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
                    self.file_list.addItem(os.path.basename(file))
            
            self.add_log(f"已添加 {len(files)} 个文件")
    
    def add_directory(self):
        """添加目录中的所有DXF文件"""
        directory = QFileDialog.getExistingDirectory(self, "选择包含DXF文件的目录")
        if not directory:
            return
        
        added_count = 0
        for filename in os.listdir(directory):
            if filename.lower().endswith('.dxf'):
                file_path = os.path.join(directory, filename)
                if file_path not in self.input_files:
                    self.input_files.append(file_path)
                    self.file_list.addItem(filename)
                    added_count += 1
        
        self.add_log(f"已从目录添加 {added_count} 个DXF文件")
    
    def remove_selected(self):
        """移除选中的文件"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要移除的文件")
            return
        
        # 从后往前删除，避免索引问题
        for item in reversed(selected_items):
            index = self.file_list.row(item)
            del self.input_files[index]
            self.file_list.takeItem(index)
        
        self.add_log(f"已移除 {len(selected_items)} 个文件")
    
    def clear_list(self):
        """清空文件列表"""
        if QMessageBox.question(self, "确认", "确定要清空所有文件吗？") == QMessageBox.Yes:
            self.input_files.clear()
            self.file_list.clear()
            self.add_log("已清空所有文件")
    
    def browse_output_file(self):
        """浏览输出文件"""
        file = QFileDialog.getSaveFileName(
            self, 
            "保存合并文件", 
            self.output_edit.text(), 
            "DXF Files (*.dxf);;All Files (*)"
        )[0]
        if file:
            self.output_edit.setText(file)
    
    def clear_log(self):
        """清空日志"""
        self.log_output.clear()
    
    def add_log(self, text):
        """添加日志信息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {text}"
        self.log_output.append(log_text)
        self.log_output.moveCursor(self.log_output.textCursor().End)
    
    def merge_files(self):
        """执行合并操作"""
        # 检查输入文件
        if not self.input_files:
            QMessageBox.warning(self, "错误", "请先添加要合并的DXF文件")
            return
        
        # 检查输出文件
        output_path = self.output_edit.text().strip()
        if not output_path:
            QMessageBox.warning(self, "错误", "请设置输出文件名")
            return
        
        try:
            # 禁用按钮
            self.merge_btn.setEnabled(False)
            self.add_files_btn.setEnabled(False)
            self.add_dir_btn.setEnabled(False)
            self.remove_selected_btn.setEnabled(False)
            self.clear_list_btn.setEnabled(False)
            self.browse_output_btn.setEnabled(False)
            self.clear_log_btn.setEnabled(False)
            
            # 清空日志和更新状态
            self.log_output.clear()
            self.progress.setValue(0)
            self.progress.setFormat("准备处理...")
            
            # 获取参数
            spacing = self.spacing_spin.value()
            show_filenames = self.show_filenames_checkbox.isChecked()
            
            # 创建工作线程
            self.worker = CadMergeWorker(
                self.input_files, 
                output_path, 
                spacing,
                show_filenames
            )
            self.worker.progress.connect(self.add_log)
            self.worker.finished.connect(self.on_merge_finished)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"合并失败: {str(e)}")
            # 恢复按钮状态
            self.restore_buttons()
    
    def on_merge_finished(self, success, result):
        """合并完成回调"""
        # 恢复按钮状态
        self.restore_buttons()
        
        if success:
            self.progress.setValue(100)
            self.progress.setFormat("合并完成")
            QMessageBox.information(self, "成功", f"合并完成！\n{result}")
        else:
            self.progress.setValue(0)
            self.progress.setFormat("合并失败")
            QMessageBox.critical(self, "错误", result)
    
    def restore_buttons(self):
        """恢复按钮状态"""
        self.merge_btn.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.add_dir_btn.setEnabled(True)
        self.remove_selected_btn.setEnabled(True)
        self.clear_list_btn.setEnabled(True)
        self.browse_output_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(True)

class DxfDwgConverterWorker(QThread):
    """DXF/DWG 转换线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, converter, input_files, output_dir, target_format, version='ACAD2018'):
        super().__init__()
        self.converter = converter
        self.input_files = input_files
        self.output_dir = output_dir
        self.target_format = target_format # 'DWG' or 'DXF' or 'DXF_VERSION'
        self.version = version
        
    def run(self):
        try:
            self.progress.emit(f"开始转换 {len(self.input_files)} 个文件...")
            self.progress.emit(f"目标格式: {self.target_format}")
            
            if self.target_format == 'DXF_VERSION':
                 success, msg = self.converter.convert_dxf_version(self.input_files, self.output_dir, self.version)
            elif self.target_format == 'PDF':
                 self.progress.emit("使用引擎: AutoCAD (COM) - PlotToDevice")
                 success, msg = self.converter.convert_to_pdf(self.input_files, self.output_dir)
            else:
                 self.progress.emit("使用引擎: AutoCAD (COM)")
                 success, msg = self.converter.convert_with_autocad(self.input_files, self.output_dir, self.target_format)
            
            self.progress.emit(msg)
            self.finished.emit(success, msg)
            
        except Exception as e:
            self.progress.emit(f"错误: {str(e)}")
            self.finished.emit(False, str(e))

class DxfDwgConverterTab(QWidget):
    """DXF/DWG 转换选项卡"""
    def __init__(self):
        super().__init__()
        from dxf_dwg_converter import DxfDwgConverter
        self.converter = DxfDwgConverter()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        status_layout = QVBoxLayout()
        
        # 检测AutoCAD
        has_autocad = self.converter.check_autocad_available()
        
        if has_autocad:
            autocad_info = QLabel("已检测到 AutoCAD，将使用 AutoCAD COM 接口进行转换。")
            autocad_info.setStyleSheet("color: green;")
            status_layout.addWidget(autocad_info)
        else:
            # 修改提示信息，因为我们不再自动启动 AutoCAD
            error_info = QLabel("提示: 未检测到运行中的 AutoCAD。转换时将尝试自动启动。")
            error_info.setStyleSheet("color: orange; font-weight: bold;")
            status_layout.addWidget(error_info)
             
        main_layout.addLayout(status_layout)

        self._external_exe_path = _find_local_exe("CAD格式转换器.exe")
        external_row = QHBoxLayout()
        external_converter_label = QLabel("CAD多功能格式转换")
        external_converter_label.setStyleSheet("color: #01579b; background-color: #fbc02d; padding: 6px 12px; border-radius: 8px; font-weight: bold;")
        external_row.addWidget(external_converter_label)
        external_row.addStretch(1)
        self.external_open_btn = QPushButton("打开")
        self.external_open_btn.clicked.connect(self.open_external_converter)
        external_row.addWidget(self.external_open_btn)
        main_layout.addLayout(external_row)
        
        # 文件设置
        file_group = QGroupBox("文件转换")
        file_layout = QFormLayout()
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_btn = QPushButton('选择文件')
        self.input_btn.clicked.connect(self.select_input_files)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.input_btn)
        file_layout.addRow("输入文件:", input_layout)
        
        # 输出目录
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_btn = QPushButton('选择输出目录')
        self.output_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_btn)
        file_layout.addRow("输出目录:", output_layout)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 转换设置
        settings_group = QGroupBox("转换设置")
        settings_layout = QHBoxLayout()
        
        # 目标格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(['DXF 转 DWG', 'DWG 转 DXF', 'DXF 版本转换', 'DXF/DWG 转 PDF'])
        self.format_combo.currentIndexChanged.connect(self.on_format_changed)
        settings_layout.addWidget(QLabel("转换模式:"))
        settings_layout.addWidget(self.format_combo)
        
        # 版本
        self.version_combo = QComboBox()
        self.version_combo.addItems(['ACAD2018', 'ACAD2013', 'ACAD2010', 'ACAD2007', 'ACAD2004', 'ACAD2000', 'ACAD12'])
        settings_layout.addWidget(QLabel("目标版本:"))
        settings_layout.addWidget(self.version_combo)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton('开始转换')
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self.run_conversion)
        self.clear_log_btn = QPushButton('清空日志')
        self.clear_log_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_log_btn)
        main_layout.addLayout(btn_layout)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)
        
        # 日志
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)
        
        self.setLayout(main_layout)
        self.input_files = []

    def select_input_files(self):
        mode = self.format_combo.currentIndex()
        if mode == 1: # DWG -> DXF
            filter_str = "DWG Files (*.dwg)"
        elif mode == 3: # DXF/DWG -> PDF
            filter_str = "CAD Files (*.dxf *.dwg)"
        else: # DXF -> DWG or DXF -> DXF
            filter_str = "DXF Files (*.dxf)"
            
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", f"{filter_str};;All Files (*)")
        if files:
            self.input_files = files
            self.input_edit.setText(f"已选择 {len(files)} 个文件")
            # 默认输出目录
            if not self.output_edit.text():
                self.output_edit.setText(os.path.dirname(files[0]))
    
    def on_format_changed(self, index):
        # Clear selection if format changes because extension mismatch
        self.input_files = []
        self.input_edit.clear()
        
    def select_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if d:
            self.output_edit.setText(d)
            
    def clear_log(self):
        self.log_output.clear()
        
    def add_log(self, text):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {text}")
        
    def run_conversion(self):
        if not self.input_files:
            QMessageBox.warning(self, "提示", "请选择输入文件")
            return
            
        output_dir = self.output_edit.text()
        if not output_dir:
            QMessageBox.warning(self, "提示", "请选择输出目录")
            return
            
        mode = self.format_combo.currentIndex() # 0: DXF->DWG, 1: DWG->DXF, 2: DXF->DXF, 3: DXF/DWG->PDF
        
        if mode == 0:
            target_format = 'DWG'
        elif mode == 1:
            target_format = 'DXF'
        elif mode == 3:
            target_format = 'PDF'
        else:
            target_format = 'DXF_VERSION'
            
        version = self.version_combo.currentText()
        
        # 检查依赖
        if (target_format == 'DWG' or target_format == 'DXF' or target_format == 'PDF'):
             # 允许在转换时启动 AutoCAD
             if not self.converter.check_autocad_available(allow_create=True):
                  QMessageBox.critical(self, "错误", "无法启动 AutoCAD COM 接口。请安装并启动 AutoCAD。")
                  return
            
        self.run_btn.setEnabled(False)
        self.progress.setValue(0)
        self.progress.setFormat("正在转换...")
        
        self.worker = DxfDwgConverterWorker(self.converter, self.input_files, output_dir, target_format, version)
        self.worker.progress.connect(self.add_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def on_finished(self, success, msg):
        self.run_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "成功", "转换完成")
            self.progress.setValue(100)
            self.progress.setFormat("转换完成")
        else:
            QMessageBox.critical(self, "失败", f"转换失败: {msg}")
            self.progress.setValue(0)
            self.progress.setFormat("转换失败")

    def open_external_converter(self):
        self._external_exe_path = _find_local_exe("CAD格式转换器.exe")
        p = self._external_exe_path
        if not p or not os.path.exists(p):
            QMessageBox.warning(self, "提示", "未找到 CAD格式转换器.exe，请确认已打包到程序里面。")
            return
        try:
            import subprocess
            subprocess.Popen([p], cwd=os.path.dirname(p))
        except Exception as e:
            QMessageBox.critical(self, "失败", f"启动失败: {str(e)}")

class SolidEdgeNestingWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    def __init__(self, input_file, output_dir, use_quantity_text, default_quantity, nesting_exe_path=None, auto_launch=False, auto_exec=False, command_template="", sheet_width=2440.0, sheet_height=1220.0, allow_rotate=True, contour_only=False):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.use_quantity_text = use_quantity_text
        self.default_quantity = default_quantity
        self.nesting_exe_path = nesting_exe_path
        self.auto_launch = auto_launch
        self.auto_exec = auto_exec
        self.command_template = command_template
        self.sheet_width = float(sheet_width)
        self.sheet_height = float(sheet_height)
        self.allow_rotate = bool(allow_rotate)
        self.contour_only = bool(contour_only)
    def run(self):
        try:
            self.progress.emit("开始生成2D Nesting包...")
            import ezdxf
            from ezdxf import bbox
            from ezdxf.math import Matrix44
            import re
            import math
            import csv
            if not os.path.exists(self.input_file):
                raise FileNotFoundError(f"输入文件不存在: {self.input_file}")
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir, exist_ok=True)
            doc = ezdxf.readfile(self.input_file)
            msp = doc.modelspace()
            materials = []
            thicknesses = []
            finishes = []
            
            def clean_mtext_label(text):
                """Clean MTEXT formatting codes (duplicated for label extraction scope)"""
                if not text: return ""
                s = text
                s = s.replace(r'\P', ' ')
                s = re.sub(r'(\\[ACcFfHhLlOopQTW][^;]*;|\{[^;]*;|\})', '', s)
                s = s.replace('\\', '')
                return s.strip()

            # Cache for block definition content
            block_content_cache = {}

            def get_block_content(blk_name):
                """Scan block definition for material/thickness/finish texts. Returns (mat_list, thick_list, fin_list)."""
                if blk_name in block_content_cache:
                    return block_content_cache[blk_name]
                
                m_list = []
                t_list = []
                f_list = []
                if blk_name in doc.blocks:
                    blk = doc.blocks.get(blk_name)
                    for be in blk:
                        if be.dxftype() in ('TEXT', 'MTEXT'):
                            txt = clean_mtext_label(be.dxf.text)
                            # Check Material
                            m_mat = re.match(r'^材质\s*[:：]?\s*(.+)$', txt)
                            if m_mat:
                                val = m_mat.group(1).strip()
                                if val: m_list.append((val, be.dxf.insert))
                            
                            # Check Thickness
                            m_thick = re.match(r'^厚度\s*[:：]?\s*(.+)$', txt)
                            if m_thick:
                                val = m_thick.group(1).strip()
                                if val: t_list.append((val, be.dxf.insert))

                            # Check Finish
                            m_fin = re.match(r'^(表面|[Ff]inish)\s*[:：]?\s*(.+)$', txt)
                            if m_fin:
                                val = m_fin.group(2).strip()
                                if val: f_list.append((val, be.dxf.insert))
                            elif txt.upper() in ['HL', 'NO.4', '2B', 'BA', 'MIRROR', 'HAIRLINE', 'NO4']:
                                f_list.append((txt, be.dxf.insert))
                
                block_content_cache[blk_name] = (m_list, t_list, f_list)
                return m_list, t_list, f_list

            for e in msp:
                try:
                    text_val = ""
                    insert_point = None
                    
                    if e.dxftype() == 'TEXT':
                        text_val = e.dxf.text
                        insert_point = e.dxf.insert
                    elif e.dxftype() == 'MTEXT':
                        text_val = e.dxf.text
                        insert_point = e.dxf.insert
                    elif e.dxftype() == 'INSERT':
                        # 1. Check attributes in INSERT (Block Reference)
                        if hasattr(e, 'attribs'):
                            for attrib in e.attribs:
                                t_attr = clean_mtext_label(attrib.dxf.text)
                                tag = attrib.dxf.tag.lower() if hasattr(attrib.dxf, 'tag') else ""
                                
                                # Check Material (Tag or Value)
                                val = ""
                                if re.search(r'(材质|material|mat)', tag):
                                    val = t_attr
                                else:
                                    m_mat = re.match(r'^材质\s*[:：]?\s*(.+)$', t_attr)
                                    if m_mat: val = m_mat.group(1).strip()
                                
                                if val:
                                    pos = attrib.dxf.insert
                                    materials.append((val, pos[0], pos[1]))
                                    self.progress.emit(f"找到属性材质: {val} (Tag: {tag})")

                                # Check Thickness (Tag or Value)
                                val = ""
                                if re.search(r'(厚度|thickness|thk)', tag):
                                    val = t_attr
                                else:
                                    m_thick = re.match(r'^厚度\s*[:：]?\s*(.+)$', t_attr)
                                    if m_thick: val = m_thick.group(1).strip()
                                
                                if val:
                                    pos = attrib.dxf.insert
                                    thicknesses.append((val, pos[0], pos[1]))
                                    self.progress.emit(f"找到属性厚度: {val} (Tag: {tag})")

                                # Check Finish (Tag or Value)
                                val = ""
                                if re.search(r'(表面|finish|surf)', tag):
                                    val = t_attr
                                else:
                                    m_fin = re.match(r'^(表面|[Ff]inish)\s*[:：]?\s*(.+)$', t_attr)
                                    if m_fin: val = m_fin.group(2).strip()
                                    elif t_attr.upper() in ['HL', 'NO.4', '2B', 'BA', 'MIRROR', 'HAIRLINE', 'NO4']:
                                        val = t_attr
                                
                                if val:
                                    pos = attrib.dxf.insert
                                    finishes.append((val, pos[0], pos[1]))
                                    self.progress.emit(f"找到属性表面: {val} (Tag: {tag})")
                        
                        # 2. Check content inside Block Definition
                        # Transform local coordinates to world coordinates
                        b_mats, b_thicks, b_fins = get_block_content(e.dxf.name)
                        
                        # Matrix for transformation
                        try:
                            tx = e.dxf.insert[0]
                            ty = e.dxf.insert[1]
                            sx = e.dxf.xscale if hasattr(e.dxf, 'xscale') else 1.0
                            sy = e.dxf.yscale if hasattr(e.dxf, 'yscale') else 1.0
                            rz = e.dxf.rotation if hasattr(e.dxf, 'rotation') else 0.0
                            m = Matrix44.scale(sx, sy, 1.0) @ Matrix44.z_rotate(math.radians(rz)) @ Matrix44.translate(tx, ty, 0)
                            
                            for (val, local_pos) in b_mats:
                                # transform local_pos
                                p = m.transform(local_pos)
                                materials.append((val, p[0], p[1]))
                                # self.progress.emit(f"找到块内材质: {val}")
                                
                            for (val, local_pos) in b_thicks:
                                p = m.transform(local_pos)
                                thicknesses.append((val, p[0], p[1]))
                                # self.progress.emit(f"找到块内厚度: {val}")

                            for (val, local_pos) in b_fins:
                                p = m.transform(local_pos)
                                finishes.append((val, p[0], p[1]))
                        except Exception as ex:
                            pass
                            
                        continue
                    else:
                        continue
                        
                    if not text_val:
                        continue
                        
                    if not text_val:
                        continue
                        
                    # Clean text
                    t = clean_mtext_label(text_val)
                    
                    # Match "材质" (Material)
                    # Support: 材质:xxx, 材质：xxx, 材质 xxx
                    m_mat = re.match(r'^材质\s*[:：]?\s*(.+)$', t)
                    if m_mat:
                        val = m_mat.group(1).strip()
                        if val:
                            materials.append((val, insert_point[0], insert_point[1]))
                            self.progress.emit(f"找到材质标签: {val} at ({insert_point[0]:.1f}, {insert_point[1]:.1f})")
                            continue

                    # Match "厚度" (Thickness)
                    # Support: 厚度:xxx, 厚度：xxx, 厚度 xxx
                    m_thick = re.match(r'^厚度\s*[:：]?\s*(.+)$', t)
                    if m_thick:
                        val = m_thick.group(1).strip()
                        if val:
                            thicknesses.append((val, insert_point[0], insert_point[1]))
                            self.progress.emit(f"找到厚度标签: {val} at ({insert_point[0]:.1f}, {insert_point[1]:.1f})")
                            continue

                    # Match "表面" (Finish)
                    m_fin = re.match(r'^(表面|[Ff]inish)\s*[:：]?\s*(.+)$', t)
                    if m_fin:
                        val = m_fin.group(2).strip()
                        if val:
                            finishes.append((val, insert_point[0], insert_point[1]))
                            self.progress.emit(f"找到表面标签: {val} at ({insert_point[0]:.1f}, {insert_point[1]:.1f})")
                            continue
                    elif t.upper() in ['HL', 'NO.4', '2B', 'BA', 'MIRROR', 'HAIRLINE', 'NO4']:
                        finishes.append((t, insert_point[0], insert_point[1]))
                        self.progress.emit(f"找到表面标签(常用): {t} at ({insert_point[0]:.1f}, {insert_point[1]:.1f})")
                        continue
                            
                except Exception:
                    continue
            
            if not materials:
                self.progress.emit("警告: 未找到任何材质标签！")
            if not thicknesses:
                self.progress.emit("警告: 未找到任何厚度标签！")
            
            def get_nearest_label(target_x, target_y, labels):
                """Find the label spatially closest to the target point (Euclidean distance)"""
                if not labels:
                    return None
                # labels item structure: (text_value, x, y)
                # Sort by Euclidean distance: sqrt((x1-x2)^2 + (y1-y2)^2)
                # math.hypot calculates sqrt(dx*dx + dy*dy) efficiently
                labels_sorted = sorted(labels, key=lambda it: math.hypot(it[1]-target_x, it[2]-target_y))
                return labels_sorted[0]
            
            def normalize_thickness_str(s):
                if not s:
                    return s
                ss = str(s).strip()
                m = re.search(r'(\d+(?:\.\d+)?)', ss)
                if m:
                    num = m.group(1)
                    if num.endswith('.0'):
                        num = num[:-2]
                    return f"T{num}"
                if ss.upper().startswith('T'):
                    return ss.upper()
                return ss

            groups = {}
            idx = 0
            for e in msp:
                try:
                    if e.dxftype() != 'INSERT':
                        continue
                    blk_name = e.dxf.name
                    if blk_name.startswith('*'):
                        continue
                    
                    # Get insertion point (X, Y)
                    # Use Bounding Box Center if possible, fallback to insertion point
                    try:
                        extents = bbox.extents([e])
                        min_pt, max_pt = extents.extmin, extents.extmax
                        tx = (min_pt[0] + max_pt[0]) / 2.0
                        ty = (min_pt[1] + max_pt[1]) / 2.0
                    except Exception:
                        # Fallback to insertion point if bbox fails (e.g. empty block)
                        tx = e.dxf.insert[0]
                        ty = e.dxf.insert[1]
                    
                    # Prefer labels from the current block reference first
                    local_materials = []
                    local_thicknesses = []
                    local_finishes = []
                    try:
                        if hasattr(e, 'attribs'):
                            for attrib in e.attribs:
                                t_attr = attrib.dxf.text if hasattr(attrib.dxf, 'text') else ""
                                tag = attrib.dxf.tag.lower() if hasattr(attrib.dxf, 'tag') else ""
                                if t_attr:
                                    mm = re.match(r'^材质\s*[:：]?\s*(.+)$', t_attr) if not re.search(r'(材质|material|mat)', tag) else None
                                    mt = re.match(r'^厚度\s*[:：]?\s*(.+)$', t_attr) if not re.search(r'(厚度|thickness|thk)', tag) else None
                                    mf = re.match(r'^(表面|[Ff]inish)\s*[:：]?\s*(.+)$', t_attr) if not re.search(r'(表面|finish|surf)', tag) else None
                                    if re.search(r'(材质|material|mat)', tag):
                                        local_materials.append((t_attr.strip(), attrib.dxf.insert[0], attrib.dxf.insert[1]))
                                    elif mm:
                                        local_materials.append((mm.group(1).strip(), attrib.dxf.insert[0], attrib.dxf.insert[1]))
                                    if re.search(r'(厚度|thickness|thk)', tag):
                                        local_thicknesses.append((t_attr.strip(), attrib.dxf.insert[0], attrib.dxf.insert[1]))
                                    elif mt:
                                        local_thicknesses.append((mt.group(1).strip(), attrib.dxf.insert[0], attrib.dxf.insert[1]))
                                    if re.search(r'(表面|finish|surf)', tag):
                                        local_finishes.append((t_attr.strip(), attrib.dxf.insert[0], attrib.dxf.insert[1]))
                                    elif mf:
                                        local_finishes.append((mf.group(2).strip(), attrib.dxf.insert[0], attrib.dxf.insert[1]))
                                    else:
                                        t_upper = str(t_attr).strip().upper()
                                        if t_upper in ['HL', 'NO.4', '2B', 'BA', 'MIRROR', 'HAIRLINE', 'NO4']:
                                            local_finishes.append((t_upper, attrib.dxf.insert[0], attrib.dxf.insert[1]))
                    except Exception:
                        pass
                    try:
                        b_mats, b_thicks, b_fins = get_block_content(e.dxf.name)
                        sx = e.dxf.xscale if hasattr(e.dxf, 'xscale') else 1.0
                        sy = e.dxf.yscale if hasattr(e.dxf, 'yscale') else 1.0
                        rz = e.dxf.rotation if hasattr(e.dxf, 'rotation') else 0.0
                        tx0 = e.dxf.insert[0]
                        ty0 = e.dxf.insert[1]
                        mtx = Matrix44.scale(sx, sy, 1.0) @ Matrix44.z_rotate(math.radians(rz)) @ Matrix44.translate(tx0, ty0, 0)
                        for (val, lp) in b_mats:
                            p = mtx.transform(lp)
                            local_materials.append((str(val).strip(), p[0], p[1]))
                        for (val, lp) in b_thicks:
                            p = mtx.transform(lp)
                            local_thicknesses.append((str(val).strip(), p[0], p[1]))
                        for (val, lp) in b_fins:
                            p = mtx.transform(lp)
                            v = str(val).strip()
                            local_finishes.append((v, p[0], p[1]))
                    except Exception:
                        pass
                    
                    # Determine labels with local-first strategy
                    t_label = get_nearest_label(tx, ty, local_thicknesses if local_thicknesses else thicknesses)
                    m_label = get_nearest_label(tx, ty, local_materials if local_materials else materials)
                    f_label = get_nearest_label(tx, ty, local_finishes if local_finishes else finishes)
                    
                    thick_val = t_label[0] if t_label else "未知厚度"
                    mat_val = m_label[0] if m_label else "未知材质"
                    
                    if f_label:
                        fin_val = f_label[0]
                        # Append finish if valid and not already part of the name
                        if fin_val and fin_val not in mat_val:
                             # Avoid double underscores if mat_val ends with _
                            if mat_val.endswith('_') or mat_val.endswith(' '):
                                mat_val = f"{mat_val.strip()}{fin_val}"
                            else:
                                mat_val = f"{mat_val}_{fin_val}"
                    
                    attr_map = {}
                    if hasattr(e, 'attribs'):
                        try:
                            for attrib in e.attribs:
                                tag = str(attrib.dxf.tag).strip() if hasattr(attrib.dxf, 'tag') else ""
                                val = attrib.dxf.text if hasattr(attrib.dxf, 'text') else ""
                                if tag:
                                    attr_map[tag] = str(val).strip()
                        except Exception:
                            pass
                    attr_mat = attr_map.get('材质', '')
                    attr_thick = attr_map.get('厚度', '')
                    if attr_mat:
                        mat_val = attr_mat
                    if attr_thick:
                        thick_val = attr_thick

                    thick_val = normalize_thickness_str(thick_val)
                    key = (mat_val, thick_val)
                    if key not in groups:
                        groups[key] = []
                    qty = self.default_quantity
                    qty_locked = False
                    try:
                        qty_text = (
                            attr_map.get('总数量')
                            or attr_map.get('total_qty')
                            or attr_map.get('TOTAL_QTY')
                            or attr_map.get('总数')
                            or attr_map.get('数量')
                            or attr_map.get('QTY')
                            or attr_map.get('Qty')
                        )
                        if qty_text:
                            s_qty = str(qty_text).strip().replace(',', '')
                            m_qty = re.search(r'(\d+)', s_qty)
                            if m_qty:
                                qty = max(1, int(m_qty.group(1)))
                                qty_locked = True
                    except Exception:
                        pass
                    idx += 1

                    # Define sanitization helper
                    def sanitize_fn(s):
                        s = str(s)
                        if not s:
                            return ""
                            
                        # Try to convert Chinese to Pinyin
                        try:
                            from pypinyin import lazy_pinyin
                            # Convert to pinyin list, preserving non-Chinese characters
                            pinyin_list = lazy_pinyin(s)
                            s = "".join(pinyin_list)
                        except ImportError:
                            pass
                        except Exception:
                            pass

                        # 1. Replace invalid filesystem chars with underscore
                        s = re.sub(r'[\\/:*?"<>|]', '_', s)
                        # 2. Replace whitespace with underscore
                        s = re.sub(r'\s+', '_', s)
                        # 3. Remove non-ASCII characters (including Chinese if pinyin failed)
                        s = re.sub(r'[^\x00-\x7F]+', '', s)
                        # 4. Keep only alphanumeric, dash, dot, underscore
                        s = re.sub(r'[^a-zA-Z0-9_\-.]', '_', s)
                        # 5. Cleanup underscores
                        s = re.sub(r'_+', '_', s).strip('_')
                        # 6. Fallback if empty
                        if not s:
                            import uuid
                            s = f"unknown_{str(uuid.uuid4())[:8]}"
                        return s
                        
                    safe_mat_val = sanitize_fn(mat_val)
                    safe_thick_val = sanitize_fn(thick_val)

                    # Collect candidate texts
                    candidate_texts = []
                    
                    # Prepare validation values for filtering
                    valid_mat = mat_val if "未知" not in mat_val else ""
                    valid_thick = thick_val if "未知" not in thick_val else ""
                    
                    def clean_mtext(text):
                        """Clean MTEXT formatting codes"""
                        if not text: return ""
                        s = text
                        # 1. Replace line breaks \P with space
                        s = s.replace(r'\P', ' ')
                        # 2. Remove formatting sequences like \f...; \H...; \C...; \A...;
                        # Also handles the {fSimSun...; content} case mentioned by user
                        # Regex explanation:
                        # \\(?:...) : Match backslash followed by specific format chars
                        # [^;]*;    : Match content up to semicolon
                        # |         : OR
                        # \{[^;]*;  : Match opening brace followed by content and semicolon (e.g. {fSimSun...;)
                        # |         : OR
                        # \}        : Match closing brace
                        s = re.sub(r'(\\[ACcFfHhLlOopQTW][^;]*;|\{[^;]*;|\})', '', s)
                        # 3. Remove remaining backslashes if they look like escape codes (simple approach)
                        s = s.replace('\\', '')
                        return s.strip()

                    def process_txt(txt):
                        if not txt: return
                        # Clean MTEXT formatting first
                        txt = clean_mtext(txt)
                        if not txt: return
                        
                        # Check quantity (extract but don't keep the text if it's just quantity)
                        if (not qty_locked) and self.use_quantity_text and '共' in txt and '件' in txt:
                            m = re.search(r'共\s*(\d+)\s*件', txt)
                            if m:
                                nonlocal qty
                                qty = max(1, int(m.group(1)))
                            # Continue to check if we should keep this text
                        
                        # Filter strictly metadata keywords
                        if any(k in txt for k in ['材质', '厚度']):
                            return
                            
                        # Remove "共X件" from text to see what remains
                        clean_txt = re.sub(r'共\s*\d+\s*件', '', txt).strip()
                        if not clean_txt:
                            return
                            
                        # --- Redundancy Filtering ---
                        txt_lower = clean_txt.lower().replace(' ', '')
                        
                        # 1. Contains both Material and Thickness (High confidence junk like "06Cr19Ni10 T1.5 2件_套")
                        if valid_mat and valid_thick:
                            m_clean = valid_mat.lower().replace(' ', '')
                            t_clean = valid_thick.lower().replace(' ', '')
                            if m_clean in txt_lower and t_clean in txt_lower:
                                return
                                
                        # 2. Is exactly Material or Thickness (or close to it)
                        if valid_mat:
                            m_clean = valid_mat.lower().replace(' ', '')
                            if txt_lower == m_clean: return
                        if valid_thick:
                            t_clean = valid_thick.lower().replace(' ', '')
                            if txt_lower == t_clean: return
                            
                        # 3. Pure Quantity strings (e.g. "2件", "14件_套", "2件套")
                        # Matches: Number followed by '件' or '套', optionally followed by more chars like '_套'
                        if re.match(r'^[\d\.]+\s*[件套](_?[件套])?$', clean_txt):
                            return
                        
                        candidate_texts.append(clean_txt)

                    # 1. ATTRIB
                    if hasattr(e, 'attribs'):
                        for attrib in e.attribs:
                            process_txt(attrib.dxf.text)
                            
                    # 2. BLOCK
                    if blk_name in doc.blocks:
                        try:
                            blk = doc.blocks.get(blk_name)
                            for be in blk:
                                if be.dxftype() in ('TEXT', 'MTEXT'):
                                    process_txt(be.dxf.text)
                        except Exception:
                            pass

                    # Remove duplicates while preserving order
                    candidate_texts = list(dict.fromkeys(candidate_texts))
                    
                    # Identify Material ID and Name
                    material_id_str = ""
                    name_parts = []
                    drawing_num_str = ""
                    
                    for txt in candidate_texts:
                        # Improved Heuristic for Material ID:
                        # 1. Must contain at least 8 digits
                        # 2. Can contain hyphens '-' or parentheses '()'
                        # 3. Format: e.g. 101002002316, 248060000-1, (248010420-1)
                        digit_count = sum(c.isdigit() for c in txt)
                        is_id_format = bool(re.match(r'^[\(\d][\d\-\)\s]*$', txt))
                        
                        if is_id_format and digit_count >= 8 and not material_id_str:
                             material_id_str = txt
                        else:
                             name_parts.append(txt)
                             
                    part_name_str = "_".join(name_parts)
                    if not part_name_str:
                        # Fallback
                        safe_blk = sanitize_fn(blk_name)
                        if not safe_blk.startswith('*'):
                             part_name_str = safe_blk
                        else:
                             part_name_str = f"part_{idx}"
                    
                    attr_id = attr_map.get('物料ID', '')
                    attr_name = attr_map.get('名称', '')
                    attr_draw = attr_map.get('图号', '')
                    
                    use_id = attr_id if attr_id else material_id_str
                    use_name = attr_name if attr_name else part_name_str
                    use_draw = attr_draw if attr_draw else drawing_num_str
                    
                    fname_parts = [
                        sanitize_fn(thick_val),
                        sanitize_fn(mat_val),
                        sanitize_fn(use_id),
                        sanitize_fn(use_name),
                        sanitize_fn(use_draw)
                    ]
                    
                    final_filename = "_".join(fname_parts)
                    if not any(p for p in fname_parts):
                        final_filename = f"part_{idx}"

                    group_dir = os.path.join(self.output_dir, safe_mat_val, safe_thick_val)
                    os.makedirs(group_dir, exist_ok=True)
                    out_path = os.path.join(group_dir, f"{final_filename}.dxf")
                    new_doc = ezdxf.new(dxfversion='R2010')
                    new_msp = new_doc.modelspace()
                    if blk_name in doc.blocks:
                        blk = doc.blocks.get(blk_name)
                        sx = e.dxf.xscale if hasattr(e.dxf, 'xscale') else 1.0
                        sy = e.dxf.yscale if hasattr(e.dxf, 'yscale') else 1.0
                        rz = e.dxf.rotation if hasattr(e.dxf, 'rotation') else 0.0
                        
                        # Fix: Use radians for rotation and remove translation to keep at origin
                        m = Matrix44.scale(sx, sy, 1.0) @ Matrix44.z_rotate(math.radians(rz))
                        
                        def export_entities(layout, transform_matrix, target_msp):
                            for entity in layout:
                                try:
                                    dxftype = entity.dxftype()
                                    if self.contour_only and dxftype in ('TEXT', 'MTEXT', 'DIMENSION', 'LEADER', 'MLEADER', 'POINT', 'ATTDEF'):
                                        continue
                                        
                                    if dxftype == 'INSERT':
                                        # Handle nested block
                                        nested_name = entity.dxf.name
                                        if nested_name in doc.blocks:
                                            nested_blk = doc.blocks.get(nested_name)
                                            
                                            # Nested transformation
                                            nsx = entity.dxf.xscale if hasattr(entity.dxf, 'xscale') else 1.0
                                            nsy = entity.dxf.yscale if hasattr(entity.dxf, 'yscale') else 1.0
                                            nsz = entity.dxf.zscale if hasattr(entity.dxf, 'zscale') else 1.0
                                            nrz = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0
                                            nins = entity.dxf.insert
                                            
                                            local_m = Matrix44.scale(nsx, nsy, nsz) @ \
                                                      Matrix44.z_rotate(math.radians(nrz)) @ \
                                                      Matrix44.translate(nins[0], nins[1], nins[2])
                                            
                                            combined_m = local_m @ transform_matrix
                                            export_entities(nested_blk, combined_m, target_msp)
                                    else:
                                        # Regular entity
                                        ce = entity.copy()
                                        ce.transform(transform_matrix)
                                        target_msp.add_entity(ce)
                                except Exception:
                                    continue
                        
                        export_entities(blk, m, new_msp)
                    new_doc.saveas(out_path)
                    groups[key].append((out_path, qty))
                    self.progress.emit(f"已导出部件: {os.path.basename(out_path)} x{qty} -> {mat_val}/{thick_val}")
                except Exception:
                    continue
            
            # Helper to sanitize folder names
            def sanitize_filename(name):
                name = str(name)
                if not name:
                    return ""
                
                # Try to convert Chinese to Pinyin
                try:
                    from pypinyin import lazy_pinyin
                    pinyin_list = lazy_pinyin(name)
                    name = "".join(pinyin_list)
                except ImportError:
                    pass
                except Exception:
                    pass

                name = re.sub(r'[\\/:*?"<>|]', '_', name)
                name = re.sub(r'\s+', '_', name)
                name = re.sub(r'[^\x00-\x7F]+', '', name) # Remove non-ASCII
                name = re.sub(r'[^a-zA-Z0-9_\-.]', '_', name)
                name = re.sub(r'_+', '_', name).strip('_')
                if not name:
                    import uuid
                    name = f"unknown_{str(uuid.uuid4())[:8]}"
                return name

            total_parts = 0
            
            # Store launch tasks to be executed after all files are generated
            launch_tasks = []
            
            for (mat, thick), items in groups.items():
                # Sanitize material and thickness for folder names
                safe_mat = sanitize_filename(mat)
                safe_thick = sanitize_filename(thick)
                
                csv_dir = os.path.join(self.output_dir, safe_mat, safe_thick)
                # Ensure the directory exists (it should have been created in previous loop if names match)
                if not os.path.exists(csv_dir):
                     os.makedirs(csv_dir, exist_ok=True)
                     
                # 生成 nest_parts.csv (Standard Format for Nesting)
                nest_csv = os.path.join(csv_dir, "nest_parts.csv")
                try:
                    # 使用 ANSI 编码，确保 Windows 软件（如 Solid Edge）能正确读取路径
                    # 不写入表头，防止软件将表头误读为数据
                    # 严格按照报错提示的列顺序：Part Name, File Path, Quantity, Rotation, Allow Mirror(0/1), Priority(0-6)
                    with open(nest_csv, 'w', newline='', encoding='mbcs') as f:
                        writer = csv.writer(f)
                        
                        for fn, q in items:
                            part_name = os.path.splitext(os.path.basename(fn))[0]
                            abs_path = os.path.abspath(fn)
                            priority = 1
                            rotation = 90 if self.allow_rotate else 0
                            mirror = 0
                            # Part Name, File Path, Quantity, Rotation, Mirror, Priority
                            writer.writerow([part_name, abs_path, q, rotation, mirror, priority])
                            
                    self.progress.emit(f"排版清单: {mat}/{thick} -> {nest_csv}")
                except Exception as e:
                    self.progress.emit(f"生成排版清单失败: {str(e)}")

                if self.nesting_exe_path:
                    try:
                        # 1. 生成 BAT 启动脚本 (保留供用户手动使用)
                        bat_path = os.path.join(csv_dir, "RunNesting.bat")
                        ps1_path = os.path.join(csv_dir, "AutoNest.ps1")
                        
                        # PowerShell 内容：使用 System.Windows.Forms.SendKeys 进行 Tab 遍历点击
                        ps1_content = """
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$targetTitle = "CAD File Importer"
$maxRetries = 20
$found = $false

Write-Host "Searching for window: $targetTitle..."

# 1. 尝试找到并激活窗口
For ($i=0; $i -lt $maxRetries; $i++) {
    $window = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
        [System.Windows.Automation.TreeScope]::Children,
        (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $targetTitle))
    )

    If ($window -ne $null) {
        Write-Host "Window found! Activating..."
        $found = $true
        try { $window.SetFocus() } catch {}
        Start-Sleep -Milliseconds 500
        
        # 2. 暴力 Tab 遍历策略
        # 有些界面默认焦点不在按钮上，通过循环 Tab + Enter 遍历所有可能
        Write-Host "Starting Tab-Loop strategy..."
        
        # 先尝试直接 Enter
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
        Start-Sleep -Milliseconds 500
        
        # 循环 8 次：Tab -> Enter
        For ($j=0; $j -lt 8; $j++) {
            Write-Host "Tab loop $j..."
            [System.Windows.Forms.SendKeys]::SendWait("{TAB}")
            Start-Sleep -Milliseconds 200
            [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
            Start-Sleep -Milliseconds 500
        }
        
        # 最后尝试 Alt+S
        Write-Host "Sending Alt+S..."
        [System.Windows.Forms.SendKeys]::SendWait("%s")
        
        Break
    }
    Start-Sleep -Seconds 1
}

If (-not $found) {
    Write-Host "Window '$targetTitle' not found."
    # 最后的盲试
    try { 
        $wshell = New-Object -ComObject WScript.Shell
        $wshell.AppActivate("Solid Edge 2D Nesting")
        Start-Sleep -Milliseconds 500
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    } catch {}
}
"""
                        # 使用 utf-8-sig (带BOM) 编码
                        with open(ps1_path, 'w', encoding='utf-8-sig') as pf:
                            pf.write(ps1_content)

                        # BAT 仅作为用户手动备用
                        with open(bat_path, 'w', encoding='mbcs') as bf:
                            exe_path = os.path.abspath(self.nesting_exe_path)
                            bf.write(f'@echo off\n')
                            bf.write(f'echo Starting Automation...\n')
                            bf.write(f'start "" powershell -ExecutionPolicy Bypass -File "{os.path.abspath(ps1_path)}"\n')
                            bf.write(f'echo Starting Solid Edge...\n')
                            bf.write(f'"{exe_path}" "{os.path.abspath(nest_csv)}"\n')

                        self.progress.emit(f"生成启动脚本: {bat_path}")
                        
                        if self.auto_launch:
                            # Store the launch task instead of executing it immediately
                            launch_tasks.append((mat, thick, csv_dir, ps1_path, nest_csv))
                            
                    except Exception as e:
                        self.progress.emit(f"生成启动脚本失败: {str(e)}")

                total_parts += len(items)

            # Execute launch tasks sequentially after all files are generated
            if self.auto_launch and launch_tasks:
                import subprocess
                self.progress.emit(f"\n开始启动排版软件 (共 {len(launch_tasks)} 组)...")
                
                for i, (mat, thick, csv_dir, ps1_path, nest_csv) in enumerate(launch_tasks, 1):
                    self.progress.emit(f"[{i}/{len(launch_tasks)}] 正在启动排版软件 ({mat}/{thick})...")
                    self.progress.emit("请在操作完成后关闭软件以继续下一组。")
                    
                    try:
                        # 1. 启动 PowerShell 自动化脚本 (后台运行，隐藏窗口)
                        # CREATE_NO_WINDOW = 0x08000000
                        creation_flags = 0x08000000
                        ps_cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", os.path.abspath(ps1_path)]
                        subprocess.Popen(ps_cmd, cwd=csv_dir, creationflags=creation_flags)
                        
                        # 2. 启动 Solid Edge (阻塞等待)
                        exe_cmd = [self.nesting_exe_path, os.path.abspath(nest_csv)]
                        subprocess.call(exe_cmd, cwd=csv_dir)
                        
                        self.progress.emit(f"已完成该组排版: {mat}/{thick}")
                    except Exception as e:
                        self.progress.emit(f"启动失败 ({mat}/{thick}): {str(e)}")

            self.finished.emit(True, f"处理完成，共导出 {total_parts} 个部件")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(False, str(e))
class SolidEdgeNestingTab(QWidget):
    """Solid Edge 2D Nesting 排版包生成"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    def init_ui(self):
        main_layout = QVBoxLayout()
        file_group = QGroupBox("输入/输出")
        file_layout = QFormLayout()
        in_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setMinimumWidth(300)
        self.input_btn = QPushButton("选择合并DXF")
        self.input_btn.clicked.connect(self.select_input_file)
        in_layout.addWidget(self.input_edit)
        in_layout.addWidget(self.input_btn)
        file_layout.addRow("合并DXF文件:", in_layout)
        out_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        try:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            default_dir = os.path.join(desktop_dir, "nest_package")
        except Exception:
            default_dir = "nest_package"
        self.output_edit.setText(default_dir)
        self.output_edit.setMinimumWidth(300)
        self.output_btn = QPushButton("选择输出目录")
        self.output_btn.clicked.connect(self.select_output_dir)
        out_layout.addWidget(self.output_edit)
        out_layout.addWidget(self.output_btn)
        file_layout.addRow("输出目录:", out_layout)
        exe_layout = QHBoxLayout()
        self.exe_edit = QLineEdit()
        self.exe_edit.setMinimumWidth(300)
        
        # Load saved path
        self.settings = QSettings("CADToolkit", "SolidEdgeNesting")
        saved_exe_path = self.settings.value("nesting_exe_path", "")
        if saved_exe_path and os.path.exists(saved_exe_path):
            self.exe_edit.setText(saved_exe_path)
            
        self.exe_btn = QPushButton("浏览")
        self.exe_btn.clicked.connect(self.select_exe_file)
        exe_layout.addWidget(self.exe_edit)
        exe_layout.addWidget(self.exe_btn)
        file_layout.addRow("排版软件路径:", exe_layout)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        settings_group = QGroupBox("设置")
        settings_layout = QFormLayout()
        self.auto_launch_checkbox = QCheckBox("生成后启动排版软件")
        self.auto_launch_checkbox.setChecked(True)
        settings_layout.addRow("", self.auto_launch_checkbox)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        action_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成排版包")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.clicked.connect(self.generate_package)
        self.open_dir_btn = QPushButton("打开输出目录")
        self.open_dir_btn.clicked.connect(self.open_output_dir)
        action_layout.addWidget(self.generate_btn)
        action_layout.addWidget(self.open_dir_btn)
        main_layout.addLayout(action_layout)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("准备就绪")
        main_layout.addWidget(self.progress)
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_output.setAcceptRichText(True)
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)
        self.setLayout(main_layout)
    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择合并DXF", "", "DXF Files (*.dxf);;All Files (*)")
        if file_path:
            self.input_edit.setText(file_path)
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录", "")
        if dir_path:
            self.output_edit.setText(dir_path)
    def select_exe_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择排版软件", "", "Executable (*.exe);;All Files (*)")
        if file_path:
            self.exe_edit.setText(file_path)
            # Save path
            self.settings.setValue("nesting_exe_path", file_path)
    def add_log(self, text):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {text}")
        self.log_output.moveCursor(self.log_output.textCursor().End)
    def generate_package(self):
        input_file = self.input_edit.text().strip()
        output_dir = self.output_edit.text().strip()
        if not input_file:
            QMessageBox.warning(self, "错误", "请选择合并DXF文件")
            return
        if not output_dir:
            QMessageBox.warning(self, "错误", "请选择输出目录")
            return
        self.generate_btn.setEnabled(False)
        self.open_dir_btn.setEnabled(False)
        self.log_output.clear()
        self.progress.setValue(0)
        self.progress.setFormat("正在生成...")
        
        # 使用默认值
        use_qty = True
        default_qty = 1
        sheet_w = 2440.0
        sheet_h = 1220.0
        allow_rotate = True
        contour_only = False

        exe_path = self.exe_edit.text().strip()
        auto_launch = self.auto_launch_checkbox.isChecked()
        
        self.worker = SolidEdgeNestingWorker(input_file, output_dir, use_qty, default_qty, nesting_exe_path=exe_path, auto_launch=auto_launch, auto_exec=False, command_template="", sheet_width=sheet_w, sheet_height=sheet_h, allow_rotate=allow_rotate, contour_only=contour_only)
        self.worker.progress.connect(self.add_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    def on_finished(self, success, msg):
        self.generate_btn.setEnabled(True)
        self.open_dir_btn.setEnabled(True)
        if success:
            self.progress.setValue(100)
            self.progress.setFormat("已生成")
            QMessageBox.information(self, "完成", f"生成完成！\n{msg}")
        else:
            self.progress.setValue(0)
            self.progress.setFormat("失败")
            QMessageBox.critical(self, "失败", f"生成失败：{msg}")
    def open_output_dir(self):
        out_dir = self.output_edit.text().strip()
        if os.path.exists(out_dir):
            import subprocess
            try:
                subprocess.Popen(f'explorer "{out_dir}"')
            except Exception:
                pass

class FeaturesDialog(QDialog):
    """功能介绍对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CAD工具包功能介绍")
        self.resize(900, 700)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("CAD工具包功能详解")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #0277bd; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 内容区域
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        # 使用更现代的样式
        self.browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                padding: 20px;
                font-family: "Microsoft YaHei", "Segoe UI";
                font-size: 11pt;
                line-height: 1.6;
            }
        """)
        
        # HTML内容
        html_content = """
        <style>
            h3 { color: #0277bd; margin-top: 25px; margin-bottom: 8px; font-size: 14pt; }
            p { margin-bottom: 10px; color: #444444; line-height: 1.5; }
            ul { margin-top: 0px; margin-bottom: 15px; padding-left: 20px; }
            li { margin-bottom: 6px; color: #555555; }
            .highlight { color: #e65100; font-weight: bold; background-color: #fff3e0; padding: 2px 4px; border-radius: 3px; }
            .section-box { border-bottom: 1px solid #eeeeee; padding-bottom: 10px; }
        </style>
        
        <div class="section-box">
            <h3>1. BOM数量计算</h3>
            <p>快速统计BOM表中各组件的总需求量，解决手工计算繁琐易错的问题。</p>
            <ul>
                <li><b>操作：</b>选择Excel文件 -> 点击"开始计算"。</li>
                <li><b>输出：</b>生成包含总数量的新Excel文件，自动计算组件数量。</li>
            </ul>
        </div>

        <div class="section-box">
            <h3>2. 块筛寻和合并</h3>
            <p>根据Excel清单，从多个CAD文件中智能提取特定块并合并到新图纸中。</p>
            <ul>
                <li><b>核心功能：</b>支持自动提取<span class="highlight">材质、厚度、物料ID、名称、图号、总数量</span>等属性。</li>
                <li><b>智能布局：</b>按材质和厚度自动分组排列，支持自定义块间距和组间距。</li>
            </ul>
        </div>

        <div class="section-box">
            <h3>3. 块批量导出</h3>
            <p>将复杂的CAD图纸拆分为独立的块文件，便于管理和复用。</p>
            <ul>
                <li><b>应用场景：</b>建立标准件库。</li>
                <li><b>核心功能：</b>支持添加<span class="highlight">材质、板厚、物料ID、名称、图号</span>等属性。</li>
            </ul>
        </div>

        <div class="section-box">
            <h3>4. 批量块创建</h3>
            <p>将散乱的图形对象转换为标准的CAD块，实现标准化绘图。</p>
            <ul>
                <li><b>属性同步：</b>支持从Excel读取属性并写入块定义（材质、名称、图号、总数量等）。</li>
                <li><b>命名策略：</b>自动提取图形内的文本作为块名，支持多种命名规则。</li>
            </ul>
        </div>

        <div class="section-box">
            <h3>5. CAD文件合并</h3>
            <p>将多个独立的DXF文件拼合到一张图纸中，便于集中打印或查看。</p>
            <ul>
                <li><b>灵活排版：</b>支持按中心对齐或按边距对齐。</li>
            </ul>
        </div>

        <div class="section-box">
            <h3>6. 文本内容更改</h3>
            <p>批量更新图纸中的文本信息，支持重构和追加两种模式。</p>
            <ul>
                <li><b>文本重构：</b>根据Excel数据完全重写文本（如格式化为"材质-厚度-ID"）。</li>
                <li><b>追加模式：</b>仅在原有文本后追加数量信息（如"共X件"）。</li>
            </ul>
        </div>

        <div class="section-box">
            <h3>7. DXF/DWG 转换</h3>
            <p>实现不同CAD格式间的无缝转换。</p>
            <ul>
                <li><b>兼容性：</b>支持AutoCAD COM接口，确保高保真转换，CAD格式转换器支持多种文件转化。</li>
            </ul>
        </div>

        <div class="section-box">
            <h3>8. 2D Nesting 排版</h3>
            <p>为Solid Edge Nesting等套料软件准备标准数据。</p>
            <ul>
                <li><b>自动化：</b>一键生成导入清单(CSV)和批处理脚本，大幅提高排版效率。</li>
            </ul>
        </div>
        """
        self.browser.setHtml(html_content)
        layout.addWidget(self.browser)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(120, 40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        # 按钮样式
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0277bd;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #01579b;
            }
            QPushButton:pressed {
                background-color: #004c8c;
            }
        """)
        
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        
        # 初始化通知管理器
        if NOTIFICATION_ENABLED:
            self.notification_manager = NotificationManager(
                api_url=NOTIFICATION_CONFIG['api_url'],
                cache_file=NOTIFICATION_CONFIG['cache_file']
            )
        else:
            self.notification_manager = None
        
        self.init_ui()
        
        # 初始化通知和更新系统
        if NOTIFICATION_ENABLED:
            self.init_notification_system()
            self.init_update_system()
    
    def init_ui(self):
        # 设置窗口标题和大小
        version_text = f"CAD工具包 v{APP_VERSION}" if NOTIFICATION_ENABLED else "CAD工具包 v3.8"
        self.setWindowTitle(version_text)
        try:
            screen = QApplication.primaryScreen()
            if screen:
                rect = screen.availableGeometry()
                target_w = min(1200, int(rect.width() * 0.95))
                target_h = min(800, int(rect.height() * 0.9))
                self.resize(target_w, target_h)
                self.move(
                    rect.x() + max(0, (rect.width() - target_w) // 2),
                    rect.y() + max(0, (rect.height() - target_h) // 2),
                )
            else:
                self.resize(1200, 800)
        except Exception:
            self.resize(1200, 800)
        
        # 创建菜单
        self.create_menu()
        
        # 主布局容器
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. 侧边栏
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFocusPolicy(Qt.NoFocus)
        
        # 侧边栏样式微调 (覆盖全局样式以适应特定需求 - 明亮主题版)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border-right: 1px solid #d0d0d0;
                border-top: none;
                border-bottom: none;
                border-left: none;
                padding-top: 10px;
                outline: none;
            }
            QListWidget::item {
                height: 50px;
                padding-left: 20px;
                color: #666666;
                font-size: 11pt;
                border-left: 3px solid transparent;
            }
            QListWidget::item:selected {
                background-color: #e1f5fe;
                color: #0277bd;
                border-left: 3px solid #0277bd;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #e0e0e0;
                color: #333333;
            }
        """)
        
        # 添加侧边栏项
        nav_items = [
            ("BOM数量计算", "bom"),
            ("块批量导出", "export"),
            ("CAD块创建", "create"),
            ("块筛寻合并", "find"),
            ("CAD文件合并", "merge"),
            ("文本内容更改", "text"),
            ("DXF/DWG 转换", "convert"),
            ("2D Nesting 排版", "nest")
        ]
        
        for name, icon_name in nav_items:
            # 这里可以添加图标，目前只用文字
            item = self.sidebar.addItem(name)
            
        self.sidebar.currentRowChanged.connect(self.change_page)
        
        # 2. 内容区域
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        # 标题栏
        self.title_label = QLabel("BOM数量计算")
        self.title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        self.title_label.setStyleSheet("color: #0277bd; margin-bottom: 10px;")
        content_layout.addWidget(self.title_label)
        
        # 堆叠窗口
        self.stacked_widget = QStackedWidget()
        
        # 创建页面
        self.bom_tab = BOMCalculatorTab()
        self.export_tab = ExportBlocksTab()
        self.creator_tab = BlockCreatorTab()
        self.finder_tab = BlockFinderTab()
        self.merge_tab = CadMergeTab()
        self.text_updater_tab = TextUpdaterTab()
        self.converter_tab = DxfDwgConverterTab()
        self.nesting_tab = SolidEdgeNestingTab()
        
        # 添加页面到堆叠窗口
        self.stacked_widget.addWidget(self.bom_tab)
        self.stacked_widget.addWidget(self.export_tab)
        self.stacked_widget.addWidget(self.creator_tab)
        self.stacked_widget.addWidget(self.finder_tab)
        self.stacked_widget.addWidget(self.merge_tab)
        self.stacked_widget.addWidget(self.text_updater_tab)
        self.stacked_widget.addWidget(self.converter_tab)
        self.stacked_widget.addWidget(self.nesting_tab)
        
        content_layout.addWidget(self.stacked_widget)
        
        # 将侧边栏和内容区域添加到主布局
        main_layout.addWidget(self.sidebar)
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setWidget(content_widget)
        self.content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(self.content_scroll, 1)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # 默认选中第一项
        self.sidebar.setCurrentRow(0)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 添加通知小部件到状态栏
        if NOTIFICATION_ENABLED and self.notification_manager:
            self.notification_widget = NotificationWidget(self.notification_manager, self)
            self.statusBar().addPermanentWidget(self.notification_widget)
        
    def change_page(self, index):
        """切换页面"""
        self.stacked_widget.setCurrentIndex(index)
        # 更新标题
        item = self.sidebar.item(index)
        if item:
            self.title_label.setText(item.text())
    
    def create_menu(self):
        """创建菜单"""
        menubar = self.menuBar()
        
        # 帮助菜单
        help_menu = menubar.addMenu("&帮助")
        
        # 检查更新菜单项
        if NOTIFICATION_ENABLED:
            check_update_action = QAction("检查更新(&U)", self)
            check_update_action.setStatusTip("检查软件更新")
            check_update_action.triggered.connect(self.manual_check_update)
            help_menu.addAction(check_update_action)
            
            # 通知中心菜单项
            notification_action = QAction("通知中心(&N)", self)
            notification_action.setStatusTip("查看所有通知")
            notification_action.triggered.connect(self.show_notification_center)
            help_menu.addAction(notification_action)
            
            help_menu.addSeparator()
        
        # 功能介绍菜单项
        features_action = QAction("&功能介绍", self)
        features_action.setStatusTip("显示各模块功能介绍")
        features_action.triggered.connect(self.show_features)
        help_menu.addAction(features_action)
        
       
    
    def show_features(self):
        """显示功能介绍对话框"""
        dialog = FeaturesDialog(self)
        dialog.exec_()
    
    # ==================== 消息推送和更新系统方法 ====================
    
    def init_notification_system(self):
        """初始化通知系统"""
        if not NOTIFICATION_CONFIG['enabled'] or not self.notification_manager:
            return
        
        # 首次获取通知
        self.fetch_notifications()
        
        # 设置定时器定期检查
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.fetch_notifications)
        self.notification_timer.start(NOTIFICATION_CONFIG['check_interval'] * 1000)
    
    def fetch_notifications(self):
        """获取通知"""
        if not self.notification_manager:
            return
        
        try:
            # 保存线程引用，防止被垃圾回收
            self.notification_fetcher = NotificationFetcher(NOTIFICATION_CONFIG['api_url'])
            self.notification_fetcher.notifications_received.connect(self.on_notifications_received)
            self.notification_fetcher.error_occurred.connect(self.on_notification_error)
            self.notification_fetcher.start()
        except Exception as e:
            print(f"获取通知失败: {e}")
    
    def on_notifications_received(self, notifications):
        """收到通知"""
        if self.notification_manager:
            self.notification_manager.notifications = notifications
            if hasattr(self, 'notification_widget'):
                self.notification_widget.update_badge()
    
    def on_notification_error(self, error_msg):
        """通知获取失败"""
        print(f"获取通知失败: {error_msg}")
    
    def show_notification_center(self):
        """显示通知中心"""
        if not self.notification_manager:
            QMessageBox.information(self, "提示", "通知系统未启用")
            return
        
        try:
            from notification_system import NotificationDialog
            dialog = NotificationDialog(self.notification_manager, self)
            dialog.exec_()
            if hasattr(self, 'notification_widget'):
                self.notification_widget.update_badge()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开通知中心失败:\n{e}")
    
    def init_update_system(self):
        """初始化更新系统"""
        if not UPDATE_CONFIG['enabled']:
            return
        
        # 启动时检查更新（延迟3秒）
        if UPDATE_CONFIG['check_on_startup']:
            QTimer.singleShot(3000, self.check_update)
        
        # 设置定时器定期检查
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_update)
        self.update_timer.start(UPDATE_CONFIG['auto_check_interval'] * 1000)
    
    def check_update(self, silent=True):
        """检查更新"""
        try:
            # 保存线程引用，防止被垃圾回收
            self.update_checker = UpdateChecker(
                api_url=UPDATE_CONFIG['api_url'],
                current_version=APP_VERSION
            )
            self.update_checker.update_available.connect(
                lambda info: self.on_update_available(info, silent)
            )
            self.update_checker.no_update.connect(
                lambda: self.on_no_update(silent)
            )
            self.update_checker.error_occurred.connect(
                lambda err: self.on_update_error(err, silent)
            )
            self.update_checker.start()
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, "错误", f"检查更新失败:\n{e}")
    
    def manual_check_update(self):
        """手动检查更新"""
        self.check_update(silent=False)
    
    def on_update_available(self, update_info, silent):
        """有可用更新"""
        # 检查是否跳过此版本
        import json
        
        config_file = UPDATE_CONFIG['config_file']
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    skipped_version = config.get('skipped_version', '')
                    if skipped_version == update_info.get('version'):
                        if not silent:
                            QMessageBox.information(self, "检查更新", 
                                                   "当前已是最新版本（已跳过的版本）")
                        return
            except:
                pass
        
        # 显示更新对话框
        try:
            dialog = UpdateDialog(update_info, APP_VERSION, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"显示更新对话框失败:\n{e}")
    
    def on_no_update(self, silent):
        """无可用更新"""
        if not silent:
            QMessageBox.information(self, "检查更新", "当前已是最新版本")
    
    def on_update_error(self, error_msg, silent):
        """更新检查失败"""
        if not silent:
            QMessageBox.warning(self, "检查更新", f"检查更新失败:\n{error_msg}")

if __name__ == '__main__':
    # 确保中文显示正常
    app = QApplication(sys.argv)
    
    # 应用现代明亮主题 (根据用户请求: 颜色改为白色)
    try:
        from ui_styles import get_modern_light_style
        app.setStyleSheet(get_modern_light_style())
    except ImportError:
        print("未找到样式文件，使用默认样式")
        app.setStyle('Fusion')
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    print("初始化GUI界面...")
    window = MainWindow()
    print("显示GUI窗口...")
    window.show()
    print("进入事件循环...")
    sys.exit(app.exec_())
