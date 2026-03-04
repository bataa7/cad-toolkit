
import os
import sys
import logging
import ezdxf
from collections import defaultdict, Counter
from block_finder import BlockFinder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_blocks(target_dir: str):
    finder = BlockFinder()
    
    # 1. Collect all blocks and their fingerprints
    # List of (fingerprint, name, file_path)
    all_blocks = []
    
    # Map: file_path -> list of (block_name, fingerprint)
    file_block_map = defaultdict(list)
    
    files_processed = 0
    if not os.path.exists(target_dir):
        logger.error(f"Directory not found: {target_dir}")
        return

    logger.info("Phase 1: Scanning files and collecting block info...")
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith('.dxf'):
                file_path = os.path.join(root, file)
                try:
                    doc = ezdxf.readfile(file_path)
                    for block in doc.blocks:
                        if hasattr(block, 'is_layout_block'):
                            if block.is_layout_block:
                                continue
                        else:
                            # Fallback check
                            if block.name.upper() in ('*MODEL_SPACE', '*PAPER_SPACE'):
                                continue
                            if block.name.startswith('*Paper_Space'):
                                continue
                        
                        # SKIP Special and Anonymous blocks
                        if block.name.startswith('*') or block.name.startswith('_') or block.name.startswith('$'):
                            # logger.debug(f"Skipping special block: {block.name}")
                            continue
                            
                        fp = finder._get_block_content_key(block)
                        all_blocks.append((fp, block.name, file_path))
                        file_block_map[file_path].append((block.name, fp))
                        
                    files_processed += 1
                except Exception as e:
                    logger.error(f"Error scanning {file_path}: {e}")

    logger.info(f"Scanned {files_processed} files, found {len(all_blocks)} block definitions.")

    # 2. Determine Canonical Names
    # Step 2a: Resolve Name Conflicts (Same Name -> Different Content)
    # Map: Name -> list of fingerprints
    name_to_fps = defaultdict(set)
    for fp, name, _ in all_blocks:
        name_to_fps[name].add(fp)
        
    # Map: (Name, Fingerprint) -> ResolvedName
    resolved_names = {}
    
    for name, fps in name_to_fps.items():
        if len(fps) == 1:
            resolved_names[(name, list(fps)[0])] = name
        else:
            # Conflict! Sort fingerprints to be deterministic
            sorted_fps = sorted(list(fps), key=lambda x: str(x))
            logger.warning(f"Conflict for block name '{name}': {len(fps)} variations.")
            
            for i, fp in enumerate(sorted_fps):
                if i == 0:
                    resolved_names[(name, fp)] = name # Keep original for first
                else:
                    new_name = f"{name}_v{i+1}"
                    resolved_names[(name, fp)] = new_name
                    logger.info(f"  Renaming variation {i+1} to {new_name}")

    # Step 2b: Resolve Content Aliases (Same Content -> Multiple Names)
    # Map: Fingerprint -> CanonicalName
    fp_to_canonical = {}
    
    # Group by fingerprint
    fp_to_names = defaultdict(list)
    for fp, name, _ in all_blocks:
        # Use the resolved name from Step 2a
        r_name = resolved_names.get((name, fp), name)
        fp_to_names[fp].append(r_name)
        
    for fp, names in fp_to_names.items():
        # Pick the most frequent name
        counts = Counter(names)
        most_common = counts.most_common(1)[0][0]
        
        fp_to_canonical[fp] = most_common
        
        if len(counts) > 1:
            logger.info(f"Merging aliases for content {hash(fp)}: {list(counts.keys())} -> {most_common}")

    # 3. Update Files
    logger.info("Phase 3: Updating files with canonical names...")
    updated_files_count = 0
    
    for file_path, blocks in file_block_map.items():
        logger.info(f"Processing {file_path}...")
        try:
            doc = ezdxf.readfile(file_path)
            changed = False
            
            # Group blocks in this file by their Target Canonical Name
            target_groups = defaultdict(list)
            
            for name, fp in blocks:
                if (name, fp) not in resolved_names:
                    continue
                
                final_name = fp_to_canonical[fp]
                target_groups[final_name].append(name)

            # Now execute updates
            for final_name, current_names in target_groups.items():
                unique_currents = list(set(current_names))
                
                survivor_name = None
                
                # Check if final_name exists in current_names
                if final_name in unique_currents:
                    survivor_name = final_name
                else:
                    # Pick the first one as survivor and rename it later
                    survivor_name = unique_currents[0]
                    
                # Merge others into survivor
                for name in unique_currents:
                    if name == survivor_name:
                        continue
                    
                    # Double check safety
                    if name.startswith('_') or name.startswith('*') or name.startswith('$'):
                        logger.warning(f"Skipping merge of special block: {name}")
                        continue

                    logger.info(f"  Merging local block '{name}' into '{survivor_name}' (Target: {final_name})")
                    try:
                        _merge_block_references(doc, name, survivor_name)
                        if name in doc.blocks:
                            doc.blocks.delete_block(name)
                        changed = True
                    except Exception as e:
                        logger.warning(f"  Failed to merge/delete block '{name}': {e}")
                    
                # Rename survivor to final_name if needed
                if survivor_name != final_name:
                    if final_name in doc.blocks:
                        logger.warning(f"  Cannot rename '{survivor_name}' to '{final_name}': Target name already exists.")
                    else:
                        logger.info(f"  Renaming '{survivor_name}' to '{final_name}'")
                        try:
                            doc.blocks.rename_block(survivor_name, final_name)
                            changed = True
                        except Exception as e:
                            logger.warning(f"  Failed to rename block '{survivor_name}': {e}")
            
            if changed:
                # Verify consistency before saving
                # ensure all INSERTs point to valid blocks?
                # That's expensive. But let's assume ezdxf handles basic integrity.
                doc.save()
                updated_files_count += 1
                
        except Exception as e:
            logger.error(f"Error updating {file_path}: {e}")
            import traceback
            traceback.print_exc()

    logger.info(f"Normalization complete. Updated {updated_files_count} files.")

def _merge_block_references(doc, old_name, new_name):
    """
    Update all references of old_name to new_name.
    """
    # Iterate all layouts (Modelspace + Paperspace)
    for layout in doc.layouts:
        for entity in layout:
            if entity.dxftype() == 'INSERT':
                if entity.dxf.name == old_name:
                    entity.dxf.name = new_name
                    
    # Also update nested blocks
    for block in doc.blocks:
        if block.name == old_name: 
            continue 
        for entity in block:
            if entity.dxftype() == 'INSERT':
                if entity.dxf.name == old_name:
                    entity.dxf.name = new_name

if __name__ == "__main__":
    target_dir = 'cad'
    normalize_blocks(target_dir)
