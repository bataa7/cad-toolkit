import os
import ezdxf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def clean_broken_refs(target_dir):
    logger.info(f"Scanning {target_dir} to REMOVE broken refs...")
    
    files_cleaned = 0
    total_removed = 0
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.dxf'):
                file_path = os.path.join(root, file)
                try:
                    doc = ezdxf.readfile(file_path)
                    
                    block_names = set(b.name.upper() for b in doc.blocks)
                    
                    # We need to collect entities to delete first
                    to_delete_layouts = [] # (layout, entity)
                    to_delete_blocks = [] # (block, entity)
                    
                    # Scan Layouts
                    for layout in doc.layouts:
                        for entity in layout:
                            if entity.dxftype() == 'INSERT':
                                if entity.dxf.name.upper() not in block_names:
                                    to_delete_layouts.append((layout, entity))
                                    
                    # Scan Blocks
                    for block in doc.blocks:
                        for entity in block:
                            if entity.dxftype() == 'INSERT':
                                if entity.dxf.name.upper() not in block_names:
                                    to_delete_blocks.append((block, entity))
                                    
                    if not to_delete_layouts and not to_delete_blocks:
                        continue
                        
                    count = len(to_delete_layouts) + len(to_delete_blocks)
                    logger.info(f"File: {file} - Removing {count} broken references.")
                    
                    for layout, entity in to_delete_layouts:
                        layout.delete_entity(entity)
                        
                    for block, entity in to_delete_blocks:
                        block.delete_entity(entity)
                        
                    doc.save()
                    files_cleaned += 1
                    total_removed += count
                    
                except Exception as e:
                    logger.error(f"Error cleaning {file_path}: {e}")

    logger.info(f"Cleanup complete. Removed {total_removed} refs in {files_cleaned} files.")

if __name__ == "__main__":
    clean_broken_refs('cad')
