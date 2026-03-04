
import os
import sys
import logging
import ezdxf
from collections import defaultdict
from block_finder import BlockFinder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_duplicates(search_dirs: list[str]):
    finder = BlockFinder()
    
    # Map: fingerprint -> list of {'file': str, 'block_name': str}
    content_map = defaultdict(list)
    
    # Map: block_name -> list of {'file': str, 'fingerprint': tuple}
    name_map = defaultdict(list)
    
    total_files = 0
    total_blocks = 0
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            logger.warning(f"Directory not found: {search_dir}")
            continue
            
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.lower().endswith('.dxf'):
                    file_path = os.path.join(root, file)
                    logger.info(f"Scanning file: {file_path}")
                    total_files += 1
                    
                    try:
                        doc = ezdxf.readfile(file_path)
                        
                        # Debug: inspect first block
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
                            
                            # Skip anonymous blocks (*U...) unless necessary? 
                            if block.name.startswith('*'):
                                continue
                                
                            fingerprint = finder._get_block_content_key(block)
                            
                            entry = {'file': file_path, 'block_name': block.name}
                            content_map[fingerprint].append(entry)
                            
                            name_entry = {'file': file_path, 'fingerprint': fingerprint}
                            name_map[block.name].append(name_entry)
                            
                            total_blocks += 1
                            
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {e}")
                        # import traceback
                        # traceback.print_exc()

    logger.info(f"Scan complete. Processed {total_files} files, {total_blocks} blocks.")
    
    # Analyze duplicates (Same content)
    duplicates = {k: v for k, v in content_map.items() if len(v) > 1}
    logger.info(f"Found {len(duplicates)} unique contents that appear multiple times.")
    
    # Analyze conflicts (Same name, different content)
    conflicts = {}
    for name, entries in name_map.items():
        unique_fingerprints = set(e['fingerprint'] for e in entries)
        if len(unique_fingerprints) > 1:
            conflicts[name] = entries
            
    logger.info(f"Found {len(conflicts)} block names with conflicting content.")
    
    return duplicates, conflicts

def report_results(duplicates, conflicts, output_file='duplicate_report.txt'):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== Duplicate Block Resources Report ===\n")
        f.write(f"Total Unique Contents with Duplicates: {len(duplicates)}\n")
        f.write(f"Total Block Name Conflicts: {len(conflicts)}\n\n")
        
        if conflicts:
            f.write("--- Block Name Conflicts (Same Name, Different Content) ---\n")
            f.write("Warning: These blocks have the same name but different geometry!\n")
            for name, entries in conflicts.items():
                f.write(f"\nBlock Name: {name}\n")
                # Group by fingerprint to show variations
                variations = defaultdict(list)
                for entry in entries:
                    variations[entry['fingerprint']].append(entry['file'])
                
                for i, (fp, files) in enumerate(variations.items(), 1):
                    f.write(f"  Variation {i} (Files: {len(files)}):\n")
                    for file in files:
                        f.write(f"    - {file}\n")
            f.write("\n")
            
        if duplicates:
            f.write("--- Duplicate Block Contents (Same Content, Potentially Different Names) ---\n")
            for fp, entries in duplicates.items():
                f.write(f"\nContent Hash: {hash(fp)}\n")
                # Check if names are consistent
                names = set(e['block_name'] for e in entries)
                if len(names) > 1:
                    f.write(f"  Warning: Content appears under different names: {', '.join(names)}\n")
                else:
                    f.write(f"  Block Name: {list(names)[0]}\n")
                
                for entry in entries:
                    f.write(f"    - {entry['file']} : {entry['block_name']}\n")

if __name__ == "__main__":
    search_dirs = ['cad']
    duplicates, conflicts = find_duplicates(search_dirs)
    report_results(duplicates, conflicts)
    print(f"Report generated: duplicate_report.txt")
