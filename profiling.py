#The trace files are from the pytorch generated chrome trace files
#TODO: should probably run the profiles here as well
import importlib
import sys
trace_files = ['prof_child_fwd_trace',
               'prof_child_bp_trace',
               'prof_ctlr_fwd_trace',
               'prof_ctlr_bp_trace',
               'prof_sample_trace',
               'prof_get_loss_trace'
              ]

prof = importlib.import_module(sys.argv[1])

#based on chrome trace format
# {"name": "unsigned short", "ph": "X", "ts": 86.114, "dur": 13.083999999999989, 
#  "tid": 0, "pid": "CPU functions", "args": {}}
class Interval(object):
    def __init__(self, trace_dict):
        self.start = trace_dict["ts"]
        self.end   = self.start + trace_dict["dur"]
        self.dur   = trace_dict["dur"]
        self.name  = trace_dict["name"]
        self.contained = False
        if "CPU" in trace_dict["pid"]:
            self.type = "CPU"
        elif "GPU" in trace_dict["pid"]:
            self.type = "GPU"
        else:
            selt.type = None

    def contains(self, other):
        contains = other.start >= self.start and other.end <= self.end
        if contains:
            other.contained = True
        return contains

class FuncStat(object):
    def __init__(self, name, initial_duration=0.0):
        self.name = name
        self.duration = initial_duration
        self.num_calls = 1

    def add(self,duration):
        self.duration += duration
        self.num_calls += 1

class ScanList(list):
    toplevel ={}
    def _remove_to_toplevel(self, item):
        self.remove(item)
        #print(f"Removing {item.name}")
        if(not item.contained):
            if item.name in ScanList.toplevel:
                ScanList.toplevel[item.name].add(item.dur)
            else:
                ScanList.toplevel[item.name] = FuncStat(item.name, item.dur)

    def finalize(self):
        for item in self:
            self._remove_to_toplevel(item)


    def append(self,interval):
        #first we need to see if any existing items need to be removed:
        for item in self:
            if item.end < interval.start:
                self._remove_to_toplevel(item)
        #now add interval obj checking to see if it is contained by any existing items
        for item in self:
            if item.contains(interval):
                interval.contained = True
                #print(f' ---> {item.name} contains {interval.name}')
            
        super().append(interval)
        
# {"name": "unsigned short", "ph": "X", "ts": 86.114, "dur": 13.083999999999989, 
#  "tid": 0, "pid": "CPU functions", "args": {}}


def report_prof(prof_name):
    print("-"*80)
    prof_rpt_name = " ".join(prof_name.split("_")[1:-1])
    print(f'Profile for {prof_rpt_name} sorted by total CPU time')
    print("-"*80)
    scanlist = ScanList()
    prof = importlib.import_module(prof_name)
    for call in prof.trace:
        interval = Interval(call)
        scanlist.append(interval)
        #print(f'len(scanlist): {len(scanlist)}')
    scanlist.finalize()
    names = ScanList.toplevel.keys()
    all_cpu_time = 0.0
    all_gpu_time = 0.0
    longest_func_name = 0
    for name in names:
        if len(name) > longest_func_name:
            longest_func_name = len(name)

    for func_name, func_stat in sorted(list(ScanList.toplevel.items()), key=lambda x: x[1].duration):
        print(f'{func_name:{longest_func_name}}: total CPU time {func_stat.duration:.2f}us, #calls: {func_stat.num_calls}, time/call:{func_stat.duration/func_stat.num_calls:.2f}us')
        all_cpu_time += func_stat.duration
    print(f'\nTotal Time for {prof_rpt_name}: {all_cpu_time} us' )
    print("-"*80)
    print()


for trace_file in trace_files:
    report_prof(trace_file)

