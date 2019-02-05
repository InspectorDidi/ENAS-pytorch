##########################################################
# Run profiling.py prior to running gen_tables.py
##########################################################
import importlib
import sys
import os
import glob
from pathlib import Path
import tex_utils

for trace_file in glob.glob("*trace_.py"):
    prof_name = Path(trace_file).stem
    with open(trace_file, 'r') as tf:
        prof = importlib.import_module(prof_name)
        tex_utils.tex_table(prof.profile, " ".join(prof_name.split("_"))) 
    print()
    


