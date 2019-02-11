#The trace files are from the pytorch generated chrome trace files
#TODO: should probably run the profiles here as well
import importlib
import sys
from collections import deque
sys.setrecursionlimit(8000)
trace_files = [#'prof_child_fwd_trace',
               'prof_child_bp_trace',
               #'prof_ctlr_fwd_trace',
               #'prof_ctlr_bp_trace',
               #'prof_sample_trace',
               #'prof_get_loss_trace',
               #'prof_get_reward_trace'
              ]

#prof = importlib.import_module(sys.argv[1])

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
    def __str__(self):
        return f"Interval: {name} {dur}"

    def contains(self, other):
        contains = other.start >= self.start and other.end <= self.end
        if contains:
            other.contained = True
        return contains

    def after(self,other):
        return (self.start >= other.end)

    def before(self,other):
        return (self.end >= other.start)

class FuncStat(object):
    def __init__(self, name, initial_duration=0.0,level=0,node=None):
        self.name = name
        self.duration = initial_duration
        self.num_calls = 1
        self.level = level
        self.node = node

    def add(self,duration):
        self.duration += duration
        self.num_calls += 1

    def __str__(self):
        return f'{"  "*self.level}{self.name}: {self.num_calls} : {self.duration}'

class IntervalNode(object):
    def __init__(self,interval,indent=0):
        self.interval = interval
        self.next_node      = None
        self.contained_node = None
        self.contained_nodes = 0
        self.indent_level = indent
        self.contained_calls = {}
        #print(f"IntervalNode indent={indent}")
    def __iter__(self):
        cur_node = self
        while(cur_node):
            yield cur_node
            cur_node = cur_node.next_node

    def iter_contained(self):
        cur_node = self.contained_node
        while(cur_node):
            yield cur_node
            cur_node = cur_node.next_node

    def pre_iter(self,cur_node=None):
        if not cur_node:
            cur_node = self.contained_node
        while(cur_node):
            yield cur_node
            cur_node = cur_node.contained_node
            pre_iter(cur_node.contained_node)
            

    def add_interval(self, interval):
        contained = False
        if self.interval.contains(interval):
            self.contained_nodes += 1
            #child node: increment indent_level
            #self.indent_level += 1
            if not self.contained_node:
                self.contained_node = IntervalNode(interval, self.indent_level+1)
                #if interval.name in self.contained_calls:
                #    self.contained_calls[interval.name].add(interval.dur)
                #else:
                #    self.contained_calls[interval.name] = FuncStat(interval.name,
                #                                                   interval.dur,
                #                                                   self.indent_level+1,
                #                                                   self.contained_node)
            else:
                self.contained_node.add_interval(interval)
        else:
            # 'peer' node, don't increment indent_level
            if self.next_node:
                self.next_node.add_interval(interval)
            else:
                self.next_node = IntervalNode(interval, self.indent_level)

    def summarize(self,log=False):
        cur_node = self
        while(cur_node):
            #print(f"   >>> cur_node is: {cur_node}")
            #print(f'{cur_node.interval.name} contains {cur_node.contained_nodes}')
            if cur_node.interval.name in self.contained_calls:
                self.contained_calls[cur_node.interval.name].add(cur_node.interval.dur)
            else:
                self.contained_calls[cur_node.interval.name] = FuncStat(cur_node.interval.name, cur_node.interval.dur,cur_node.indent_level,self.contained_node)
            cur_node = cur_node.next_node
        return self.contained_calls

    def __str__(self):
        return "   "*self.indent_level + str(self.interval.name)

    def print_node(self):
        # print current interval:
        print(str(self))

    def print_contained_nodes(self):
        cur_node = self.contained_node
        while(cur_node):
           cur_node.print_node()
           cur_node = cur_node.contained_node

    def print_contained(self):
        for call, func_stat in self.contained_calls.items():
            print(f'{"   "*func_stat.level}{func_stat.name}:: {func_stat.num_calls} : {func_stat.duration}')
                 


#############################################3

class IntervalTree(object):
    def __init__(self,interval):
        """pass the initial interval here"""
        self.indent_level = 0
        self.root = IntervalNode(interval, self.indent_level)
        self.toplevel = {}
        self.levels = {}

    def add_interval(self,interval):
        self.root.add_interval(interval)

    def summarize(self):
        # gather toplevel funcs:
        cur_node = self.root
        while(cur_node):
            #self.toplevel[cur_node.interval.name]=cur_node.interval
            #print(f'{cur_node.interval.name} contains {cur_node.contained_nodes}')
            if cur_node.interval.name in self.toplevel:
                self.toplevel[cur_node.interval.name].add(cur_node.interval.dur)
            else:
                self.toplevel[cur_node.interval.name] = FuncStat(cur_node.interval.name, cur_node.interval.dur,cur_node.indent_level,cur_node.contained_node)
                print(f'{"  "*cur_node.indent_level} Current: {cur_node} Adding: {cur_node.contained_node}')
            cur_node = cur_node.next_node
        return self.toplevel
        
    def print_level(self,node=None):
        if not node:
            node = self.root
        cur_node = node
        while cur_node:
            print(cur_node)
            cur_node.print_contained()
            cur_node = cur_node.next_node

    def print_tree(self, node):
        curr_node = node
        while(curr_node):
            print(curr_node)
            curr_contained_node = curr_node.contained_node
            while(curr_contained_node):
                self.print_tree(curr_contained_node)
                curr_contained_node = curr_contained_node.next_node
            curr_node = curr_node.next_node

def walk_levels(calls_dict,func_to_stop=""):
    """must be called after tree is summarized"""
    for name, func_stat in calls_dict.items():
        if name == func_to_stop:
            print(f">>> {func_to_stop}")
            print(f"    >>> {func_to_stop}.node: {func_stat.node}")
            print(f"    >>> contained_calls: {func_stat.node.contained_calls}")
        print(f'{func_stat}')
        if func_stat.node:
            func_stat.node.summarize()
            walk_levels(func_stat.node.contained_calls)
         
class ScanList(list):
    def __init__(self):
        self.toplevel = {}
        self.thislevel = {}
        self.child_list = None
        super().__init__()
        self.scanlist = None

    def _remove_to_toplevel(self, item):
        self.remove(item)
        #print(f"Removing {item.name}")
        if(not item.contained):
            #if item.name in ScanList.toplevel:
            if item.name in self.toplevel:
                self.toplevel[item.name].add(item.dur)
            else:
                self.toplevel[item.name] = FuncStat(item.name, item.dur)

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


def build_call_tree(prof_name):
    prof = importlib.import_module(prof_name)
    tree = IntervalTree(Interval(prof.trace[0]))
    for call in prof.trace[1:-1]:
        tree.add_interval(Interval(call))
    return tree

def report_prof(prof_name):
    pyprof_outfile = f'{prof_name}_.py'
    pyfile = open(pyprof_outfile,'w')
    print(f'import file: {prof_name}, pyprof_outfile: {pyprof_outfile}')
    pyfile.write("profile=[")
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
    names = scanlist.toplevel.keys()
    all_cpu_time = 0.0
    all_gpu_time = 0.0
    longest_func_name = 0
    for name in names:
        if len(name) > longest_func_name:
            longest_func_name = len(name)

    for func_name, func_stat in sorted(list(scanlist.toplevel.items()), key=lambda x: x[1].duration):
        print(f'{func_name:{longest_func_name}}: total CPU time {func_stat.duration:.2f}us, #calls: {func_stat.num_calls}, time/call:{func_stat.duration/func_stat.num_calls:.2f}us')
        pyfile.write(f'("{func_name}",{{"time":{func_stat.duration},"calls":{func_stat.num_calls} }}),')
        all_cpu_time += func_stat.duration
    print(f'\nTotal Time for {prof_rpt_name}: {all_cpu_time} us' )
    print("-"*80)
    print()
    pyfile.write("]")
    pyfile.close()
    #scanlist.toplevel = {}


def print_contained(node):
    """given an IntervalNode print contained calls """
    pass

def print_prof(tree):
    toplevel_calls= (tree.summarize())
    for name, stat in toplevel_calls.items():
        print(f'call:{name} calls:{stat.num_calls} duration:{stat.duration}')
        if(stat.node):
            stat.node.print_contained()

toplevel_calls = []
#tree = None
for trace_file in trace_files:
    print(f"----- report_prof({trace_file}) ------")
#    report_prof(trace_file)
    tree = build_call_tree(trace_file)
    print("------  tree.print_tree(tree.root) -----")
    tree.print_tree(tree.root)
    #toplevel_calls.append(tree.summarize())
    tree.summarize()
    print("-"*80)
    print("------ tree.print_level() ------ ") 
    print("-"*80)
    tree.print_level()
    print("-"*80)
    print(f"{tree.root.print_contained()}")
    print("----> iterate ")
    for node in tree.root:
        print(node)
    print("-----> walk_levels() <-----")
    #tree.walk_levels()
    walk_levels(tree.toplevel,"matmul")

print("="*80)
for call in toplevel_calls:
    print(call)
    for name, stat in call.items():
        print(f'call:{name} calls:{stat.num_calls} duration:{stat.duration}')
    print("*"*80)

print("="*80)

