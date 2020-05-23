""" Extra functionality for reframe

    TODO: refactor into modules
"""

import reframe as rfm
from reframe.core.buildsystems import BuildSystem
from reframe.core.logging import getlogger
from reframe.core.launchers import JobLauncher

import os, shutil, subprocess, shlex
from pprint import pprint

class CachedCompileOnlyTest(rfm.CompileOnlyRegressionTest):
    """ A compile-only test with caching of binaries between `reframe` runs.
    
        Test classes derived from this class will save `self.executable` to a ./builds/{system}/{partition}/{environment}/{self.name}` directory after compilation.
        However if this path (including the filename) exists before compilation (i.e. on the next run):
            - No compilation occurs
            - `self.sourcesdir` is set to this directory, so `reframe` will copy the binary to the staging dir (as if compilation had occured)
            - A new attribute `self.build_path` is set to this path (otherwise None)

        Note that `self.sourcesdir` is only manipulated if no compilation occurs, so compilation test-cases which modify this to specify the source directory should be fine.

        TODO: Make logging tidier - currently produces info-level (stdout by default) messaging on whether cache is used.
    """
    @rfm.run_before('compile')
    def conditional_compile(self):
        build_dir = os.path.abspath(os.path.join('builds', self.current_system.name, self.current_partition.name, self.current_environ.name, self.name))
        build_path = os.path.join(build_dir, self.executable)
        if os.path.exists(build_path):
            self.build_path = build_path
            getlogger().info('found exe at %r', self.build_path)
            self.build_system = NoBuild()
            self.sourcesdir = build_dir # means reframe will copy the exe back in
        else:
            self.build_path = None

    @rfm.run_after('compile')
    def copy_executable(self):
        if not self.build_path: # i.e. only if actually did a compile:
            self.exes_dir = os.path.join('builds', self.current_system.name, self.current_partition.name, self.current_environ.name, self.name)
            exe_path = os.path.join(self.stagedir, self.executable)
            build_path = os.path.join(self.exes_dir, self.executable)
            build_dir = os.path.dirpath(build_path) # self.executable might include a directory
            if not os.path.exists(build_dir):
                os.makedirs(build_dir)
            shutil.copy(exe_path, build_path)
            getlogger().info('copied exe to %r', build_path)

class NoBuild(BuildSystem):
    """ A no-op build system """
    def __init__(self):
        super().__init__()
    def emit_build_commands(self, environ):
        return []

def slurm_node_info():
    """ Get information about slurm nodes.
    
        Returns a sequence of dicts, one per node.
        TODO: document keys - are as per `sinfo --Node --long`

        TODO: add partition selection? with None being current one (note system partition != slurm partition)
    """
    nodeinfo = subprocess.run(['sinfo', '--Node', '--long'], capture_output=True).stdout.decode('utf-8') # encoding?

    nodes = []
    lines = nodeinfo.split('\n')
    header = lines[1].split() # line[0] is date/time
    for line in lines[2:]:
        line = line.split()
        if not line:
            continue
        nodes.append({})
        for ci, key in enumerate(header):
            nodes[-1][key] = line[ci]
    return nodes


# you don't need this, you can just use e.g.:
# @rfm.run_before('run')
#     def add_launcher_options(self):
#         self.job.launcher.options = ['--map-by=xxx']

# class LauncherWithOptions(JobLauncher):
#     """ Wrap a job launcher to provide options.

#         Use like:

#         @rfm.run_after('setup')
#         def modify_launcher(self):
#             self.job.launcher = LauncherWithOptions(self.job.launcher, options=['--bind-to', 'core'])
        
#         TODO: change behaviour depending on launcher type?
#     """
#     def __init__(self, target_launcher, options=None):
#         if options is None:
#             options = []
#         super().__init__()
#         self.self.launcher_options = options
#         self._target_launcher = target_launcher
#         self._wrapper_command = [wrapper_command] + wrapper_options

#     def command(self, job):
#         launcher_cmd = self._target_launcher.command(job) # a list
#         return launcher_cmd[0] + self.launcher_options + launcher_cmd[1:]

if __name__ == '__main__':
    # will need something like:
    # [hpc-tests]$ PYTHONPATH='reframe' python reframe_extras/__init__.py
    pprint(slurm_node_info())