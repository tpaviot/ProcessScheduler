# Copyright (c) 2020-2021 Thomas Paviot (tpaviot@gmail.com)
#
# This file is part of ProcessScheduler.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


import processscheduler as ps


def test_json_export_1():
    pb = ps.SchedulingProblem(name="JSONExport1", horizon=10)
    # tasks
    task_1 = ps.FixedDurationTask(name="task1", duration=3)
    task_2 = ps.VariableDurationTask(name="task2")
    task_3 = ps.ZeroDurationTask(name="task3")

    # buffers
    buffer_1 = ps.NonConcurrentBuffer(name="Buffer1", initial_state=10)
    buffer_2 = ps.NonConcurrentBuffer(name="Buffer2", initial_state=0)

    # resources
    worker_1 = ps.Worker(name="Worker1")
    worker_2 = ps.Worker(name="Worker2")
    worker_3 = ps.Worker(name="Worker3")

    sw_1 = ps.SelectWorkers(list_of_workers=[worker_1, worker_2, worker_3])
    sw_2 = ps.SelectWorkers(list_of_workers=[worker_1, worker_2, worker_3])
    sw_3 = ps.SelectWorkers(list_of_workers=[worker_1, worker_2, worker_3])

    ps.CumulativeWorker(name="CumulMachine1", size=3)
    ps.CumulativeWorker(name="CumulMachine2", size=7)

    # assign resources to tasks
    task_1.add_required_resources([worker_1, worker_2])
    task_2.add_required_resource(sw_1)
    task_3.add_required_resource(sw_2)

    # task constraints
    ps.TaskPrecedence(task_before=task_1, task_after=task_2)
    ps.TaskStartAt(task=task_1, value=5)
    ps.TaskUnloadBuffer(task=task_1, buffer=buffer_1, quantity=3)
    ps.TaskLoadBuffer(task=task_1, buffer=buffer_2, quantity=2)

    # resource constraints
    ps.SameWorkers(select_workers_1=sw_1, select_workers_2=sw_2)
    ps.DistinctWorkers(select_workers_1=sw_2, select_workers_2=sw_3)
    ps.WorkLoad(
        resource=worker_1,
        dict_time_intervals_and_bound={(0, 6): 3, (19, 24): 4},
        kind="exact",
    )
    ps.ResourceUnavailable(resource=worker_1, list_of_time_intervals=[(1, 3), (6, 8)])
    ps.ResourceTasksDistance(
        resource=worker_1,
        distance=4,
        mode="exact",
        list_of_time_intervals=[[10, 18]],
    )

    # export to json
    solver = ps.SchedulingSolver(problem=pb)
    ps.export_json_to_file(pb, solver, "test_export_1.json")
