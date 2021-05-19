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
commit_short_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()
print("\tz3 version:", z3.Z3_get_full_version())

print("\tProcessScheduler commit number:", commit_short_hash.decode('utf-8'))
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

n = 30  # max number of dev teams

N = list(range(4, n, 2)) # from 4 to N, step 2

for num_dev_teams in N:
    print("-> Num dev teams:", num_dev_teams)
    # Teams and Resources
    num_resource_a = 2
    num_resource_b = 2

    init_time = time.perf_counter()
    # Resources
    digital_transformation = ps.SchedulingProblem('DigitalTransformation')
    r_a = [ps.Worker('A_%i' % (i + 1)) for i in range(num_resource_a)]
    r_b = [ps.Worker('B_%i' % (i + 1)) for i in range(num_resource_b)]

    # Dev Team Tasks
    # For each dev_team pick one resource a and one resource b.
    ts_team_migration = [ps.FixedDurationTask('DevTeam_%i' % (i + 1), duration=1, priority=10) for i in range(num_dev_teams)]
    for t_team_migration in ts_team_migration:
        t_team_migration.add_required_resource(ps.SelectWorkers(r_a))
        t_team_migration.add_required_resource(ps.SelectWorkers(r_b))

    # solve
    #digital_transformation.add_objective_priorities()
    digital_transformation.add_objective_makespan()

    top1 = time.perf_counter()
    model_creation_time = top1 - init_time

    #print("Teams: ", num_dev_teams)
    #print("Creating ")
    mt = 3
    solver = ps.SchedulingSolver(digital_transformation, random_seed=True, max_time=mt)
    #print("Done ok.")
    #print("Solve.")
    top2 = time.perf_counter()
    solution = solver.solve()

    computing_time = time.perf_counter() - top2
    if computing_time > mt:
        computing_time = computing_time - mt

    model_creation_times.append(model_creation_time)
    computation_times.append(computing_time)

    solver.print_statistics()

plt.title("Benchmark SelectWorkers %s:%s" % (bench_date, bench_id[8:]))
plt.plot(model_creation_times, label="Model creation")
plt.plot(computation_times, label="Computing time")
plt.legend()
plt.grid(True)
plt.show()
