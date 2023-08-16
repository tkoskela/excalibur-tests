In this tutorial you will set up the benchmarking framework on the [ARCHER2](https://www.archer2.ac.uk) supercomputer, build and run example benchmarks, create a new benchmark and explore benchmark data.

# Getting Started

To complete this tutorial, you need to [connect to ARCHER2 via ssh](https://docs.archer2.ac.uk/user-guide/connecting/). You will need

1. An ARCHER2 account. You can [request a new account](https://docs.archer2.ac.uk/quick-start/quickstart-users/#request-an-account-on-archer2) if you haven't got one you can use. TODO: How do we give accounts to trainees during live workshop?
2. A command line terminal with an ssh client. Most Linux and Mac systems come with these preinstalled. Please see [Connecting to ARCHER2](https://docs.archer2.ac.uk/user-guide/connecting/#command-line-terminal) for more information and Windows instructions.

Once you have the above prerequisites, you have to [generate an ssh key pair](https://docs.archer2.ac.uk/user-guide/connecting/#ssh-key-pairs) and [upload the public key to SAFE](https://docs.archer2.ac.uk/user-guide/connecting/#upload-public-part-of-key-pair-to-safe). Once you are done, you should be able to connect to ARCHER2 with

```bash
ssh username@login.archer2.ac.uk
```

# Installing the Framework

## Set up python

We are going to use `python` and the `pip` package installer to install and run the framework. Load the `cray-python` module to get a python version that fills the requirements.
```bash
$ module load cray-python
```
You can check with `python3 --version` that your python version is `3.8` or greater (at the time of writing, the default version was `3.9.13`).

## Change to work directory

On ARCHER2, the compute nodes do not have access to your home directory, therefore it is import to install everything in a [work file system](https://docs.archer2.ac.uk/user-guide/data/#work-file-systems). Change to the work directory with

```bash
$ cd /work/<project code>/<project code>/${username}
```

TODO: Fill in project code
where ``${username}`` is the username you used to log in. In the work directory, clone the [excalibur-tests](https://github.com/ukri-excalibur/excalibur-tests) repository with

## Clone the repository

```bash
$ git clone https://github.com/ukri-excalibur/excalibur-tests.git
```
## Create a virtual environment
Before proceeding to install the software, we recommend creating a python virtual environment to avoid clashes with other installed python packages. You can do this with
```bash
$ python3 -m venv excalibur-env
$ source excalibur-env/bin/activate
```
You should now see the name of the environment in parenthesis your terminal prompt
```bash
(excalibur-env) tk-d193@ln03:/work/d193/d193/tk-d193>
```
## Install the excalibur-tests package
Now we can use `pip` to install the package in the virtual environment
```bash
$ pip install -e ./excalibur-tests
```
We used the `editable` flag `-e` because later in the tutorial you will edit the repository to develop a new benchmark. If pip returns an error *TODO: Check the error message*, update it to the latest version with `python3 -m pip install --upgrade pip`. 

## Set configuration variables

Configure the framework by setting these environment variables

```bash
export RFM_CONFIG_FILES="$(pwd)/excalibur-tests/benchmarks/reframe_config.py"
export RFM_USE_LOGIN_SHELL="true"
```

## Install and configure spack

Finally, we need to install the `spack` package manager. The framework will use it to build the benchmarks. Clone spack with

```bash
$ git clone -c feature.manyFiles=true git@github.com:spack/spack.git
```

Then configure `spack` with

```bash
$ source ./spack/share/spack/setup-env.sh
```

Spack should now be in the default search path.

## Check installation was successful

You can check everything has been installed successfully by checking that `spack` and `reframe` are in path and the path to the ReFrame config file is set correctly

```bash
$ spack --version
reframe --version0.19.0.dev0 (a8b1314d188149e696eb8e7ba3e4d0de548f1894)
$ reframe --version
4.3.0
$ ls $RFM_CONFIG_FILES
/work/d193/d193/tk-d193/excalibur-tests/benchmarks/reframe_config.py
```

# Run Sombrero Example

You can now use ReFrame to run benchmarks from the `benchmarks/examples` and `benchmarks/apps` directories. The basic syntax is `reframe -c <path/to/benchmark> -r`. In addition, on ARCHER2, you have to provide the quality of service (QoS) type and your account on the command line. For example you can run the sombrero example with *TODO: Check if we need to pass account to reframe*
```bash
$ reframe -c excalibur-tests/benchmarks/examples/sombrero -r -J'--qos=short' -J'--account=t01'
```
You may notice you actually ran four benchmarks with that single command! That is because the benchmark is parametrized. We will talk about it in the next section.
:::spoiler Output sample
```
$ reframe -c benchmarks/examples/sombrero/ -r -J'--qos=short' --performance-report
[ReFrame Setup]
  version:           4.3.0
  command:           '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/excalibur-env/bin/reframe -c benchmarks/examples/sombrero/ -r -J--qos=short'
  launched by:       tk-d193@ln03
  working directory: '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/excalibur-tests'
  settings files:    '<builtin>', '/work/d193/d193/tk-d193/excalibur-tests/benchmarks/reframe_config.py'
  check search path: '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/excalibur-tests/benchmarks/examples/sombrero'
  stage directory:   '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/excalibur-tests/stage'
  output directory:  '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/excalibur-tests/output'
  log files:         '/tmp/rfm-u1l6yt7f.log'

[==========] Running 4 check(s)
[==========] Started on Fri Jul  7 15:47:45 2023 

[----------] start processing checks
[ RUN      ] SombreroBenchmark %tasks=2 %cpus_per_task=2 /de04c10b @archer2:compute-node+default
[ RUN      ] SombreroBenchmark %tasks=2 %cpus_per_task=1 /c52a123d @archer2:compute-node+default
[ RUN      ] SombreroBenchmark %tasks=1 %cpus_per_task=2 /c1c3a3f1 @archer2:compute-node+default
[ RUN      ] SombreroBenchmark %tasks=1 %cpus_per_task=1 /52e1ce98 @archer2:compute-node+default
[       OK ] (1/4) SombreroBenchmark %tasks=1 %cpus_per_task=2 /c1c3a3f1 @archer2:compute-node+default
P: flops: 0.67 Gflops/seconds (r:1.2, l:None, u:None)
[       OK ] (2/4) SombreroBenchmark %tasks=1 %cpus_per_task=1 /52e1ce98 @archer2:compute-node+default
P: flops: 0.67 Gflops/seconds (r:1.2, l:None, u:None)
[       OK ] (3/4) SombreroBenchmark %tasks=2 %cpus_per_task=2 /de04c10b @archer2:compute-node+default
P: flops: 1.27 Gflops/seconds (r:1.2, l:None, u:None)
[       OK ] (4/4) SombreroBenchmark %tasks=2 %cpus_per_task=1 /c52a123d @archer2:compute-node+default
P: flops: 1.24 Gflops/seconds (r:1.2, l:None, u:None)
[----------] all spawned checks have finished

[  PASSED  ] Ran 4/4 test case(s) from 4 check(s) (0 failure(s), 0 skipped, 0 aborted)
[==========] Finished on Fri Jul  7 15:48:23 2023 
Log file(s) saved in '/tmp/rfm-u1l6yt7f.log'

```
:::
Things to note in output
- Config file
- Stage directory for intermediate files (useful when benchmarks fail)
- Output directory for output files
- Figures of merit
You can find the log files from this benchmark in `perflogs/`

# Postprocess Benchmark Results

# Create a Benchmark

In this section you will create a ReFrame benchmark by writing a python class that tells ReFrame how to build and run an application and collect data from its output. For simplicity, we use the [`STREAM`](https://www.cs.virginia.edu/stream/ref.html) benchmark. It is a simple memory bandwidth benchmark with minimal build dependencies.

## Include ReFrame modules

:::spoiler Code
```python
import reframe as rfm
import reframe.utility.sanity as sn
```
:::

## Create a Test Class

`SpackTest` is a class for benchmarks which will use Spack as build system. 

:::spoiler Code
```python=
from benchmarks.modules.utils import SpackTest

@rfm.simple_test
class StreamBenchmark(SpackTest):
```
:::

## Add Build Recipe

We prefer installing packages via spack whenever possible. In this exercise, the spack package for `stream` already exists in the global spack repository.

The `SpackTest` base class takes care of setting up spack as the build system ReFrame uses. We only need to instruct ReFrame to install version `5.10` of the [`stream` spack package](https://spack.readthedocs.io/en/latest/package_list.html#stream).

:::spoiler Code
```python
spack_spec = 'stream@5.10 +openmp'
```
:::

## Add Run Configuration

:::spoiler Code
```python
valid_systems = ['*']
valid_prog_environs = ['default']
executable = stream
num_tasks = 1
num_cpus_per_task = 128
time_limit = '5m'
```
:::

## Add Sanity Check

The rest of the benchmark follows the [Writing a Performance Test ReFrame Tutorial](https://reframe-hpc.readthedocs.io/en/latest/tutorial_basics.html#writing-a-performance-test). First we need a sanity check that ensures the benchmark ran successfully. A function decorated with the `@sanity_function` decorator is used by ReFrame to check that the test ran successfully. The sanity function can perform a number of checks, in this case we want to match a line of the expected output.

:::spoiler Code
```python=
@sanity_function
def validate_solution(self):
    return sn.assert_found(r'Solution Validates', self.stdout)
```
:::

## Add Performance Pattern Check

To record the performance of the benchmark, ReFrame should extract a figure of merit from the output of the test. A function decorated with the `@performance_function` decorator extracts or computes a performance metric from the test’s output.

> In this example, we extract four performance variables, namely the memory bandwidth values for each of the “Copy”, “Scale”, “Add” and “Triad” sub-benchmarks of STREAM, where each of the performance functions use the [`extractsingle()`](https://reframe-hpc.readthedocs.io/en/latest/deferrable_functions_reference.html#reframe.utility.sanity.extractsingle) utility function. For each of the sub-benchmarks we extract the “Best Rate MB/s” column of the output (see below) and we convert that to a float.

:::spoiler Code
```python=
@performance_function('MB/s', perf_key='Copy')
def extract_copy_perf(self):
    return sn.extractsingle(r'Copy:\s+(\S+)\s+.*', self.stdout, 1, float)

@performance_function('MB/s', perf_key='Scale')
def extract_scale_perf(self):
    return sn.extractsingle(r'Scale:\s+(\S+)\s+.*', self.stdout, 1, float)

@performance_function('MB/s', perf_key='Add')
def extract_add_perf(self):
    return sn.extractsingle(r'Add:\s+(\S+)\s+.*', self.stdout, 1, float)

@performance_function('MB/s', perf_key='Triad')
def extract_triad_perf(self):
    return sn.extractsingle(r'Triad:\s+(\S+)\s+.*', self.stdout, 1, float)
```
:::

## Run Stream

```bash
reframe -c apps/stream/ -r --system archer2 -J'--qos=short'
```

:::spoiler Output
```bash
reframe -c apps/stream/ -r --system archer2 -J'--qos=short'
[ReFrame Setup]
  version:           4.3.0
  command:           '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/excalibur-env/bin/reframe -c apps/stream/ -r --system archer2 -J--qos=short'
  launched by:       tk-d193@ln04
  working directory: '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/rsecon-demo'
  settings files:    '<builtin>', '/work/d193/d193/tk-d193/excalibur-tests/benchmarks/reframe_config.py'
  check search path: '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/rsecon-demo/apps/stream'
  stage directory:   '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/rsecon-demo/stage'
  output directory:  '/mnt/lustre/a2fs-work3/work/d193/d193/tk-d193/rsecon-demo/output'
  log files:         '/tmp/rfm-70arere5.log'

[==========] Running 1 check(s)
[==========] Started on Mon Jul 10 15:55:01 2023 

[----------] start processing checks
[ RUN      ] StreamBenchmark /8aeff853 @archer2:compute-node+default
[       OK ] (1/1) StreamBenchmark /8aeff853 @archer2:compute-node+default
P: Copy: 842018.4 MB/s (r:0, l:None, u:None)
P: Scale: 808540.5 MB/s (r:0, l:None, u:None)
P: Add: 959612.0 MB/s (r:0, l:None, u:None)
P: Triad: 941658.5 MB/s (r:0, l:None, u:None)
[----------] all spawned checks have finished

[  PASSED  ] Ran 1/1 test case(s) from 1 check(s) (0 failure(s), 0 skipped, 0 aborted)
[==========] Finished on Mon Jul 10 15:55:18 2023 
Log file(s) saved in '/tmp/rfm-70arere5.log'

```
:::

# Portability Demo

Having gone through the process of setting up the framework on multiple systems enables you to run benchmarks configured in the repository on those systems. As a proof of this concept, this demo shows how to run a benchmark (e.g. `hpgmg`) on a list of systems (ARCHER2, csd3, cosma8, isambard-macs). Note that to run this demo, you will need an account and a CPU time allocation on each of these systems.

The commands to set up and run the demo are recorded in [scripts in the exaclibur-tests repository](https://github.com/ukri-excalibur/excalibur-tests/tree/tk-portability-demo/demo). It is not feasible to make the progress completely system-agnostic, in our case we need to manually

- Load a compatible python module
- Specify the user account for charging CPU time
- Change the working directory and select quality of service (on ARCHER2)

That is done differently on each system. The framework attempts to automtically identify the system it is being run on, but due to ambiguity in login node names this can fail, and we also recommend specifying the system on the command line.

:::spoiler setup.sh
```bash
#!/bin/bash -l

system=$1

# System specific part of setup. Mostly load the correct python module
if [ $system == archer2 ]
then
    module load cray-python
    cd /work/d193/d193/tk-d193
elif [ $system == csd3 ]
then
    module load python/3.8
elif [ $system == cosma ]
then
    module swap python/3.10.7
elif [ $system == isambard ]
then
    module load python37
    export PATH=/home/ri-tkoskela/.local/bin:$PATH
fi

# Setup
mkdir demo
cd demo
python3 --version
python3 -m venv demo-env
source ./demo-env/bin/activate
git clone git@github.com:ukri-excalibur/excalibur-tests.git
git clone -c feature.manyFiles=true git@github.com:spack/spack.git
source ./spack/share/spack/setup-env.sh
export RFM_CONFIG_FILES="$(pwd)/excalibur-tests/benchmarks/reframe_config.py"
export RFM_USE_LOGIN_SHELL="true"
pip install --upgrade pip
pip install -e ./excalibur-tests
```
:::

:::spoiler run.sh
```bash
#!/bin/bash

app=$1
compiler=$2
system=$3
spec=$app\%$compiler

apps_dir=excalibur-tests/benchmarks/apps

if [ $system == archer2 ]
then
    reframe -c $apps_dir/$app -r -J'--qos=standard' --system archer2 -S spack_spec=$spec --setvar=num_cpus_per_task=8  --setvar=num_tasks_per_node=2 --setvar=num_tasks=8
elif [ $system == cosma ]
then
    reframe -c $apps_dir/$app -r -J'--account=do006' --system cosma8 -S spack_spec=$spec --setvar=num_cpus_per_task=8  --setvar=num_tasks_per_node=2 --setvar=num_tasks=8
elif [ $system == csd3 ]
then
    reframe -c $apps_dir/$app -r -J'--account=DIRAC-DO006-CPU' --system csd3-cascadelake -S spack_spec=$spec --setvar=num_cpus_per_task=8  --setvar=num_tasks_per_node=2 --setvar=num_tasks=8
elif [ $system == isambard ]
then
    reframe -c $apps_dir/$app -r --system isambard-macs:cascadelake -S build_locally=false -S spack_spec=$spec --setvar=num_cpus_per_task=8  --setvar=num_tasks_per_node=2 --setvar=num_tasks=8
fi
```
:::