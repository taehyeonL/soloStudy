"""Focused checks for weekend scheduling and RC diagnostic counts."""
import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import study_manager as manager


class DailyProgressTests(unittest.TestCase):
    def test_workload_counts_wrong_answers_excludes_pending_and_caps_extra(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sessions').mkdir()
            (root / 'subjects/daily_plans').mkdir(parents=True)
            day = date(2026, 10, 27)
            target = {'targets': {'review': 3, 'ncs': 1, 'cs_security': 4, 'wrapup': 1}}
            (root / 'subjects/daily_plans/2026-10-27.json').write_text(json.dumps(target), encoding='utf-8')
            tracks = [('review', 'computer-science')] * 3 + [('first', 'ncs')] + [('first', 'computer-science')] * 3
            attempts = [{'attempt_id': str(i), 'kind': kind, 'exam_track': track, 'correct': False}
                        for i, (kind, track) in enumerate(tracks)]
            session = {'date': day.isoformat(), 'status': 'active', 'attempts': attempts, 'pending_question_id': 'Q-next'}
            path = root / 'sessions/2026-10-27.json'
            path.write_text(json.dumps(session), encoding='utf-8')
            with patch.object(manager, 'ROOT', root):
                result = manager.daily_progress(day)
                self.assertEqual((result['done'], result['total'], result['percent']), (7, 9, 77.8))
                self.assertIsNone(result['time_progress_percent'])
                attempts.extend([{'attempt_id': 'next' + str(i), 'kind': 'first', 'exam_track': 'computer-science', 'correct': True} for i in range(2)])
                session['status'] = 'completed'
                path.write_text(json.dumps(session), encoding='utf-8')
                result = manager.daily_progress(day)
                self.assertEqual(result['percent'], 100)
                self.assertEqual(result['extra_tasks'], 1)

    def test_no_plan_does_not_invent_percentage(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(manager, 'ROOT', Path(folder)):
            self.assertIsNone(manager.daily_progress(date(2026, 10, 27))['percent'])


class WeekendStudyTests(unittest.TestCase):
    def setUp(self):
        self.profile = manager.read_json(manager.ROOT / 'study_profile.json')

    def test_weekday_excludes_toeic_without_removing_weekly_budget(self):
        result = manager.plan(self.profile, {'events': []}, date(2026, 10, 27))
        self.assertEqual(result['minutes'], {'ncs': 360, 'cs_security': 360, 'toeic': 120})
        self.assertEqual(result['daily_available_groups'], ['ncs', 'cs_security'])
        self.assertEqual(result['next_toeic_study_date'], '2026-10-31')
        self.assertEqual(result['toeic_weekend_questions_target'], 50)

    def test_weekend_and_goal_secured(self):
        result = manager.plan(self.profile, {'events': []}, date(2026, 10, 31), 7)
        self.assertTrue(result['toeic_today_included'])
        self.assertEqual(sum(result['minutes'].values()), 420)
        profile = copy.deepcopy(self.profile)
        profile['toeic'].update(confirmed_official_score=750, score_evidence_confirmed=True)
        result = manager.plan(profile, {'events': []}, date(2026, 10, 31))
        self.assertEqual(result['minutes'], {'ncs': 420, 'cs_security': 420, 'toeic': 0})
        self.assertFalse(result['toeic_today_included'])
        self.assertEqual(result['toeic_weekend_questions_target'], 0)

    def test_nominal_and_execution_dates(self):
        nominal = date(2026, 10, 28)
        self.assertEqual(manager.toeic_review_date(nominal), date(2026, 10, 31))
        self.assertEqual(nominal, date(2026, 10, 28))
        self.assertEqual(manager.toeic_review_date(date(2026, 11, 1)), date(2026, 11, 1))

    def test_diagnostic_counts_exclude_reviews_and_other_sets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sessions').mkdir()
            (root / 'subjects/toeic').mkdir(parents=True)
            (root / 'study_profile.json').write_text(json.dumps(self.profile), encoding='utf-8')
            (root / 'subjects/toeic/sets.json').write_text(json.dumps({'sets': [{'set_id': 'S1'}]}), encoding='utf-8')
            attempts = [
                {'attempt_id': 'A1', 'exam_track': 'toeic', 'kind': 'first', 'study_set_id': 'S1', 'question_id': 'Q1', 'correct': False, 'part': 'part5', 'skill_tags': ['agreement']},
                {'attempt_id': 'A2', 'exam_track': 'toeic', 'kind': 'first', 'study_set_id': 'S1', 'question_id': 'Q2', 'correct': True, 'part': 'part5', 'skill_tags': ['agreement']},
                {'attempt_id': 'A3', 'exam_track': 'toeic', 'kind': 'review', 'study_set_id': 'S1', 'question_id': 'Q1', 'correct': True, 'skill_tags': ['agreement']},
                {'attempt_id': 'A4', 'exam_track': 'toeic', 'kind': 'first', 'study_set_id': 'S2', 'question_id': 'Q3', 'correct': True, 'skill_tags': ['vocabulary']},
            ]
            (root / 'sessions/test.json').write_text(json.dumps({'attempts': attempts}), encoding='utf-8')
            with patch.object(manager, 'ROOT', root):
                result = manager.toeic_report('S1')
            self.assertEqual(result['answered'], 2)
            self.assertEqual(result['skills']['agreement']['accuracy'], 0.5)
            self.assertTrue(result['skills']['agreement']['small_sample'])
            self.assertEqual(result['wrong_question_ids'], ['Q1'])
            self.assertIsNone(result['toeic_score_estimate'])


if __name__ == '__main__':
    unittest.main()
