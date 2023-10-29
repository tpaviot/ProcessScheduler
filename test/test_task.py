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
import processscheduler.context as ps_context

from pydantic import ValidationError


def new_problem_or_clear() -> None:
    """clear the current context. If no context is defined,
    create a SchedulingProject object"""
    if ps_context.main_context is None:
        ps.SchedulingProblem(name="NewProblem")
    else:
        ps_context.main_context.clear()


class TestTask(unittest.TestCase):
    def test_clear_context(self) -> None:
        ps_context.main_context = None
        new_problem_or_clear()
        self.assertIsInstance(ps_context.main_context, ps.SchedulingContext)

    def test_create_task_without_problem(self) -> None:
        ps_context.main_context = None
        with self.assertRaises(AssertionError):
            ps.ZeroDurationTask(name="AZeroDurationTask")

    def test_create_task_zero_duration(self) -> None:
        ps.SchedulingProblem(name="ProblemWithoutHorizon")
        task = ps.ZeroDurationTask(name="zdt")
        self.assertIsInstance(task, ps.ZeroDurationTask)

    def test_create_task_fixed_duration(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask(name="fdt", duration=1)
        self.assertIsInstance(task, ps.FixedDurationTask)
        ps.FixedDurationTask(name="FloatDuration", duration=1.0)
        with self.assertRaises(ValidationError):
            ps.FixedDurationTask(name="NullInteger", duration=0)
        with self.assertRaises(ValidationError):
            ps.FixedDurationTask(name="NegativeInteger", duration=-1)
        ps.FixedDurationTask(name="FloatWorkAmount", duration=2, work_amount=1.0)
        with self.assertRaises(ValidationError):
            ps.FixedDurationTask(name="NegativeWorkAmount", duration=2, work_amount=-3)

    def test_create_task_variable_duration(self) -> None:
        pb = ps.SchedulingProblem(name="CreateVariableDurationTask")

        ps.VariableDurationTask(name="vdt1")
        vdt_2 = ps.VariableDurationTask(name="vdt2", max_duration=4)
        vdt_3 = ps.VariableDurationTask(name="vdt3", min_duration=5)

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks[vdt_2.name].duration <= 4)
        self.assertTrue(solution.tasks[vdt_3.name].duration >= 5)

    def test_create_task_variable_duration_from_list(self) -> None:
        pb = ps.SchedulingProblem(name="CreateVariableDurationTaskFromList")

        vdt_1 = ps.VariableDurationTask(name="vdt1", allowed_durations=[3, 4])
        vdt_2 = ps.VariableDurationTask(name="vdt2", allowed_durations=[5, 6])
        vdt_3 = ps.VariableDurationTask(name="vdt3", allowed_durations=[7, 8])

        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()

        self.assertTrue(solution)
        self.assertTrue(solution.tasks[vdt_1.name].duration in [3, 4])
        self.assertTrue(solution.tasks[vdt_2.name].duration in [5, 6])
        self.assertTrue(solution.tasks[vdt_3.name].duration in [7, 8])

    def test_task_types(self) -> None:
        new_problem_or_clear()
        with self.assertRaises(ValidationError):
            ps.VariableDurationTask(name="vdt5", max_duration=4.5)
        with self.assertRaises(ValidationError):
            ps.VariableDurationTask(name="vdt6", max_duration=-1)
        with self.assertRaises(ValidationError):
            ps.VariableDurationTask(name="vdt7", min_duration=-1)
        with self.assertRaises(ValidationError):
            ps.VariableDurationTask(name="vdt8", work_amount=-1)
        with self.assertRaises(ValidationError):
            ps.VariableDurationTask(name="vdt9", work_amount=1.5)
        with self.assertRaises(ValidationError):
            ps.VariableDurationTask(name="vdt10", work_amount=None)

    def test_task_same_names(self) -> None:
        new_problem_or_clear()
        ps.VariableDurationTask(name="t1")
        with self.assertRaises(ValueError):
            ps.VariableDurationTask(name="t1")

    def test_eq_overloading(self) -> None:
        new_problem_or_clear()
        task_1 = ps.ZeroDurationTask(name="task1")
        task_2 = ps.ZeroDurationTask(name="task2")
        self.assertEqual(task_1, task_1)
        self.assertNotEqual(task_1, task_2)

    def test_redondant_tasks_resources(self) -> None:
        pb = ps.SchedulingProblem(name="SameNameTasks")
        # we should not be able to add twice the same resource or task
        task_1 = ps.ZeroDurationTask(name="task1")
        self.assertEqual(list(pb._context.tasks), [task_1])
        self.assertEqual(list(pb._context.tasks), [task_1])
        # do the same for resources
        worker_1 = ps.Worker(name="Worker1")
        self.assertEqual(list(pb._context.resources), [worker_1])
        self.assertEqual(list(pb._context.resources), [worker_1])

    def test_resource_requirements(self) -> None:
        pb = ps.SchedulingProblem(name="ResourceRequirements")

        task_1 = ps.FixedDurationTask(name="task1", duration=3)
        worker_1 = ps.Worker(name="Worker1")
        worker_2 = ps.Worker(name="Worker2")
        worker_3 = ps.Worker(name="Worker3")
        worker_4 = ps.Worker(name="Worker4")
        task_1.add_required_resource(worker_1)
        task_1.add_required_resource(worker_2)
        task_1.add_required_resources([worker_3, worker_4])
        solver = ps.SchedulingSolver(problem=pb)
        solution = solver.solve()
        self.assertTrue(solution)
        self.assertEqual(len(solution.tasks["task1"].assigned_resources), 4)

    def test_wrong_assignement(self) -> None:
        new_problem_or_clear()
        task_1 = ps.FixedDurationTask(name="task1", duration=3)
        worker_1 = ps.Worker(name="Worker1")
        task_1.add_required_resource(worker_1)
        with self.assertRaises(TypeError):
            task_1.add_required_resource(3)
        with self.assertRaises(TypeError):
            task_1.add_required_resources("a_string")
        with self.assertRaises(ValueError):
            task_1.add_required_resource(worker_1)

    #
    # Single task constraints
    #
    def test_create_task_start_at(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask(name="task", duration=2)
        c = ps.TaskStartAt(task, 1)
        self.assertIsInstance(c, ps.TaskStartAt)
        self.assertEqual(c.value, 1)

    # def test_create_task_start_after_strict(self) -> None:
    #     new_problem_or_clear()
    #     task = ps.FixedDurationTask("task", 2)
    #     c = ps.TaskStartAfter(task, 3, kind="strict")
    #     self.assertIsInstance(c, ps.TaskStartAfter)
    #     self.assertEqual(c.value, 3)

    # def test_create_task_start_after_lax(self) -> None:
    #     new_problem_or_clear()
    #     task = ps.FixedDurationTask("task", 2)
    #     c = ps.TaskStartAfter(task, 3, kind="lax")
    #     self.assertIsInstance(c, ps.TaskStartAfter)
    #     self.assertEqual(c.value, 3)

    # def test_create_task_end_at(self) -> None:
    #     new_problem_or_clear()
    #     task = ps.FixedDurationTask("task", 2)
    #     c = ps.TaskEndAt(task, 3)
    #     self.assertIsInstance(c, ps.TaskEndAt)
    #     self.assertEqual(c.value, 3)

    # def test_create_task_before_strict(self) -> None:
    #     new_problem_or_clear()
    #     task = ps.FixedDurationTask("task", 2)
    #     c = ps.TaskEndBefore(task, 3, kind="strict")
    #     self.assertIsInstance(c, ps.TaskEndBefore)
    #     self.assertEqual(c.value, 3)

    # def test_create_task_before_lax(self) -> None:
    #     new_problem_or_clear()
    #     task = ps.FixedDurationTask("task", 2)
    #     constraint = ps.TaskEndBefore(task, 3, kind="lax")
    #     self.assertIsInstance(constraint, ps.TaskEndBefore)
    #     self.assertEqual(constraint.value, 3)

    # def test_task_duration_depend_on_start(self) -> None:
    #     pb = ps.SchedulingProblem("TaskDurationDependsOnStart", horizon=30)

    #     task_1 = ps.VariableDurationTask("Task1")
    #     task_2 = ps.VariableDurationTask("Task2")

    #     ps.TaskStartAt(task_1, 5)
    #     pb.add_constraint(task_1.duration == task_1.start * 3)

    #     ps.TaskStartAt(task_2, 11)
    #     pb.add_constraint(
    #         ps.if_then_else(
    #             task_2.start < 10, [task_2.duration == 3], [task_2.duration == 1]
    #         )
    #     )

    #     solver = ps.SchedulingSolver(pb)
    #     solution = solver.solve()
    #     self.assertTrue(solution)
    #     self.assertEqual(solution.tasks["Task1"].duration, 15)
    #     self.assertEqual(solution.tasks["Task2"].duration, 1)

    # #
    # # Two tasks constraints
    # #
    # def test_create_task_precedence_lax(self) -> None:
    #     new_problem_or_clear()
    #     t_1 = ps.FixedDurationTask("t1", duration=2)
    #     t_2 = ps.FixedDurationTask("t2", duration=3)
    #     precedence_constraint = ps.TaskPrecedence(t_1, t_2, offset=1, kind="lax")
    #     self.assertIsInstance(precedence_constraint, ps.TaskPrecedence)

    # def test_create_task_precedence_tight(self) -> None:
    #     new_problem_or_clear()
    #     t_1 = ps.FixedDurationTask("t1", duration=2)
    #     t_2 = ps.FixedDurationTask("t2", duration=3)
    #     precedence_constraint = ps.TaskPrecedence(t_1, t_2, offset=1, kind="tight")
    #     self.assertIsInstance(precedence_constraint, ps.TaskPrecedence)

    # def test_create_task_precedence_strict(self) -> None:
    #     pb = ps.SchedulingProblem("TaskPrecedenceStrict")
    #     t_1 = ps.FixedDurationTask("t1", duration=2)
    #     t_2 = ps.FixedDurationTask("t2", duration=3)
    #     ps.TaskPrecedence(t_1, t_2, offset=1, kind="strict")
    #     pb.add_objective_makespan()
    #     solver = ps.SchedulingSolver(pb)
    #     solution = solver.solve()
    #     self.assertTrue(solution)
    #     self.assertEqual(
    #         solution.tasks[t_2.name].start, solution.tasks[t_1.name].end + 2
    #     )

    # def test_create_task_precedence_raise_exception_kind(self) -> None:
    #     new_problem_or_clear()
    #     t_1 = ps.FixedDurationTask("t1", duration=2)
    #     t_2 = ps.FixedDurationTask("t2", duration=3)
    #     with self.assertRaises(ValueError):
    #         ps.TaskPrecedence(t_1, t_2, offset=1, kind="foo")

    # def test_create_task_precedence_raise_exception_offset_int(self) -> None:
    #     new_problem_or_clear()
    #     t_1 = ps.FixedDurationTask("t1", duration=2)
    #     t_2 = ps.FixedDurationTask("t2", duration=3)
    #     with self.assertRaises(ValueError):
    #         ps.TaskPrecedence(t_1, t_2, offset=1.5, kind="lax")  # should be int

    # def test_tasks_dont_overlap(self) -> None:
    #     pb = ps.SchedulingProblem("TasksDontOverlap")
    #     t_1 = ps.FixedDurationTask("t1", duration=7)
    #     t_2 = ps.FixedDurationTask("t2", duration=11)
    #     ps.TasksDontOverlap(t_1, t_2)
    #     pb.add_objective_makespan()
    #     solver = ps.SchedulingSolver(pb)
    #     solution = solver.solve()
    #     self.assertTrue(solution)
    #     self.assertEqual(solution.horizon, 18)

    # def test_tasks_start_sync(self) -> None:
    #     pb = ps.SchedulingProblem("TasksStartSync")
    #     t_1 = ps.FixedDurationTask("t1", duration=2)
    #     t_2 = ps.FixedDurationTask("t2", duration=3)
    #     ps.TaskStartAt(t_1, 7)
    #     ps.TasksStartSynced(t_1, t_2)
    #     solver = ps.SchedulingSolver(pb)
    #     solution = solver.solve()
    #     self.assertTrue(solution)
    #     self.assertEqual(solution.tasks[t_1.name].start, solution.tasks[t_2.name].start)

    # def test_tasks_end_sync(self) -> None:
    #     pb = ps.SchedulingProblem("TasksEndSync")
    #     t_1 = ps.FixedDurationTask("t1", duration=2)
    #     t_2 = ps.FixedDurationTask("t2", duration=3)
    #     ps.TasksEndSynced(t_1, t_2)
    #     solver = ps.SchedulingSolver(pb)
    #     solution = solver.solve()
    #     self.assertTrue(solution)
    #     self.assertEqual(solution.tasks[t_1.name].end, solution.tasks[t_2.name].end)

    # def test_schedule_n_task_raise_exception(self) -> None:
    #     new_problem_or_clear()
    #     with self.assertRaises(TypeError):
    #         ps.ScheduleNTasksInTimeIntervals(
    #             "list_of_tasks", 1, "list_of_time_intervals"
    #         )
    #     with self.assertRaises(TypeError):
    #         ps.ScheduleNTasksInTimeIntervals([], 1, "list_of_time_intervals")

    # #
    # # List of tasks constraints
    # #
    # def test_tasks_contiguous(self) -> None:
    #     pb = ps.SchedulingProblem("TasksContiguous")
    #     n = 7
    #     tasks_w1 = [ps.FixedDurationTask("t_w1_%i" % i, duration=3) for i in range(n)]
    #     tasks_w2 = [ps.FixedDurationTask("t_w2_%i" % i, duration=5) for i in range(n)]
    #     worker_1 = ps.Worker("Worker1")
    #     worker_2 = ps.Worker("Worker2")
    #     for t in tasks_w1:
    #         t.add_required_resource(worker_1)
    #     for t in tasks_w2:
    #         t.add_required_resource(worker_2)

    #     ps.TasksContiguous(tasks_w1 + tasks_w2)

    #     pb.add_objective_makespan()

    #     solver = ps.SchedulingSolver(pb)
    #     solution = solver.solve()
    #     self.assertTrue(solution)
    #     self.assertEqual(solution.horizon, 56)


if __name__ == "__main__":
    unittest.main()
