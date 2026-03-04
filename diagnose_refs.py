
import os
import ezdxf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_broken_references(search_dir):
    logger.info(f"Scanning {search_dir} for broken block references...")
    
    total_files = 0
    broken_files = 0
    
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.lower().endswith('.dxf'):
                file_path = os.path.join(root, file)
                total_files += 1
                
                try:
                    doc = ezdxf.readfile(file_path)
                    block_names = set(block.name.upper() for block in doc.blocks)
                    
                    broken_refs = []
                    
                    # 1. Check Modelspace
                    msp = doc.modelspace()
                    for entity in msp:
                        if entity.dxftype() == 'INSERT':
                            if entity.dxf.name.upper() not in block_names:
                                broken_refs.append(f"Modelspace INSERT: {entity.dxf.name}")
                                
                    # 2. Check Paperspace
                    for layout in doc.layouts:
                        if layout.name == 'Model': continue
                        for entity in layout:
                            if entity.dxftype() == 'INSERT':
                                if entity.dxf.name.upper() not in block_names:
                                    broken_refs.append(f"Paperspace ({layout.name}) INSERT: {entity.dxf.name}")
                                    
                    # 3. Check Block Definitions (Nested Blocks)
                    for block in doc.blocks:
                        for entity in block:
                            if entity.dxftype() == 'INSERT':
                                if entity.dxf.name.upper() not in block_names:
                                    broken_refs.append(f"Block ({block.name}) INSERT: {entity.dxf.name}")
                    
                    if broken_refs:
                        broken_files += 1
                        logger.error(f"Broken references in {file}:")
                        # Show first 10
                        for ref in broken_refs[:10]:
                            logger.error(f"  - {ref}")
                        if len(broken_refs) > 10:
                            logger.error(f"  ... and {len(broken_refs)-10} more.")
                    else:
                        # logger.info(f"OK: {file}")
                        pass
                        
                except Exception as e:
                    logger.error(f"Error reading {file}: {e}")

    logger.info(f"Scan complete. Found broken references in {broken_files} out of {total_files} files.")

if __name__ == "__main__":
    check_broken_references('cad')
