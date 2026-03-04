#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD文件合并工具 (Robust Version)
使用 ezdxf.addons.Importer 确保完整导入块定义和依赖项，避免断开引用。
"""

import os
import ezdxf
from ezdxf import units
from ezdxf.addons import Importer
from ezdxf.enums import TextEntityAlignment
from typing import List, Tuple, Dict, Any
import traceback

def compute_entities_bbox(entities) -> Tuple[float, float, float, float]:
    """计算实体列表的包围盒"""
    try:
        from ezdxf import bbox
        extents = bbox.extents(entities)
        if extents.has_data:
            return (extents.extmin.x, extents.extmin.y, extents.extmax.x, extents.extmax.y)
    except Exception:
        pass

    # Fallback
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    found = False
    
    for entity in entities:
        try:
            # Skip viewport
            if entity.dxftype() == 'VIEWPORT': continue
            
            points = []
            if hasattr(entity.dxf, 'insert'):
                points.append(entity.dxf.insert)
            elif hasattr(entity.dxf, 'start'):
                points.append(entity.dxf.start)
                points.append(entity.dxf.end)
            elif hasattr(entity.dxf, 'center'):
                c = entity.dxf.center
                r = getattr(entity.dxf, 'radius', 0)
                points.append((c[0]-r, c[1]-r))
                points.append((c[0]+r, c[1]+r))
            elif entity.dxftype() == 'LWPOLYLINE':
                points.extend(entity.get_points())
                
            for p in points:
                px, py = float(p[0]), float(p[1])
                min_x = min(min_x, px)
                min_y = min(min_y, py)
                max_x = max(max_x, px)
                max_y = max(max_y, py)
                found = True
        except Exception:
            continue
            
    if not found:
        return (0.0, 0.0, 0.0, 0.0)
    return (min_x, min_y, max_x, max_y)

def merge_dxf_files(input_files: List[str], output_file: str, spacing: float = 100.0, show_filenames: bool = False) -> None:
    """
    合并多个DXF文件。
    使用 Importer 导入源文件内容到目标文件的各个 Block 中。
    """
    # Create target doc
    doc = ezdxf.new(dxfversion='R2010')
    doc.units = units.MM
    
    # Setup styles/layers
    try:
        doc.header['$DWGCODEPAGE'] = 'ANSI_936'
    except: pass
    
    if 'SimHei' not in doc.styles:
        doc.styles.new('SimHei', dxfattribs={'font': 'simhei.ttf'})
    if 'FILENAME' not in doc.layers:
        doc.layers.new('FILENAME')

    msp = doc.modelspace()
    
    processed_blocks = []
    
    print(f"开始合并 {len(input_files)} 个文件...")
    
    for i, file_path in enumerate(input_files):
        if not os.path.exists(file_path): continue
        
        filename = os.path.basename(file_path)
        print(f"[{i+1}/{len(input_files)}] 处理: {filename}")
        
        try:
            source_doc = ezdxf.readfile(file_path)
            
            # Prepare container block name
            file_base = os.path.splitext(filename)[0]
            safe_base = "".join([c if c.isalnum() or c in '_-' else '_' for c in file_base])
            container_block_name = f"MERGE_{i}_{safe_base}"
            
            # Create container block in target
            container_block = doc.blocks.new(name=container_block_name)
            
            # Initialize Importer
            importer = Importer(source_doc, doc)
            
            # Import ModelSpace entities
            source_msp = source_doc.modelspace()
            src_entities = list(source_msp)
            
            if not src_entities:
                print(f"  文件为空，跳过")
                continue
                
            # Import entities directly to container block
            importer.import_entities(src_entities, target_layout=container_block)
            
            # Finalize to resolve dependencies (blocks, layers, styles)
            importer.finalize()
            
            # Calculate bbox of ORIGINAL entities to determine offset
            min_x, min_y, max_x, max_y = compute_entities_bbox(src_entities)
            width = max_x - min_x
            height = max_y - min_y
            
            if width <= 0 or height <= 0:
                width, height = 100.0, 100.0
                min_x, min_y = 0.0, 0.0
                
            # Shift geometry to align (min_x, min_y) to (0,0)
            # Iterate entities in container_block (which are the ones we just imported)
            for entity in container_block:
                try:
                    entity.translate(-min_x, -min_y, 0)
                except Exception as e:
                    print(f"  无法平移实体 {entity.dxftype()}: {e}")
            
            processed_blocks.append({
                'name': container_block_name,
                'width': width,
                'height': height,
                'filename': filename
            })
            
        except Exception as e:
            print(f"  处理失败: {e}")
            traceback.print_exc()
            
    # Layout blocks
    print(f"开始布局 {len(processed_blocks)} 个图纸...")
    current_x = 0.0
    baseline_y = 0.0
    
    for info in processed_blocks:
        name = info['name']
        w = info['width']
        h = info['height']
        fname = info['filename']
        
        msp.add_blockref(name, (current_x, baseline_y))
        
        if show_filenames:
            label_x = current_x + (w / 2.0)
            label_y = baseline_y - 20.0
            text_height = max(min(w, h) * 0.05, 5.0)
            text_height = min(text_height, 200.0)
            
            msp.add_text(
                _sanitize_text(fname),
                dxfattribs={
                    'height': text_height,
                    'style': 'SimHei',
                    'layer': 'FILENAME'
                }
            ).set_placement((label_x, label_y), align=TextEntityAlignment.TOP_CENTER)
            
        current_x += w + spacing
        
    try:
        doc.saveas(output_file)
        print(f"保存成功: {output_file}")
    except Exception as e:
        print(f"保存失败: {e}")

def _sanitize_text(text: str) -> str:
    if not text: return ""
    # Simple sanitization
    return text.replace('\n', ' ').replace('\r', '')

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python cad_merge.py [files...]")
    else:
        # Simple CLI test
        files = sys.argv[1:]
        merge_dxf_files(files, "merged_test.dxf", show_filenames=True)
