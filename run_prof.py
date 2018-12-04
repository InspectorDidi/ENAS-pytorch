#!/usr/bin/env python
##############################################################
# run_prof.py
# run profiling - for use only with the profiling branch
##############################################################
import os
from subprocess import Popen, PIPE
import re
#import argparse
#parser = argparse.ArgumentParser()  
#parser.add_argument("-V", "--version", help="show program version", action="store_true")
import sys

filenm = "out_gpu_prof"
OUTDIR = "profiles"
if not os.path.exists(OUTDIR):
    os.makedirs(OUTDIR)

#TODO add argument parsing

if len(sys.argv) > 1:
    filenm = sys.argv[1]
    print(f"File is: {filenm}")

def process_profs(outstr,filenm):
    outstr = outstr.decode('utf-8')
    non_decimal = re.compile(r'[^\d.]+')
#TODO track number of calls of each function as well
    functions = {}
    out_filenm = f"./profiles/{filenm}"
    print(f"Writing to: {out_filenm}")
    out_file = open(out_filenm,'w')
    lines = outstr.splitlines()
    for cnt, line in enumerate(lines):
        if len(line) > 1 and line[0] == '[':
            print(line,file=out_file)
            continue
        fields = line.split()
        if len(fields) > 0 and fields[0] == 'Profile':
           print(line,file=out_file)
        else:
            try:
                funcname = fields[0]
                cputime  = fields[4]
                cputime  = non_decimal.sub('',cputime)
                cputime  = float(cputime)
                cudatime = fields[5]
                cudatime = float(non_decimal.sub('', cudatime))
            except ValueError:
                continue
            except IndexError:
                continue
            #print(f'line: {cnt} cputime: {cputime} cudatime: {cudatime}')
            if funcname in functions:
                functions[funcname][0] += cputime
                functions[funcname][1] += cudatime
                functions[funcname][2] += 1
            else:
                functions[funcname] = [0.0, 0.0, 0]

    allcpu = 0.0
    allgpu = 0.0
    longest_func_name = 0
    for func in functions.keys():
        #print(f'{func} cpu total: {functions[func][0]}')
        #print(f'{func} gpu total: {functions[func][1]}')
        allcpu += functions[func][0]
        allgpu += functions[func][1]
        if len(func) > longest_func_name:
            longest_func_name = len(func)

    print("-"*64, file=out_file)
    print("Sorted by CPU time", file=out_file)
    print("-"*64, file=out_file)

    for func, value in sorted(functions.items(), key=lambda x: x[1][0]):
        print(f'{func:{longest_func_name}}: CPU time {value[0]:.2f} calls: {value[2]}', file=out_file)
    print(file=out_file)
    print("-"*64,file=out_file)
    print("Sorted by GPU time",file=out_file)
    print("-"*64,file=out_file)
    for func, value in sorted(functions.items(), key=lambda x: x[1][1]):
        if value[1] > 0.0:
           print(f"{func:{longest_func_name}}: GPU time: {value[1]:.2f} calls: {value[2]}",file=out_file)
        else:
           print(f"{func:{longest_func_name}}: GPU time: {value[1]:.2f}",file=out_file)

    print("-"*64,file=out_file)
    print(f'CPU total: {allcpu}',file=out_file)
    print(f'GPU total: {allgpu}',file=out_file)
    out_file.close()


prof_args = ['prof_ctrl_bp',
            'prof_shared_bp',
            'prof_ctrl_fwd',
            'prof_shared_fwd',
            'prof_sample']

for prof_arg in prof_args:
    command = [  "python3",
                 "main.py", 
                 "--network_type",
                 "rnn", 
                 "--dataset",
                 "ptb",
                 "--controller_optim",
                 "adam",
                 "--controller_lr",
                 "0.00035",
                 "--shared_optim",
                 "sgd",
                 "--shared_lr",
                 "20.0",
                 "--entropy_coeff",
                 "0.0001",
                 "--max_epoch",
                 "1",
                 "--num_blocks",
                 "12",
                 f"--{prof_arg}",
                 "True"
               ]
    print("-"*64)
    print(f'Running: {" ".join(command)}')
    process = Popen(command, stdout=PIPE, stderr=PIPE)
#    process = Popen(command)
    (output, err) = process.communicate()
    exit_code = process.wait()
    with open(f"{prof_arg}_raw.txt","w") as rawfile:
        rawfile.write(output.decode('utf-8'))
        #print(output,file=rawfile)
        print("="*64,file=rawfile)
        #print(err,file=rawfile)
        rawfile.write(err.decode('utf-8'))
    process_profs(output, f"{prof_arg}.txt")    
