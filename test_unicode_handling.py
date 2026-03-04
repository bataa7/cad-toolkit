#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试block_finder模块的Unicode字符处理功能
"""

import os
import sys
import logging
from block_finder import BlockFinder

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_unicode_handling():
    """测试Unicode字符处理功能"""
    try:
        # 创建BlockFinder实例
        finder = BlockFinder()
        
        # 测试_decode_unicode_escape方法
        test_cases = [
            r'\\U+5171',  # 共
            r'\\U5171',   # 共
            r'\\u+5171',  # 共
            r'\\u5171',   # 共
            r'测试\\U+5171文本',  # 测试共文本
            r'\\U+5171\\U+4ef6',  # 共件
        ]
        
        logger.info("测试Unicode转义序列解码...")
        for test_case in test_cases:
            result = finder._decode_unicode_escape(test_case)
            logger.info(f"输入: {repr(test_case)}")
            logger.info(f"输出: {repr(result)}")
            logger.info("-" * 50)
        
        logger.info("测试完成！")
        return True
    except Exception as e:
        logger.error(f"测试时出错: {e}")
        return False

if __name__ == "__main__":
    success = test_unicode_handling()
    if success:
        logger.info("Unicode字符处理测试成功！")
    else:
        logger.error("Unicode字符处理测试失败！")
    sys.exit(0 if success else 1)