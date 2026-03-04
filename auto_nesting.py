import os
import math
import logging
import re
import ezdxf
from ezdxf import bbox as ezdxf_bbox
from ezdxf.tools.text import plain_text
from typing import List, Dict, Tuple, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CadItem:
    def __init__(self, name: str, width: float, height: float, source_file: str, source_handle: str, 
                 material: str = "Unknown", thickness: str = "Unknown", quantity: int = 1):
        self.name = name
        self.width = width
        self.height = height
        self.source_file = source_file
        self.source_handle = source_handle
        self.material = material
        self.thickness = thickness
        self.quantity = quantity
        self.x = 0.0
        self.y = 0.0
        self.rotated = False

class ShelfPacker:
    def __init__(self, bin_width: float, bin_height: float = None, spacing: float = 10.0):
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.spacing = spacing
        self.current_x = 0.0
        self.current_y = 0.0
        self.shelf_height = 0.0
        self.items: List[CadItem] = []
        self.sheets: List[List[CadItem]] = [] # 支持多张板材
        self.current_sheet_items: List[CadItem] = []

    def add_item(self, item: CadItem):
        # 简单的 Shelf 算法
        # 检查是否需要换行
        if self.current_x + item.width > self.bin_width:
            self.current_y += self.shelf_height + self.spacing
            self.current_x = 0.0
            self.shelf_height = 0.0
        
        # 检查是否需要换板 (如果指定了高度)
        if self.bin_height and (self.current_y + item.height > self.bin_height):
            # 保存当前板
            self.sheets.append(self.current_sheet_items)
            self.current_sheet_items = []
            # 重置坐标
            self.current_x = 0.0
            self.current_y = 0.0
            self.shelf_height = 0.0
        
        item.x = self.current_x
        item.y = self.current_y
        
        self.current_x += item.width + self.spacing
        self.shelf_height = max(self.shelf_height, item.height)
        
        self.current_sheet_items.append(item)
        self.items.append(item)
        
    def finalize(self):
        if self.current_sheet_items:
            self.sheets.append(self.current_sheet_items)
        if not self.sheets and self.items:
             self.sheets.append(self.items)

class AutoNester:
    def __init__(self):
        self.cancel_flag = False

    def _get_bbox(self, entity) -> Tuple[float, float, float, float]:
        """获取实体的边界框 (minx, miny, maxx, maxy)"""
        try:
            extents = ezdxf_bbox.extents([entity])
            return (extents.extmin.x, extents.extmin.y, extents.extmax.x, extents.extmax.y)
        except Exception:
            # 简单的回退逻辑
            if entity.dxftype() == 'LINE':
                return (min(entity.dxf.start[0], entity.dxf.end[0]), min(entity.dxf.start[1], entity.dxf.end[1]),
                        max(entity.dxf.start[0], entity.dxf.end[0]), max(entity.dxf.start[1], entity.dxf.end[1]))
            elif entity.dxftype() == 'CIRCLE':
                r = entity.dxf.radius
                c = entity.dxf.center
                return (c[0]-r, c[1]-r, c[0]+r, c[1]+r)
            return (0,0,0,0)

    def _copy_entity(self, entity, target_block, offset_x: float, offset_y: float):
        """将实体复制到目标块，并应用偏移"""
        try:
            dxftype = entity.dxftype()
            dxfattribs = {}
            # 复制通用属性
            if hasattr(entity.dxf, 'layer'): dxfattribs['layer'] = entity.dxf.layer
            if hasattr(entity.dxf, 'color'): dxfattribs['color'] = entity.dxf.color
            if hasattr(entity.dxf, 'linetype'): dxfattribs['linetype'] = entity.dxf.linetype
            
            if dxftype == 'LINE':
                start = (entity.dxf.start[0] + offset_x, entity.dxf.start[1] + offset_y)
                end = (entity.dxf.end[0] + offset_x, entity.dxf.end[1] + offset_y)
                target_block.add_line(start, end, dxfattribs=dxfattribs)
            elif dxftype == 'CIRCLE':
                center = (entity.dxf.center[0] + offset_x, entity.dxf.center[1] + offset_y)
                target_block.add_circle(center, entity.dxf.radius, dxfattribs=dxfattribs)
            elif dxftype == 'ARC':
                center = (entity.dxf.center[0] + offset_x, entity.dxf.center[1] + offset_y)
                target_block.add_arc(center, entity.dxf.radius, entity.dxf.start_angle, entity.dxf.end_angle, dxfattribs=dxfattribs)
            elif dxftype == 'LWPOLYLINE':
                points = []
                with entity.points() as pts:
                    for p in pts:
                        points.append((p[0] + offset_x, p[1] + offset_y) + tuple(p[2:]))
                target_block.add_lwpolyline(points, format='xyseb', dxfattribs=dxfattribs)
            elif dxftype in ('TEXT', 'MTEXT'):
                insert = (entity.dxf.insert[0] + offset_x, entity.dxf.insert[1] + offset_y)
                dxfattribs['insert'] = insert
                if hasattr(entity.dxf, 'height'): dxfattribs['height'] = entity.dxf.height
                if hasattr(entity.dxf, 'style'): dxfattribs['style'] = entity.dxf.style
                if dxftype == 'TEXT':
                    target_block.add_text(entity.dxf.text, dxfattribs=dxfattribs)
                else:
                    target_block.add_mtext(entity.dxf.text, dxfattribs=dxfattribs)
            # 其他实体类型按需添加
        except Exception as e:
            logger.warning(f"复制实体失败: {e}")

    def collect_items(self, input_dir: str) -> List[CadItem]:
        items = []
        files = []
        if os.path.isfile(input_dir):
            files.append(input_dir)
        elif os.path.isdir(input_dir):
            for f in os.listdir(input_dir):
                if f.lower().endswith('.dxf'):
                    files.append(os.path.join(input_dir, f))
        
        for dxf_path in files:
            try:
                doc = ezdxf.readfile(dxf_path)
                msp = doc.modelspace()
                
                # 收集标签
                combined_labels = [] # (material, thickness, position)
                
                for e in msp:
                    if e.dxftype() in ('TEXT', 'MTEXT'):
                        raw_text = e.dxf.text
                        # 去除格式控制符
                        text = plain_text(raw_text).strip()
                        # 支持中文冒号
                        text = text.replace('：', ':')
                        
                        # 模式1: "材质: xxx"
                        if text.startswith("材质:"):
                            mat = text.split(":", 1)[1].strip()
                            combined_labels.append((mat, "Unknown", e.dxf.insert))
                            continue
                            
                        # 模式2: "厚度: xxx"
                        if text.startswith("厚度:"):
                            thick = text.split(":", 1)[1].strip()
                            combined_labels.append(("Unknown", thick, e.dxf.insert))
                            continue
                            
                        # 模式3: "06Cr19Ni10 T2"
                        # 匹配: 任意非空字符 + 空格 + T + 数字
                        match = re.search(r"(?P<mat>.*?)\s+T(?P<thick>\d+(?:\.\d+)?)", text)
                        if match:
                            mat = match.group("mat").strip()
                            thick = match.group("thick").strip()
                            # 过滤掉包含过多无关信息的匹配（可选）
                            combined_labels.append((mat, thick, e.dxf.insert))

                # 收集块引用
                for e in msp:
                    if e.dxftype() == 'INSERT':
                        insert_pos = e.dxf.insert
                        
                        # 查找最近标签
                        def get_nearest_label(labels, pos, threshold=2000):
                            best_mat = "Unknown"
                            best_thick = "Unknown"
                            min_dist = float('inf')
                            
                            for mat, thick, label_pos in labels:
                                dist = math.hypot(label_pos[0]-pos[0], label_pos[1]-pos[1])
                                if dist < min_dist:
                                    min_dist = dist
                                    best_mat = mat
                                    best_thick = thick
                                    
                            return (best_mat, best_thick) if min_dist < threshold else ("Unknown", "Unknown")

                        mat, thick = get_nearest_label(combined_labels, insert_pos)
                        
                        # 尝试从单独的 materials/thicknesses 列表中查找（如果需要）
                        # 这里简化为只使用 combined_labels，因为看起来文件中主要是这种格式
                        
                        # 获取块尺寸
                        block_name = e.dxf.name
                        if block_name not in doc.blocks:
                            continue
                        block_def = doc.blocks.get(block_name)
                        
                        minx, miny, maxx, maxy = float('inf'), float('inf'), float('-inf'), float('-inf')
                        has_geom = False
                        
                        try:
                            extents = ezdxf_bbox.extents(block_def)
                            width = extents.extmax.x - extents.extmin.x
                            height = extents.extmax.y - extents.extmin.y
                            if width > 0 and height > 0:
                                has_geom = True
                        except:
                            pass
                        
                        if not has_geom:
                            # 粗略估算
                            for ent in block_def:
                                bbox = self._get_bbox(ent)
                                if bbox != (0,0,0,0):
                                    minx = min(minx, bbox[0]); miny = min(miny, bbox[1])
                                    maxx = max(maxx, bbox[2]); maxy = max(maxy, bbox[3])
                                    has_geom = True
                            if has_geom:
                                width = maxx - minx
                                height = maxy - miny
                            else:
                                width, height = 100, 100
                        
                        items.append(CadItem(block_name, width, height, dxf_path, e.dxf.handle, mat, thick))
                        
            except Exception as e:
                logger.error(f"处理文件 {dxf_path} 失败: {e}")
                
        return items

    def _clean_name(self, name: str) -> str:
        # 移除 MTEXT 格式代码 (简单的正则表达式，作为 plain_text 的补充)
        name = re.sub(r"\{.*?;", "", name)
        name = name.replace("}", "")
        # 只保留安全字符
        return re.sub(r'[\\/:*?"<>|\r\n]', '_', name).strip()

    def run(self, input_path: str, output_path: str, sheet_width: float = None, sheet_height: float = None, spacing: float = 10.0, progress_callback=None):
        def log(msg):
            logger.info(msg)
            if progress_callback:
                progress_callback(msg)

        log("开始收集图形...")
        items = self.collect_items(input_path)
        log(f"共收集到 {len(items)} 个图形")
        
        # 缓存源文档，避免重复读取
        source_docs = {}
        unique_source_files = set(item.source_file for item in items)
        log(f"正在缓存 {len(unique_source_files)} 个源文件...")
        for f in unique_source_files:
            if self.cancel_flag: return
            try:
                source_docs[f] = ezdxf.readfile(f)
            except Exception as e:
                logger.error(f"无法缓存文件 {f}: {e}")

        # 分组
        groups = {}
        for item in items:
            key = (item.material, item.thickness)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
            
        # 创建输出文档
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        if 'SimHei' not in doc.styles:
            doc.styles.new('SimHei', dxfattribs={'font': 'simhei.ttf'})
            
        current_y = 0.0
        spacing_y = 500.0 # 组间距
        
        for (mat, thick), group_items in groups.items():
            if self.cancel_flag: return
            log(f"排版组: 材质={mat}, 厚度={thick}, 数量={len(group_items)}")
            
            # 排序：高度降序
            group_items.sort(key=lambda x: x.height, reverse=True)
            
            # 估算宽度 (如果没有指定 sheet_width)
            if sheet_width:
                bin_width = sheet_width
            else:
                total_area = sum(i.width * i.height for i in group_items)
                bin_width = max(2000, math.sqrt(total_area) * 2.0)
            
            packer = ShelfPacker(bin_width, sheet_height, spacing)
            for item in group_items:
                packer.add_item(item)
            packer.finalize()
                
            # 绘制
            # 添加组头标签
            header_text = f"材质: {mat}  厚度: {thick}  (共 {len(packer.sheets)} 张板)"
            msp.add_text(header_text, dxfattribs={
                'insert': (0, current_y + 150), 
                'height': 80, 
                'style': 'SimHei',
                'color': 1
            })
            
            # 遍历每一张板
            sheet_start_y = current_y
            
            for i, sheet_items in enumerate(packer.sheets):
                # 绘制板框 (如果指定了尺寸)
                if sheet_width and sheet_height:
                    msp.add_lwpolyline([(0, sheet_start_y), (sheet_width, sheet_start_y), 
                                      (sheet_width, sheet_start_y - sheet_height), (0, sheet_start_y - sheet_height)], 
                                     dxfattribs={'closed': True, 'color': 2})
                    # 板序号
                    msp.add_text(f"Sheet {i+1}", dxfattribs={
                        'insert': (10, sheet_start_y - 30), 'height': 20, 'color': 2
                    })

                for item in sheet_items:
                    # 在新文档中创建块
                    # 使用文件名和块名作为唯一标识，共享块定义
                    safe_mat = self._clean_name(mat)
                    safe_thick = self._clean_name(thick)
                    safe_filename = self._clean_name(os.path.basename(item.source_file))
                    safe_blockname = self._clean_name(item.name)
                    
                    new_block_name = f"{safe_mat}_{safe_thick}_{safe_filename}_{safe_blockname}"
                    # 截断过长的名称
                    if len(new_block_name) > 200:
                        # 保留最重要的部分：文件名哈希 + 块名
                        import hashlib
                        h = hashlib.md5(safe_filename.encode()).hexdigest()[:8]
                        new_block_name = f"{safe_mat}_{safe_thick}_{h}_{safe_blockname}"
                        if len(new_block_name) > 250:
                             new_block_name = new_block_name[:250]
                    
                    if new_block_name not in doc.blocks:
                        # 读取源文件中的块定义
                        try:
                            if item.source_file not in source_docs:
                                continue
                                
                            src_doc = source_docs[item.source_file]
                            if item.name not in src_doc.blocks:
                                continue
                                
                            src_block = src_doc.blocks.get(item.name)
                            new_block = doc.blocks.new(name=new_block_name)
                            
                            # 复制实体
                            for ent in src_block:
                                self._copy_entity(ent, new_block, 0, 0)
                                
                        except Exception as e:
                            logger.error(f"复制块定义失败 {new_block_name}: {e}")
                            continue
                    
                    # 插入块引用
                    if new_block_name in doc.blocks:
                        insert_x = item.x
                        # 如果有多张板，y坐标是相对于 sheet_start_y 的
                        # item.y 是相对于板顶部的正偏移量
                        insert_y = sheet_start_y - item.y
                        msp.add_blockref(new_block_name, (insert_x, insert_y))
            
                # 如果是多张板，更新 sheet_start_y 为下一张板的位置
                if sheet_height:
                     sheet_start_y -= (sheet_height + 200) # 板间距
                
            # 更新下一组的起始 Y
            if sheet_height:
                 # 使用实际使用的总高度
                 total_group_height = len(packer.sheets) * (sheet_height + 200)
                 current_y -= (total_group_height + spacing_y)
            else:
                 # 旧逻辑
                 group_height = packer.current_y + packer.shelf_height
                 current_y -= (group_height + spacing_y)
            
        doc.saveas(output_path)
        log(f"保存完成: {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CAD 自动排版工具")
    parser.add_argument("-i", "--input", required=True, help="输入文件或目录")
    parser.add_argument("-o", "--output", required=True, help="输出DXF文件")
    args = parser.parse_args()
    
    nester = AutoNester()
    nester.run(args.input, args.output)
