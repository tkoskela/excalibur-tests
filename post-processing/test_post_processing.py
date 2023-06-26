import fileinput
import os
from pandas.errors import EmptyDataError
from pathlib import Path
import post_processing as post
import pytest
import shutil
import subprocess as sp

# Run given benchmark with reframe using subprocess
def run_benchmark(path):
    sp.run("reframe -c " + path + " -r", shell=True)

# Clean unnecessary files and folders at end of test after running reframe
def benchmark_cleanup(remove_test_logs):

    # remove residual folders
    shutil.rmtree("stage", ignore_errors=True)
    shutil.rmtree("output", ignore_errors=True)

    # remove test log files
    if remove_test_logs:
        shutil.rmtree("perflogs", ignore_errors=True)

# Remove given field from perflog line
def remove_field_from_perflog(line, field_index):

    # parse line
    columns = line.strip().split("|")
    # remove given field
    columns.pop(field_index)
    # convert back to string
    line = "|".join(columns)

    return line

# Test that display name parsing works and parameters can be extracted
def test_display_name_parsing():

    display_name = "TestName %param1=one %param2=two %param3=three"
    test_name, params = post.get_display_name_info(display_name)

    # check param length, names, and values
    assert test_name == "TestName"
    assert len(params) == 3
    assert (params["param1"] == "one") & (params["param2"] == "two") & (params["param3"] == "three")

    display_name = "TestName"
    _, params = post.get_display_name_info(display_name)

    # no params expected
    assert len(params) == 0

@pytest.fixture(scope="module")
# Fixture to run sombrero benchmark example, generate perflogs, and clean up after test
def run_sombrero():

    # settings
    # set True to remove test log files at the end of the test
    remove_test_logs = True

    # setup
    # absolute path to post-processing directory
    post_processing_dir = Path(__file__).parent
    # change current working dir to avoid potentially deleting non-test perflogs
    os.chdir(post_processing_dir)
    # remove the test perflog directory if it currently exists
    if os.path.exists("perflogs"):
        shutil.rmtree("perflogs", ignore_errors=True)
    # get test log location path
    perflog_path = os.path.join(post_processing_dir, "perflogs")
    # resolve relative path from post-processing directory to access sombrero benchmark
    sombrero_bench_path = os.path.join(post_processing_dir.parent / "benchmarks/examples/sombrero/sombrero.py")

    # use sombrero example to generate new test perflog file
    run_benchmark(sombrero_bench_path)

    sombrero_log = "SombreroBenchmark.log"
    # look for newly generated log file
    for root, _, files in os.walk(perflog_path):
        if files:
            # if file is found, get file dir path
            if sombrero_log in files:
                # perflog path with <system>/<partition>
                perflog_path = root
    # get log file path
    sombrero_log_path = os.path.join(perflog_path, sombrero_log)

    # create an incomplete log file
    sombrero_incomplete_log = "SombreroBenchmarkIncomplete.log"
    sombrero_incomplete_log_path = os.path.join(perflog_path, sombrero_incomplete_log)

    if os.path.exists(sombrero_log_path):
        # copy and modify regular log file
        shutil.copyfile(sombrero_log_path, sombrero_incomplete_log_path)

        REQUIRED_FIELD = "flops_value"
        required_field_index = 0
        for line in fileinput.input(sombrero_incomplete_log_path, inplace=True):
            # find index of column to be removed
            if fileinput.isfirstline():
                LOG_FIELDS = line.strip().split("|")
                required_field_index = LOG_FIELDS.index(REQUIRED_FIELD)
            # remove a required field
            new_line = remove_field_from_perflog(line, required_field_index)
            # inline replacement
            print(new_line, end="\n")

    yield sombrero_log_path, sombrero_incomplete_log_path

    # teardown
    # clean unnecessary files and folders
    benchmark_cleanup(remove_test_logs)

# Test that perflog parsing works and information can be extracted to an appropriate DataFrame
def test_read_perflog(run_sombrero):

    sombrero_log_path, sombrero_incomplete_log_path = run_sombrero

    # check the sombrero log path is valid
    assert os.path.exists(sombrero_log_path)
    # if the incomplete log file hasn't been created, something went wrong
    assert os.path.exists(sombrero_incomplete_log_path)

    # check incomplete log is missing required fields
    try:
        post.read_perflog(sombrero_incomplete_log_path)
    except KeyError:
        assert True
    # if an error hasn't been thrown, something went wrong
    else:
        assert False

    # get dataframe from complete perflog
    df = post.read_perflog(sombrero_log_path)

    EXPECTED_FIELDS = ["job_completion_time", "version", "info", "jobid", "num_tasks", "num_cpus_per_task", "num_tasks_per_node", "num_gpus_per_node", "flops_value", "flops_unit", "flops_ref", "flops_lower_thres", "flops_upper_thres", "spack_spec", "test_name", "tasks", "cpus_per_task", "system", "partition", "environ", "extra_resources", "env_vars", "tags"]

    # check example perflog file is read appropriately
    # check all expected columns are present
    assert df.columns.tolist() == EXPECTED_FIELDS
    # check the expected number of rows is present
    assert len(df) == 4
    # check all cells in first row contain something
    assert all(df[column][0] != "" for column in df)
    # check test name matches
    assert df["test_name"][0] == "SombreroBenchmark"
    # check tags match
    assert df["tags"][0] == "example"

# Test that high-level control script works as expected
def test_high_level_script(run_sombrero):

    sombrero_log_path, sombrero_incomplete_log_path = run_sombrero
    post_ = post.PostProcessing()

    # check expected failure from invalid log file
    try:
        post_.run_post_processing(sombrero_incomplete_log_path, {})
    except FileNotFoundError:
        assert True
    else:
        assert False

    # check expected failure from lack of required columns
    try:
        post_.run_post_processing(sombrero_log_path, {"columns": []})
    except KeyError:
        assert True
    else:
        assert False

    # check expected failure from invalid column
    try:
        post_.run_post_processing(sombrero_log_path, {"columns": ["flops_value", "flops_unit", "fake_column"]})
    except KeyError:
        assert True
    else:
        assert False

    EXPECTED_FIELDS = ["flops_value", "flops_unit", "tasks"]

    # check expected failure from invalid filter column
    try:
        post_.run_post_processing(sombrero_log_path, {"columns": EXPECTED_FIELDS, "filters": [["fake_column", "==", 2]]})
    except KeyError:
        assert True
    else:
        assert False

    # check expected failure from invalid filter operator
    try:
        post_.run_post_processing(sombrero_log_path, {"columns": EXPECTED_FIELDS, "filters": [["tasks", "!!", 2]]})
    except KeyError:
        assert True
    else:
        assert False

    # check expected failure from invalid filter value type
    try:
        post_.run_post_processing(sombrero_log_path, {"columns": EXPECTED_FIELDS, "filters": [["flops_value", ">", 1]]})
    except ValueError:
        assert True
    else:
        assert False

    # check expected failure from filtering out every row
    try:
        post_.run_post_processing(sombrero_log_path, {"columns": EXPECTED_FIELDS, "filters": [["tasks", ">", 2]]})
    except EmptyDataError:
        assert True
    else:
        assert False

    # get collated dataframe subset
    df = post_.run_post_processing(Path(sombrero_incomplete_log_path).parent, {"columns": EXPECTED_FIELDS, "filters": [["tasks", ">", 1], ["cpus_per_task", "==", 2]]})

    # check returned subset is as expected
    assert df.columns.tolist() == EXPECTED_FIELDS
    assert len(df) == 1
