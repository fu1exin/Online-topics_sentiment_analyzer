"""编译检查所有模块"""
import py_compile
import os, sys

base = os.path.dirname(os.path.abspath(__file__))
files = [
    "config.py",
    "crawler/weibo_crawler.py",
    "preprocess/cleaner.py",
    "preprocess/segmenter.py",
    "sentiment/analyzer.py",
    "visualize/pie_chart.py",
    "main.py",
]
ok = 0
for f in files:
    path = os.path.join(base, f)
    try:
        py_compile.compile(path, doraise=True)
        print(f"  OK  {f}")
        ok += 1
    except py_compile.PyCompileError as e:
        print(f"  FAIL {f}: {e}")

print(f"\n{ok}/{len(files)} 模块编译通过")
