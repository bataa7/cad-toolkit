import ezdxf
import os
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_dxf(filename):
    if not os.path.exists(filename):
        logger.error(f"File not found: {filename}")
        return

    try:
        doc = ezdxf.readfile(filename)
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return

    logger.info(f"Analyzing {filename}...")
    
    def _get_attrib_value(insert, tag):
        for attrib in getattr(insert, "attribs", []):
            if attrib.dxf.tag == tag:
                return attrib.dxf.text
        return None

    def _normalize_text(value):
        if value is None:
            return None
        return str(value).strip()

    # 1. Block Definitions
    block_names = [b.name for b in doc.blocks if not b.name.startswith('*')]
    logger.info(f"Total user blocks: {len(block_names)}")
    
    # Check for similar names
    name_groups = defaultdict(list)
    for name in block_names:
        # Group by prefix (before $ or _v)
        base = name.split('$')[0].split('_v')[0]
        name_groups[base].append(name)
        
    duplicates = {k: v for k, v in name_groups.items() if len(v) > 1}
    if duplicates:
        logger.info(f"Found {len(duplicates)} groups of similar block names (potential duplicates):")
        for base, names in list(duplicates.items())[:10]:
            logger.info(f"  {base}: {names}")
            
    # 2. Block References (INSERTs) in ModelSpace
    msp = doc.modelspace()
    inserts = [e for e in msp if e.dxftype() == 'INSERT']
    logger.info(f"Total INSERTs in ModelSpace: {len(inserts)}")
    
    # Count per block
    insert_counts = defaultdict(int)
    for i in inserts:
        insert_counts[i.dxf.name] += 1
        
    logger.info("Top 10 used blocks in ModelSpace:")
    for name, count in sorted(insert_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"  {name}: {count}")

    # 3. Check for broken references
    broken = 0
    for i in inserts:
        if i.dxf.name not in doc.blocks:
            broken += 1
    if broken > 0:
        logger.error(f"Found {broken} BROKEN references in ModelSpace!")

    drawing_map = defaultdict(list)
    for i in inserts:
        drawing_num = _normalize_text(_get_attrib_value(i, "图号"))
        if drawing_num:
            drawing_map[drawing_num].append(i)

    duplicates_by_drawing = {k: v for k, v in drawing_map.items() if len(v) > 1}
    if duplicates_by_drawing:
        logger.info(f"Found {len(duplicates_by_drawing)} drawing numbers used by multiple blocks:")
        for drawing_num, items in list(duplicates_by_drawing.items())[:20]:
            names = [it.dxf.name for it in items]
            logger.info(f"  图号 {drawing_num}: {names}")

    identifier_map = defaultdict(list)
    for i in inserts:
        name = i.dxf.name
        if name.startswith("BLOCK_"):
            parts = name.split("_", 4)
            if len(parts) == 5:
                identifier = _normalize_text(parts[4])
                if identifier:
                    identifier_map[identifier].append(name)

    duplicates_by_identifier = {k: v for k, v in identifier_map.items() if len(v) > 1}
    if duplicates_by_identifier:
        logger.info(f"Found {len(duplicates_by_identifier)} identifiers used by multiple blocks:")
        for identifier, names in list(duplicates_by_identifier.items())[:20]:
            logger.info(f"  标识 {identifier}: {names}")

if __name__ == "__main__":
    import sys
    files = sys.argv[1:] if len(sys.argv) > 1 else ['cad/merged_blocks.dxf', 'cad/merg_blocks.dxf']
    for f in files:
        if os.path.exists(f):
            analyze_dxf(f)
