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

N = list(range(10, n, step))  # from 4 to N, step 2

# Teams and Resources
num_resource_a = 2
num_resource_b = 2

for num_dev_teams in N:
    print("-> Num dev teams:", num_dev_teams)
    init_time = time.perf_counter()
    # Resources
    digital_transformation = ps.SchedulingProblem(
        name="DigitalTransformation", horizon=num_dev_teams
    )
    r_a = [ps.Worker(name="A_%i" % (i + 1)) for i in range(num_resource_a)]
    r_b = [ps.Worker(name="B_%i" % (i + 1)) for i in range(num_resource_b)]

    # Dev Team Tasks
    # For each dev_team pick one resource a and one resource b.
    ts_team_migration = [
        ps.FixedDurationTask(name="DevTeam_%i" % (i + 1), duration=1, priority=10)
        for i in range(num_dev_teams)
    ]
    for t_team_migration in ts_team_migration:
        t_team_migration.add_required_resource(ps.SelectWorkers(list_of_workers=r_a))
        t_team_migration.add_required_resource(ps.SelectWorkers(list_of_workers=r_b))

    # create the solver and solve
    solver = ps.SchedulingSolver(
        problem=digital_transformation, max_time=mt, logics=args.logics
    )
    solution = solver.solve()

    if not solution:
        break

    computation_times.append(time.perf_counter() - init_time)
    plot_abs.append(num_dev_teams)

    solver.print_statistics()

plt.title(f"Benchmark SelectWorkers {bench_date}:{bench_id}")
plt.plot(plot_abs, computation_times, "D-", label="Computing time")
plt.legend()
plt.xlabel("n")
plt.ylabel("time(s)")
plt.grid(True)
plt.savefig(f"bench_dev_team_{bench_id}.svg")
if args.plot:
    plt.show()
