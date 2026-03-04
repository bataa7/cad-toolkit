
import os
import csv
import logging
import ezdxf
from collections import defaultdict, Counter
from block_finder import BlockFinder

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_report(search_dirs, output_csv='block_resource_list.csv'):
    finder = BlockFinder()
    
    # Map: fingerprint -> {
    #   'canonical_name': str,
    #   'files': set(str),
    #   'count': int
    # }
    content_map = {}
    
    total_files = 0
    
    logger.info("Scanning files to generate report...")
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
            
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.lower().endswith('.dxf'):
                    file_path = os.path.join(root, file)
                    total_files += 1
                    
                    try:
                        doc = ezdxf.readfile(file_path)
                        for block in doc.blocks:
                            if hasattr(block, 'is_layout_block'):
                                if block.is_layout_block:
                                    continue
                            else:
                                if block.name.upper() in ('*MODEL_SPACE', '*PAPER_SPACE'):
                                    continue
                                if block.name.startswith('*Paper_Space'):
                                    continue
                            
                            if block.name.startswith('*') or block.name.startswith('_'):
                                continue
                                
                            fp = finder._get_block_content_key(block)
                            
                            if fp not in content_map:
                                content_map[fp] = {
                                    'canonical_name': block.name,
                                    'files': set(),
                                    'count': 0
                                }
                            
                            # Update name if we find a "better" one? 
                            # Since we normalized, they should be consistent.
                            # But if they are not (across files), we might see different names for same FP.
                            # But we normalized globally, so they SHOULD be consistent.
                            # Let's record all names seen just in case.
                            if 'names' not in content_map[fp]:
                                content_map[fp]['names'] = set()
                            content_map[fp]['names'].add(block.name)
                            
                            content_map[fp]['files'].add(file_path)
                            content_map[fp]['count'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error scanning {file_path}: {e}")

    logger.info(f"Scan complete. Found {len(content_map)} unique block contents.")
    
    # Write CSV
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Block Name', 'Fingerprint Hash', 'Total Occurrences', 'File Count', 'Files', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for fp, data in content_map.items():
            names = list(data['names'])
            primary_name = names[0]
            if len(names) > 1:
                # This shouldn't happen if normalization worked perfectly
                status = f"Name Conflict: {', '.join(names)}"
                primary_name = sorted(names)[0] # Pick one deterministically
            else:
                status = "Normalized"
            
            writer.writerow({
                'Block Name': primary_name,
                'Fingerprint Hash': hash(fp),
                'Total Occurrences': data['count'],
                'File Count': len(data['files']),
                'Files': '; '.join(sorted(list(data['files']))),
                'Status': status
            })
            
    logger.info(f"Report generated: {output_csv}")

if __name__ == "__main__":
    generate_report(['cad'])
