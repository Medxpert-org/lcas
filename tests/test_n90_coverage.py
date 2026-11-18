#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_n90_coverage.py —— 覆盖矩阵必须与映射一致（防止"文档写得好、代码没跟上"）。"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class CoverageFresh(unittest.TestCase):
    def test_matrix_is_up_to_date(self):
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "n90_coverage.py"), "--check"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0,
                         "docs/N90-COVERAGE.md 与当前映射不一致，请重跑 tools/n90_coverage.py\n" + p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
