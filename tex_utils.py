import sys
import matplotlib.pyplot as plt
import pylab
import numpy as np
def tex_table(profile, table_name, fo=sys.stdout):
    def prt(s):
        print(s,file=fo)

    prt('\\begin{table}[tb]')
    prt('\\centering')
    prt('\\footnotesize')
    prt(f'\\caption{{{table_name}}} \\label{{tbl:{"".join(table_name.split(" "))}}}')
    prt('\\centering')
    prt(' \\begin{threeparttable}[]')
    prt(' \\begin{tabular}{l r r r r r}')
    prt(' \\toprule')
    prt(' Function & Total Time ($\\mu$sec) & Calls \\\\')
    prt(' \\midrule')
    for func_time in profile:
        func_name = func_time[0].replace('_','\\_')
        func_calls = func_time[1]["calls"]
        func_t  = func_time[1]["time"]
        prt(f'{func_name} & {func_t:.2f} & {func_calls} \\\\ \\hline')
    prt(' \\botrule')
    prt(' \\end{tabular}')
    prt(' \\begin{footnotesize}')
    prt(' \\begin{tablenotes}[para,flushleft]')
    prt(' \\item[]')
    prt('    YOUR TABLE DESCRIPTION HERE ')
    prt(' \\end{tablenotes}')
    prt(' \\end{footnotesize}')
    prt('\\end{threeparttable}')
    prt('\\end{table}')






def plot():
    n_groups = len(profile)

    labels = [ x[0] for x in profile ]
    times =  [ x[1]["time"] for x in profile]

# create plot
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.35
    opacity = 0.8
    loc_plts = []
    for i,func in enumerate(profile):
        func_nm   = func[0]
        func_time = func[1]["time"]
        tmp_plt = plt.bar(i,func,bar_width, color='b')


