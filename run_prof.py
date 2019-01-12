#!/usr/bin/env python
##############################################################
# run_prof.py
# run profiling - for use only with the profiling branch
##############################################################
import os
from subprocess import Popen, PIPE
import re
import sys
import argparse

prof_args = ['prof_ctrl_bp',
            'prof_shared_bp',
            'prof_ctrl_fwd',
            'prof_shared_fwd',
            'prof_sample'
            ]

parser = argparse.ArgumentParser()  
def str2bool(v):
    return v.lower() in ('true')

#parser.add_argument("-V", "--version", help="show program version", action="store_true")
parser.add_argument('--with_GPU', type=str2bool, default=False)
parser.add_argument('--rawfile', type=str, help='process an existing raw profile file')
parser.add_argument('--prof_ctrl_bp', type=str2bool, default=False)
parser.add_argument('--prof_ctrl_fwd', type=str2bool, default=False)
parser.add_argument('--prof_shared_bp', type=str2bool, default=False)
parser.add_argument('--prof_shared_fwd', type=str2bool, default=False)
parser.add_argument('--prof_sample', type=str2bool, default=False)



args = parser.parse_args()
if args.prof_ctrl_bp or args.prof_ctrl_fwd or args.prof_shared_bp or args.prof_shared_fwd or args.prof_sample:
    prof_args = []
    if args.prof_ctrl_bp:
        prof_args.append('prof_ctrl_bp')
    if args.prof_ctrl_fwd:
        prof_args.append('prof_ctrl_fwd')
    if args.prof_shared_fwd:
        prof_args.append('prof_shared_fwd')
    if args.prof_shared_bp:
        prof_args.append('prof_shared_bp')
    if args.prof_sample:
        prof_args.append('prof_sample')


print(args.with_GPU)
print(args.rawfile)
print(prof_args)




USE_GPU = args.with_GPU
filenm = "out_gpu_prof"
if USE_GPU:
    OUTDIR = f"profiles_gpu"
    NUM_GPU = 1 
else:
    OUTDIR = f"profiles_cpu"
    NUM_GPU = 0

if not os.path.exists(OUTDIR):
    os.makedirs(OUTDIR)

#TODO add argument parsing

if len(sys.argv) > 1:
    filenm = sys.argv[1]
    print(f"File is: {filenm}")

def process_profs(outstr,filenm=None):
    if not args.rawfile:
        outstr = outstr.decode('utf-8')
    non_decimal = re.compile(r'[^\d.]+')
#TODO track number of calls of each function as well
    functions = {}
    out_filenm = f"./{OUTDIR}/{filenm}"
    print(f"Writing to: {out_filenm}")
    if filenm:
        print(f"open {out_filenm}")
        out_file = open(out_filenm,'w')
    else:
        out_file = sys.stdout
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
                if fields[0] == "================================================================":
                    break #done, don't look at anymore lines
                funcname = fields[0]
                cputime  = fields[4]
                cputime  = non_decimal.sub('',cputime)
                cputime  = float(cputime)
                cudatime = fields[5]
                cudatime = float(non_decimal.sub('', cudatime))
                print(f'funcname: {funcname} at line: {cnt} cputime: {cputime}')
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
                functions[funcname] = [cputime, cudatime, 1]

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
        print(f'{func:{longest_func_name}}: CPU time {value[0]:.2f} us calls: {value[2]}', file=out_file)
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




def run_profiles(prof_args):
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
                     "--num_gpu",
                     f"{NUM_GPU}",
                     "--log_dir",
                     "alt_log",
                     f"--{prof_arg}",
                     "True"
                   ]
        print("-"*64)
        print(f'Running: {" ".join(command)}')
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        with open(f"{prof_arg}_raw.txt","w") as rawfile:
            rawfile.write(output.decode('utf-8'))
            #print(output,file=rawfile)
            print("="*64,file=rawfile)
            #print(err,file=rawfile)
            rawfile.write(err.decode('utf-8'))
        process_profs(output, f"{prof_arg}.txt")

if args.rawfile:
    with open(args.rawfile, 'r') as f:
        data = f.read()
        process_profs(data)
else:
    run_profiles(prof_args)
