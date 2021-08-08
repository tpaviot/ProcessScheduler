# ProcessScheduler benchmark
import argparse
import time
from datetime import datetime
import subprocess
import platform
import uuid
import psutil

import matplotlib.pyplot as plt
import processscheduler as ps
import z3

#
# Argument parser
#
parser = argparse.ArgumentParser()
parser.add_argument(
    "-p", "--plot", default=True, help="Display results in a matplotlib chart"
)
parser.add_argument("-n", "--nmax", default=100, help="max dev team")
parser.add_argument("-s", "--step", default=10, help="step")
parser.add_argument(
    "-mt", "--max_time", default=60, help="Maximum time in seconds to find a solution"
)
parser.add_argument("-l", "--logics", default=None, help="SMT logics")

args = parser.parse_args()

n = int(args.nmax)  # max number of dev teams
mt = int(args.max_time)  # max time in seconds
step = int(args.step)

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


bench_id = uuid.uuid4().hex[:8]
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
os_info = platform.uname()
print("OS:")
print("\tOS:", os_info.system)
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

computation_times = []
plot_abs = []

MAX_TASKS_PER_PERIOD = 2
MAX_TASKS_IN_PROBLEM = 4
NB_WORKERS = 10
NB_TASKS_PER_WORKER = 10
for horizon in range(20, n, step):
    PERIODS = [
        (10 * i, 10 * (i + 1)) for i in range(int(horizon / 10))
    ]  # Periods of 10 slots from 0 to horizon
    init_time = time.perf_counter()

    # Create problem and initialize constraints
    pb = ps.SchedulingProblem(name="performance_analyzer", horizon=horizon)
    # Create resources and assign tasks
    general_worker = ps.Worker("general")
    workers = []
    for i in range(NB_WORKERS):
        name = f"worker_{i+1}"
        worker = ps.Worker(name)

        # Create tasks and assign resources
        tasks = []
        for j in range(NB_TASKS_PER_WORKER):
            tasks.append(
                ps.FixedDurationTask(f"{name}__{j:02d}", duration=1, optional=True)
            )
            tasks[-1].add_required_resources([general_worker, worker])

        workers.append({"name": name, "worker": worker, "tasks": tasks})

    workload = {period: MAX_TASKS_PER_PERIOD for period in PERIODS}
    workload[(0, horizon)] = MAX_TASKS_IN_PROBLEM
    
    for worker in workers:
        ps.WorkLoad(worker["worker"], workload, kind="max")

    # Add constraints, define objective and solve problem
    pb.add_objective_resource_utilization(general_worker)
    solver = ps.SchedulingSolver(pb)
    solution = solver.solve()
    if not solution:
        break

    computation_times.append(time.perf_counter() - init_time)
    plot_abs.append(i)

    solver.print_statistics()

plt.title("Benchmark_mixed_constraints %s:%s" % (bench_date, bench_id))
plt.plot(plot_abs, computation_times, "D-", label="Computing time")
plt.legend()
plt.xlabel("n")
plt.ylabel("time(s)")
plt.grid(True)
plt.savefig("bench_%s.svg" % bench_id)
if args.plot:
    plt.show()
