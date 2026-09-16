"""pytest 公共路径：把 starter 下的各子目录加入 sys.path，方便按模块名 import。"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _d in ("agent", "platform", "p2"):
    _p = os.path.join(ROOT, _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)
