
import unittest
from typing import Dict, List, Any
from block_finder import BlockFinder

# Mock logger
import logging
logging.basicConfig(level=logging.DEBUG)

class TestBlockFilter(unittest.TestCase):
    def setUp(self):
        self.finder = BlockFinder()
        # Mock methods that are not needed for this test
        self.finder._log_progress = lambda cb, msg: print(f"LOG: {msg}")

    def test_priority_filtering_simple(self):
        """测试简单场景：同一行 MatID 和 DrawNum 都找到，DrawNum 应被移除"""
        # Setup
        material_info = {
            'M1': {'id_type': 'material_id', 'total_qty': 1, 'row_allocations': {0: 1}, 'row_index': 0},
            'D1': {'id_type': 'drawing_num', 'total_qty': 1, 'row_allocations': {0: 1}, 'row_index': 0}
        }
        all_found_blocks = {
            'M1': [('BlockM', {})],
            'D1': [('BlockD', {})]
        }
        
        # Execute
        self.finder._filter_blocks_by_priority(all_found_blocks, material_info)
        
        # Assert
        self.assertIn('M1', all_found_blocks)
        self.assertNotIn('D1', all_found_blocks)
        print("Test Simple: Passed")

    def test_priority_filtering_partial_overlap(self):
        """测试部分重叠：D1 在 Row 0 被 M1 覆盖，但在 Row 1 未被覆盖"""
        material_info = {
            'M1': {'id_type': 'material_id', 'total_qty': 1, 'row_allocations': {0: 1}, 'row_index': 0},
            'D1': {'id_type': 'drawing_num', 'total_qty': 2, 'row_allocations': {0: 1, 1: 1}, 'row_index': 0}
        }
        all_found_blocks = {
            'M1': [('BlockM', {})],
            'D1': [('BlockD', {})]
        }
        
        # Execute
        self.finder._filter_blocks_by_priority(all_found_blocks, material_info)
        
        # Assert
        self.assertIn('M1', all_found_blocks)
        self.assertIn('D1', all_found_blocks)
        # D1 total qty should be reduced to 1 (Row 1 only)
        self.assertEqual(material_info['D1']['total_qty'], 1)
        self.assertNotIn(0, material_info['D1']['row_allocations'])
        self.assertIn(1, material_info['D1']['row_allocations'])
        print("Test Partial Overlap: Passed")

    def test_priority_filtering_full_overlap_multi_row(self):
        """测试完全重叠：D1 在 Row 0 和 Row 1 都被 MatID 覆盖"""
        material_info = {
            'M1': {'id_type': 'material_id', 'total_qty': 1, 'row_allocations': {0: 1}, 'row_index': 0},
            'M2': {'id_type': 'material_id', 'total_qty': 1, 'row_allocations': {1: 1}, 'row_index': 1},
            'D1': {'id_type': 'drawing_num', 'total_qty': 2, 'row_allocations': {0: 1, 1: 1}, 'row_index': 0}
        }
        all_found_blocks = {
            'M1': [('BlockM1', {})],
            'M2': [('BlockM2', {})],
            'D1': [('BlockD', {})]
        }
        
        # Execute
        self.finder._filter_blocks_by_priority(all_found_blocks, material_info)
        
        # Assert
        self.assertIn('M1', all_found_blocks)
        self.assertIn('M2', all_found_blocks)
        self.assertNotIn('D1', all_found_blocks)
        print("Test Full Overlap Multi Row: Passed")

    def test_mat_id_not_found(self):
        """测试 MatID 未找到的情况：DrawNum 应保留"""
        material_info = {
            'M1': {'id_type': 'material_id', 'total_qty': 1, 'row_allocations': {0: 1}, 'row_index': 0},
            'D1': {'id_type': 'drawing_num', 'total_qty': 1, 'row_allocations': {0: 1}, 'row_index': 0}
        }
        # M1 not in all_found_blocks
        all_found_blocks = {
            'D1': [('BlockD', {})]
        }
        
        # Execute
        self.finder._filter_blocks_by_priority(all_found_blocks, material_info)
        
        # Assert
        self.assertIn('D1', all_found_blocks)
        self.assertEqual(material_info['D1']['total_qty'], 1)
        print("Test MatID Not Found: Passed")

if __name__ == '__main__':
    unittest.main()
