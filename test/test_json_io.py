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

import unittest

import processscheduler as ps


class TestJsonImportExport(unittest.TestCase):
    def test_json_export_1(self):
        pb = ps.SchedulingProblem("ConsumeFeedBuffer1", horizon=10)
        # tasks
        task_1 = ps.FixedDurationTask("task1", duration=3)
        task_2 = ps.VariableDurationTask("task2")
        task_3 = ps.ZeroDurationTask("task3")
        # buffers
        buffer_1 = ps.NonConcurrentBuffer("Buffer1", initial_state=10)
        buffer_2 = ps.NonConcurrentBuffer("Buffer2", initial_state=0)
        # resources
        worker_1 = ps.Worker("Worker1")
        worker_2 = ps.Worker("Worker2")
        sw = ps.SelectWorkers([worker_1, worker_2])
        cumul1 = ps.CumulativeWorker("CumulMachine1", size=3)
        cumul2 = ps.CumulativeWorker("CumulMachine2", size=7)

        solver = ps.SchedulingSolver(pb)

        ps.export_json(pb, solver, "popo")


if __name__ == "__main__":
    unittest.main()
