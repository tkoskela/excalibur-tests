""" Performance test using IMB's uniband and biband.

    Run using something like:
        
        cd hpc-tests
        conda activate hpc-tests
        reframe/bin/reframe -C reframe-settings.py -c imb-2018.1/ --run --performance-report

    Runs:
    - 2 tasks on same node
    - 2 tasks on different nodes
    Both have exclusive node access.
"""

import reframe as rfm
import reframe.utility.sanity as sn
from reframe.utility.sanity import defer
from pprint import pprint
import sys

from reframe.core.logging import getlogger


# examples of output:
# # Benchmarking Uniband 
# # #processes = 2 
# #---------------------------------------------------
#        #bytes #repetitions   Mbytes/sec      Msg/sec
#             0         1000         0.00      2189915
#
# # Benchmarking PingPong 
# # #processes = 2 
# #---------------------------------------------------
#        #bytes #repetitions      t[usec]   Mbytes/sec
#             0         1000         2.25         0.00


def read_imb_out(path):
    """ Read stdout from an IMB-MPI1 run. Note this can contain multiple benchmarks.
        
        Returns a dict who's keys are the benchmark name (as passed to IMB-MPI1) and values are dicts:
            'benchmark': str, as above
            'file': str
            'data': {
                    <column_heading1>: [value0, value1, ...],
                    ...,
                }
            'meta':
                'processes':num processes as int
    
        TODO: use numpy instead?
    """

    COLTYPES = {
        'uniband':(int, int, float, int),
        'pingpong':(int, int, float, float),
    }
        
    results = {}
    {'file':path}
    with open(path) as f:
        for line in f:
            if line.startswith('# Benchmarking '):
                benchmark = line.split()[-1].lower()
                col_types = COLTYPES[benchmark]
                processes = int(next(f).split()[-1]) # "# #processes = 2"
                result = {'benchmark':benchmark, 'file':path, 'meta':{'processes:', processes}, 'data':{}}
                results[benchmark] = result
                next(f) # skip header
                while True:
                    cols = next(f).split()
                    if cols == []:
                        break
                    if cols[0].startswith('#'): # header row
                        header = cols
                        for label in header:
                            result['data'][label] = []
                    else:
                        for label, opr, value in zip(header, col_types, cols):
                            result['data'][label].append(opr(value))
    return results

@sn.sanity_function
def reduce(path, benchmark, column, function):
    """ Reduce results along a particular column.

        Args:
            path: str, path to results file
            benchmark: str, name of benchmark - as passed as an IMB-MPI1 argument
            column: str, column of output to operate on, e.g. 'Mbytes/sec'
            function: function to apply to column values
        
        Example:
            reduce(self.stdout, 'pingpong', 'Mbytes/sec', max)

        Caches the result of reading the reuslts file for efficency.
    """
    cache = getattr(reduce, 'cache', {})
    results = cache.setdefault(path, read_imb_out(path))
    values = results[benchmark]['data'][column]
    return function(values)

class IMB_MPI1(rfm.RunOnlyRegressionTest):
    def __init__(self):
        self.valid_systems = ['*']
        self.valid_prog_environs = ['*']
        self.modules = ['imb']
        self.executable = 'IMB-MPI1'
        self.exclusive_access = True
        self.metrics = []
        self.perf_patterns = {} # must do this
        #self.reference['*'] = {} # don't do this ...
        # self.reference = {'*':{}} # or this
    
    def add_metric(self, benchmark, function, column, label):
        """ e.g. add_metric('pingpong', max, 'Mbytes/sec', 'bandwidth') """
        benchmark = benchmark.lower()
        perf_label = '_'.join((benchmark, function.__name__, label))
        self.perf_patterns[perf_label] = reduce(self.stdout, benchmark, column, function)
        self.reference[perf_label] = (0, None, None, column) # oddly we don't have to supply the "*" scope key??
        
    @rfm.run_before('run')
    def add_launcher_options(self):
        self.job.launcher.options = ['--report-bindings'] # note these are output to stdERR


@rfm.simple_test
class IMB_PingPong(IMB_MPI1):
    def __init__(self):
        super().__init__()
        self.executable_opts = ['pingpong']
        self.num_tasks = 2
        self.num_tasks_per_node = 1
        self.sanity_patterns = sn.assert_found('# Benchmarking PingPong', self.stdout)
        self.add_metric('pingpong', max, 'Mbytes/sec', 'bandwidth')
        self.add_metric('pingpong', min, 't[usec]', 'latency')

@rfm.simple_test
class IMB_Uniband(IMB_MPI1):
    def __init__(self):
        super().__init__()
        self.executable_opts = ['uniband']
        self.num_tasks = 2
        self.num_tasks_per_node = 1
        self.sanity_patterns = sn.assert_found('# Benchmarking Uniband', self.stdout)
        self.add_metric('uniband', max, 'Mbytes/sec', 'bandwidth')

# @rfm.simple_test this is failing for some reason
class IMB_Biband(IMB_MPI1):
    def __init__(self):
        super().__init__()
        self.executable_opts = ['biband']
        self.num_tasks = 2
        self.num_tasks_per_node = 1
        self.sanity_patterns = sn.assert_found('# Benchmarking Biband', self.stdout)
        self.add_metric('biband', max, 'Mbytes/sec', 'bandwidth')


#@rfm.parameterized_test([1], [2])
# class IMB_MPI1Test(IMB_MPI1):
#     def __init__(self, num_nodes=2):
#         self.name = self.name + "_Nodes" # default names for parameterised tests include argument(s)
#         self.executable_opts = ['uniband', 'biband'] # TODO: use parameterised test instead??
#         self.perf_patterns = {
#             'uniband_max_bandwidth': max_bandwidth(self.stdout, 'Uniband'),
#             'biband_max_bandwidth': max_bandwidth(self.stdout, 'Biband'),
#         }
#         self.reference = {
#             '*': {
#                 'uniband_max_bandwidth': (0, None, None, 'Mbytes/sec'),
#                 'biband_max_bandwidth': (0, None, None, 'Mbytes/sec'),
#             }
#         }
#         self.exclusive_access = True
#         self.num_tasks = 2
#         self.num_tasks_per_node = int(self.num_tasks / num_nodes)


# if __name__ == '__main__':
#     # hacky test of extraction:
#     from reframe.utility.sanity import evaluate
#     # with open(sys.argv[-1]) as f:
#     #     stdout = f.read()
#     # pprint(evaluate(imb_results(stdout, 'Uniband')))
