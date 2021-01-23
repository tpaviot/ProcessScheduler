#Copyright 2020 Thomas Paviot (tpaviot@gmail.com)
#
#Licensed to the Apache Software Foundation (ASF) under one
#or more contributor license agreements.  See the NOTICE file
#distributed with this work for additional information
#regarding copyright ownership.  The ASF licenses this file
#to you under the Apache License, Version 2.0 (the
#"License"); you may not use this file except in compliance
#with the License.  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing,
#software distributed under the License is distributed on an
#"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#KIND, either express or implied.  See the License for the
#specific language governing permissions and limitations
#under the License.

import unittest

import processscheduler as ps
import processscheduler.context as ps_context

def new_problem_or_clear() -> None:
    """ clear the current context. If no context is defined,
    create a SchedulingProject object """
    if ps_context.main_context is None:
        ps.SchedulingProblem('NewProblem')
    else:
        ps_context.main_context.clear()

class TestFeatures(unittest.TestCase):
    def test_clear_context(self) -> None:
        ps_context.main_context = None
        new_problem_or_clear()
        self.assertIsInstance(ps_context.main_context, ps.SchedulingContext)

    def test_create_problem_with_horizon(self) -> None:
        pb = ps.SchedulingProblem('ProblemWithHorizon', horizon=10)
        self.assertIsInstance(pb, ps.SchedulingProblem)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem(4) # name not string
        with self.assertRaises(TypeError):
            ps.SchedulingProblem('NullIntegerHorizon', horizon=0)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem('FloatHorizon', horizon=3.5)
        with self.assertRaises(TypeError):
            ps.SchedulingProblem('NegativeIntegerHorizon', horizon=-2)

    def test_create_problem_without_horizon(self) -> None:
        ps.SchedulingProblem('ProblemWithoutHorizon')

    #
    # Tasks
    #
    def test_create_task_zero_duration(self) -> None:
        ps.SchedulingProblem('ProblemWithoutHorizon')
        ps.ZeroDurationTask('zdt')

    def test_create_task_fixed_duration(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask('fdt', 1)
        self.assertIsInstance(task, ps.FixedDurationTask)
        with self.assertRaises(TypeError):
            ps.FixedDurationTask('FloatDuration', 1.0)
        with self.assertRaises(TypeError):
            ps.FixedDurationTask('NullInteger', 0)
        with self.assertRaises(TypeError):
            ps.FixedDurationTask('NegativeInteger', -1)
        with self.assertRaises(TypeError):
            ps.FixedDurationTask('FloatWorkAmount', 2, work_amount=1.0)
        with self.assertRaises(TypeError):
            ps.FixedDurationTask('NegativeWorkAmount', 2, work_amount=-3)

    def test_create_task_variable_duration(self) -> None:
        new_problem_or_clear()
        ps.VariableDurationTask('vdt1')
        ps.VariableDurationTask('vdt2', length_at_most=4)
        ps.VariableDurationTask('vdt3', length_at_least=4)
        ps.VariableDurationTask('vdt4', work_amount=10)

    def test_task_types(self) -> None:
        new_problem_or_clear()
        with self.assertRaises(TypeError):
            ps.VariableDurationTask('vdt5', length_at_most=4.5)
        with self.assertRaises(TypeError):
            ps.VariableDurationTask('vdt6', length_at_most=-1)
        with self.assertRaises(TypeError):
            ps.VariableDurationTask('vdt7', length_at_least=-1)
        with self.assertRaises(TypeError):
            ps.VariableDurationTask('vdt8', work_amount=-1)
        with self.assertRaises(TypeError):
            ps.VariableDurationTask('vdt9', work_amount=1.5)
        with self.assertRaises(TypeError):
            ps.VariableDurationTask('vdt10', work_amount=None)

    def test_task_same_names(self) -> None:
        new_problem_or_clear()
        ps.VariableDurationTask('t1')
        with self.assertRaises(ValueError):
            ps.VariableDurationTask('t1')
    #
    # Workers
    #
    def test_create_worker(self) -> None:
        new_problem_or_clear()
        worker = ps.Worker('wkr')
        self.assertIsInstance(worker, ps.Worker)
        with self.assertRaises(TypeError):
            ps.Worker('WorkerNegativeIntProductivity', productivity=-3)
        with self.assertRaises(TypeError):
            ps.Worker('WorkerFloatProductivity', productivity=3.14)

    def test_create_select_workers(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker('wkr_1')
        worker_2 = ps.Worker('wkr_2')
        worker_3 = ps.Worker('wkr_3')
        single_alternative_workers = ps.SelectWorkers([worker_1,
                                                            worker_2], 1)
        self.assertIsInstance(single_alternative_workers,
                              ps.SelectWorkers)
        double_alternative_workers = ps.SelectWorkers([worker_1,
                                                            worker_2,
                                                            worker_3], 2)
        self.assertIsInstance(double_alternative_workers,
                              ps.SelectWorkers)

    def test_worker_wrong_number_of_workers(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker('wkr_1')
        worker_2 = ps.Worker('wkr_2')
        ps.SelectWorkers([worker_1, worker_2], 2)
        ps.SelectWorkers([worker_1, worker_2], 1)
        with self.assertRaises(ValueError):
            ps.SelectWorkers([worker_1, worker_2], 3)
        with self.assertRaises(TypeError):
            ps.SelectWorkers([worker_1, worker_2], -1)

    def test_worker_same_name(self) -> None:
        new_problem_or_clear()
        worker_1 = ps.Worker('wkr_1')
        self.assertIsInstance(worker_1, ps.Worker)
        with self.assertRaises(ValueError):
            ps.Worker('wkr_1')

    def test_eq_overloading(self) -> None:
        new_problem_or_clear()
        task_1 = ps.ZeroDurationTask('task1')
        task_2 = ps.ZeroDurationTask('task2')
        self.assertEqual(task_1, task_1)
        self.assertNotEqual(task_1, task_2)

    def test_redondant_tasks_resources(self) -> None:
        pb = ps.SchedulingProblem('SameNameTasks')
        # we should not be able to add twice the same resource or task
        task_1 = ps.ZeroDurationTask('task1')
        self.assertEqual(list(pb.context.tasks), [task_1])
        self.assertEqual(list(pb.context.tasks), [task_1])
        # do the same for resources
        worker_1 = ps.Worker('Worker1')
        self.assertEqual(list(pb.context.resources), [worker_1])
        self.assertEqual(list(pb.context.resources), [worker_1])

    def test_resource_requirements(self) -> None:
        new_problem_or_clear()
        task_1 = ps.FixedDurationTask('task1', duration=3)
        worker_1 = ps.Worker('Worker1')
        worker_2 = ps.Worker('Worker2')
        worker_3 = ps.Worker('Worker3')
        worker_4 = ps.Worker('Worker4')
        task_1.add_required_resource(worker_1)
        task_1.add_required_resource(worker_2)
        task_1.add_required_resources([worker_3, worker_4])

    def test_wrong_assignement(self) -> None:
        new_problem_or_clear()
        task_1 = ps.FixedDurationTask('task1', duration=3)
        worker_1 = ps.Worker('Worker1')
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
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskStartAt(task, 1)
        self.assertIsInstance(c, ps.TaskStartAt)
        self.assertEqual(c.value, 1)

    def test_create_task_start_after_strict(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskStartAfterStrict(task, 3)
        self.assertIsInstance(c, ps.TaskStartAfterStrict)
        self.assertEqual(c.value, 3)

    def test_create_task_start_after_lax(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskStartAfterLax(task, 3)
        self.assertIsInstance(c, ps.TaskStartAfterLax)
        self.assertEqual(c.value, 3)

    def test_create_task_end_at(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskEndAt(task, 3)
        self.assertIsInstance(c, ps.TaskEndAt)
        self.assertEqual(c.value, 3)

    def test_create_task_before_strict(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask('task', 2)
        c = ps.TaskEndBeforeStrict(task, 3)
        self.assertIsInstance(c, ps.TaskEndBeforeStrict)
        self.assertEqual(c.value, 3)

    def test_create_task_before_lax(self) -> None:
        new_problem_or_clear()
        task = ps.FixedDurationTask('task', 2)
        constraint = ps.TaskEndBeforeLax(task, 3)
        self.assertIsInstance(constraint, ps.TaskEndBeforeLax)
        self.assertEqual(constraint.value, 3)

    #
    # Two tasks constraints
    #
    def test_tasks_dont_overlap(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', duration=2)
        t_2 = ps.FixedDurationTask('t2', duration=3)
        constraint = ps.TasksDontOverlap(t_1, t_2)
        self.assertIsInstance(constraint, ps.TasksDontOverlap)

    def test_tasks_start_sync(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', duration=2)
        t_2 = ps.FixedDurationTask('t2', duration=3)
        constraint = ps.TasksStartSynced(t_1, t_2)
        self.assertIsInstance(constraint, ps.TasksStartSynced)

    def test_tasks_end_sync(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', duration=2)
        t_2 = ps.FixedDurationTask('t2', duration=3)
        constraint = ps.TasksEndSynced(t_1, t_2)
        self.assertIsInstance(constraint, ps.TasksEndSynced)

    #
    # Boolean operators
    #
    def test_operator_not_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', duration=2)
        not_constraint = ps.not_(ps.TaskStartAt(t_1, 1))
        self.assertIsInstance(not_constraint, ps.BoolRef)

    def test_operator_or_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', duration=2)
        or_constraint = ps.or_([ps.TaskStartAt(t_1, 1),
                                ps.TaskStartAt(t_1, 2)])
        self.assertIsInstance(or_constraint, ps.BoolRef)

    def test_operator_xor_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', duration=2)
        xor_constraint = ps.xor_([ps.TaskStartAt(t_1, 1),
                                  ps.TaskStartAt(t_1, 2)])
        self.assertIsInstance(xor_constraint, ps.BoolRef)

    def test_operator_and_(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', duration=2)
        and_constraint = ps.and_([ps.TaskStartAfterLax(t_1, 1),
                                  ps.TaskEndBeforeLax(t_1, 7)])
        self.assertIsInstance(and_constraint, ps.BoolRef)

    def test_nested_boolean_operators(self) -> None:
        new_problem_or_clear()
        t_1 = ps.VariableDurationTask('t1')
        or_constraint_1 = ps.or_([ps.TaskStartAt(t_1, 1),
                                  ps.TaskStartAt(t_1, 2)])
        or_constraint_2 = ps.or_([ps.TaskStartAt(t_1, 4),
                                  ps.TaskStartAt(t_1, 5)])
        and_constraint = ps.and_([or_constraint_1, or_constraint_2])
        self.assertIsInstance(and_constraint, ps.BoolRef)

    def test_add_constraint(self) -> None:
        pb = ps.SchedulingProblem('AddConstraint')
        t_1 = ps.FixedDurationTask('t1', duration=2)
        or_constraint = ps.or_([ps.TaskStartAt(t_1, 1),
                               ps.TaskStartAt(t_1, 2)])
        not_constraint = ps.not_(ps.TaskEndAt(t_1, 5))
        self.assertIsInstance(or_constraint, ps.BoolRef)
        self.assertIsInstance(not_constraint, ps.BoolRef)
        pb.add_constraint(or_constraint)
        pb.add_constraint(not_constraint)

    #
    # Implies
    #
    def test_implies(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', 2)
        t_2 = ps.FixedDurationTask('t2', 2)
        implies_constraint = ps.implies(t_1.start==1, [ps.TaskStartAt(t_2, 3)])
        self.assertIsInstance(implies_constraint, ps.BoolRef)

    #
    # If/Then/Else
    #
    def test_if_then_else(self) -> None:
        new_problem_or_clear()
        t_1 = ps.FixedDurationTask('t1', 2)
        t_2 = ps.FixedDurationTask('t2', 2)
        ite_constraint = ps.if_then_else(t_1.start==1, # condition
                                         [ps.TaskStartAt(t_2, 3)], # then
                                         [ps.TaskStartAt(t_2, 6)]) # else
        self.assertIsInstance(ite_constraint, ps.BoolRef)

    #
    # Indicators
    #
    def test_create_indicator(self) -> None:
        pb = ps.SchedulingProblem('CreateIndicator', horizon=3)
        i_1 = ps.Indicator('SquareHorizon', pb.horizon ** 2)  # ArithRef
        self.assertIsInstance(i_1, ps.Indicator)
        i_2 = ps.Indicator('IsLooooong ?', pb.horizon > 1000)  # BoolRef
        self.assertIsInstance(i_2, ps.Indicator)
        with self.assertRaises(TypeError):
            ps.Indicator('foo', 4)


if __name__ == "__main__":
    unittest.main()
