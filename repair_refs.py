import os
import ezdxf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def repair_refs(target_dir):
    logger.info(f"Scanning {target_dir} for broken refs and candidates...")
    
    files_with_issues = 0
    fixed_files = 0
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.dxf'):
                file_path = os.path.join(root, file)
                try:
                    doc = ezdxf.readfile(file_path)
                    
                    # Get all block names (case-insensitive map)
                    # map: UPPER_NAME -> RealName
                    block_map = {b.name.upper(): b.name for b in doc.blocks}
                    
                    broken_refs = []
                    
                    # Scan INSERTs in Modelspace and Paperspace
                    for layout in doc.layouts:
                        for entity in layout:
                            if entity.dxftype() == 'INSERT':
                                name = entity.dxf.name
                                if name.upper() not in block_map:
                                    broken_refs.append(entity)
                                    
                    # Scan INSERTs inside blocks
                    for block in doc.blocks:
                        for entity in block:
                            if entity.dxftype() == 'INSERT':
                                name = entity.dxf.name
                                if name.upper() not in block_map:
                                    broken_refs.append(entity)

                    if not broken_refs:
                        continue
                        
                    unique_broken_names = set(e.dxf.name for e in broken_refs)
                    logger.info(f"File: {file} - Found {len(broken_refs)} broken references ({len(unique_broken_names)} unique names)")
                    
                    changes_made = False
                    
                    # Map broken name -> fix name
                    fix_map = {}
                    
                    for broken in unique_broken_names:
                        # Look for candidates
                        candidates = []
                        prefix = broken.upper() + "_V"
                        for real_upper, real_name in block_map.items():
                            if real_upper.startswith(prefix):
                                # Check if it follows _v<digits> pattern
                                suffix = real_upper[len(prefix):]
                                if suffix.isdigit():
                                    candidates.append(real_name)
                                    
                        if len(candidates) == 1:
                            fix_name = candidates[0]
                            logger.info(f"  [FIXING] '{broken}' -> '{fix_name}'")
                            fix_map[broken] = fix_name
                        elif len(candidates) > 1:
                            logger.warning(f"  [AMBIGUOUS] '{broken}' -> {candidates}")
                        else:
                            logger.warning(f"  [NO CANDIDATE] '{broken}'")
                            
                    # Apply fixes
                    if fix_map:
                        for entity in broken_refs:
                            if entity.dxf.name in fix_map:
                                entity.dxf.name = fix_map[entity.dxf.name]
                                changes_made = True
                                
                    if changes_made:
                        doc.save()
                        logger.info(f"  Saved changes to {file}")
                        fixed_files += 1
                    
                    files_with_issues += 1
                    
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")

    logger.info(f"Repair complete. Fixed {fixed_files} files.")

if __name__ == "__main__":
    repair_refs('cad')
