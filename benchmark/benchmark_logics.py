# ProcessScheduler benchmark
import sys
import time
from datetime import datetime
import subprocess
import os
import platform
import psutil
import uuid

import matplotlib.pyplot as plt
import processscheduler as ps
import z3

#
# Display machine identification
#
def get_size(byt, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    # Code from https://www.thepythoncode.com/article/get-hardware-system-information-python
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if byt < factor:
            return f"{byt:.2f}{unit}{suffix}"
        byt /= factor


bench_id = uuid.uuid4().hex
bench_date = datetime.now()
print("#### Benchmark information header ####")
print("Date:", bench_date)
print("Id:", bench_id)
print("Software:")
print("\tPython version:", platform.python_version())
print("\tProcessScheduler version:", ps.__VERSION__)
commit_short_hash = subprocess.check_output(
    ["git", "rev-parse", "--short", "HEAD"]
).strip()
print("\tz3 version:", z3.Z3_get_full_version())

print("\tProcessScheduler commit number:", commit_short_hash.decode("utf-8"))
os_info = os.uname()
print("OS:")
print("\tOS:", os_info.sysname)
print("\tOS Release:", os_info.release)
print("\tOS Version:", os_info.version)
print("Hardware:")
print("\tMachine:", os_info.machine)
print("\tPhysical cores:", psutil.cpu_count(logical=False))
print("\tTotal cores:", psutil.cpu_count(logical=True))
# CPU frequencies
cpufreq = psutil.cpu_freq()
print(f"\tMax Frequency: {cpufreq.max:.2f}Mhz")
print(f"\tMin Frequency: {cpufreq.min:.2f}Mhz")
# get the memory details
svmem = psutil.virtual_memory()
print(f"\tTotal memory: {get_size(svmem.total)}")

model_creation_times = []
computation_times = []

test_init_time = time.perf_counter()
all_logics = [
    "QF_LRA",
    "HORN",
    "QF_LIA",
    "QF_RDL",
    "QF_IDL",
    "QF_AUFLIA",
    "QF_ALIA",
    "QF_AUFLIRA",
    "QF_AUFNIA",
    "QF_AUFNIRA",
    "QF_ANIA",
    "QF_LIRA",
    "QF_UFLIA",
    "QF_UFLRA",
    "QF_UFIDL",
    "QF_UFRDL",
    "QF_NIRA",
    "QF_UFNRA",
    "QF_UFNIA",
    "QF_UFNIRA",
    "QF_S",
    "QF_SLIA",
    "UFIDL",
    "HORN",
    "QF_FPLRA",
]
# skipped: "QF_NIA",


num_dev_teams = 20
print("-> Num dev teams:", num_dev_teams)
# Teams and Resources
num_resource_a = 3
num_resource_b = 3

init_time = time.perf_counter()
# Resources
def get_problem():
    digital_transformation = ps.SchedulingProblem("DigitalTransformation")
    print("Create model...", end="")
    r_a = [ps.Worker("A_%i" % (i + 1)) for i in range(num_resource_a)]
    r_b = [ps.Worker("B_%i" % (i + 1)) for i in range(num_resource_b)]

    # Dev Team Tasks
    # For each dev_team pick one resource a and one resource b.
    ts_team_migration = [
        ps.FixedDurationTask("DevTeam_%i" % (i + 1), duration=1, priority=i % 3 + 1)
        for i in range(num_dev_teams)
    ]
    for t_team_migration in ts_team_migration:
        t_team_migration.add_required_resource(ps.SelectWorkers(r_a))
        t_team_migration.add_required_resource(ps.SelectWorkers(r_b))

    # solve
    digital_transformation.add_objective_priorities()
    digital_transformation.add_objective_flowtime()
    # digital_transformation.add_objective_makespan(weight=10)
    return digital_transformation


top1 = time.perf_counter()
mt = 60
results = {}
for logics in all_logics:
    digital_transformation = get_problem()
    top2 = time.perf_counter()
    solver = ps.SchedulingSolver(
        digital_transformation,
        logics=logics,
        random_values=False,
        parallel=False,
        max_time=10,
    )
    solution = solver.solve()
    if solution:
        flowtime_result = solution.indicators["FlowTime"]
        priority_result = solution.indicators["PriorityTotal"]
    else:
        flowtime_result, priority_result = None, None
    computing_time = time.perf_counter() - top2

    computation_times.append(computing_time)

    print("Logics:", logics, "Total Time:", computing_time)
    results[logics] = (computing_time, flowtime_result, priority_result)
test_final_time = time.perf_counter()
print("TOTAL BENCH TIME:", test_final_time - test_init_time)
print("Results:")
print(results)
