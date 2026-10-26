"""Validate question structure and explicit condition models; never print answers.

Run from any directory: python scripts/verify_questions.py
Natural-language to model correspondence still requires manual review.
"""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'id', 'domain', 'subtype', 'difficulty', 'passage', 'prompt', 'choices',
    'answer', 'explanation', 'quick_solution', 'recommended_seconds',
    'source_type', 'review_status', 'manual_review', 'verification',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(q, seen):
    require(REQUIRED <= q.keys(), 'missing fields')
    require(q['id'] not in seen, 'duplicate ID')
    seen.add(q['id'])
    require(all(isinstance(q[k], str) and q[k].strip() for k in
                ['id', 'domain', 'subtype', 'difficulty', 'passage', 'prompt',
                 'explanation', 'quick_solution', 'source_type']), 'empty text')
    choices = q['choices']
    require(isinstance(choices, list) and len(choices) >= 2, 'invalid choices')
    require(all(isinstance(x, str) and x.strip() for x in choices), 'empty choice')
    normalized = [''.join(x.split()).rstrip('.。') for x in choices]
    require(len(set(normalized)) == len(choices), 'duplicate choice text')
    require(type(q['answer']) is int and 1 <= q['answer'] <= len(choices), 'invalid answer')
    require(type(q['recommended_seconds']) is int and q['recommended_seconds'] > 0, 'invalid recommended time')
    require(q['review_status'] == 'passed' and q['manual_review']['status'] == 'passed', 'not approved for use')
    v = q['verification']
    facts = v['choice_facts']
    require(len(facts) == len(choices), 'model/choice count mismatch')
    require(len({json.dumps(f, sort_keys=True) for f in facts}) == len(facts), 'duplicate choice facts')
    if v['model'] == 'submission_window':
        start = v['start_hour']
        end = v['end_hour']
        require(0 <= end <= 23, 'invalid end time')
        require(start is None or 0 <= start <= end, 'contradictory time window')

        def valid(f):
            return (f['weekday'] == v['required_weekday']
                    and (start is None or f['hour'] >= start)
                    and f['hour'] <= end
                    and f['method'] == v['required_method'])

        require(all(type(f['hour']) is int and 0 <= f['hour'] <= 23 for f in facts), 'invalid choice time')
        require(valid({'weekday': v['required_weekday'], 'hour': end,
                       'method': v['required_method']}), 'inconsistent boundary')
        if start is not None:
            require(valid({'weekday': v['required_weekday'], 'hour': start,
                           'method': v['required_method']}), 'inconsistent boundary')
    elif v['model'] == 'room_access':
        require(all(set(f) == {'reserved', 'external', 'approved'} and
                    all(type(x) is bool for x in f.values()) for f in facts), 'invalid boolean facts')

        def valid(f):
            return f['reserved'] and (not f['external'] or f['approved'])

        states = [dict(zip(['reserved', 'external', 'approved'], bits))
                  for bits in itertools.product([False, True], repeat=3)]
        # Independent denial-rule expression checks every possible state.
        for state in states:
            denied = (not state['reserved']) or (state['external'] and not state['approved'])
            require(valid(state) == (not denied), 'truth-table mismatch')
        require(any(map(valid, states)), 'unsatisfiable rules')
    else:
        raise ValueError('unsupported model; add a verifier before release')
    winners = [i for i, fact in enumerate(facts, 1) if valid(fact)]
    require(len(winners) == 1, 'answer not unique or no valid choice')
    require(winners[0] == q['answer'], 'answer/model mismatch')
    if q.get('kind') == 'practice':
        student = ROOT / 'questions' / (q['id'] + '.md')
        require(student.is_file(), 'missing student file')
        content = student.read_text(encoding='utf-8')
        require(q['passage'] in content and q['prompt'] in content, 'student passage/prompt mismatch')
        for i, choice in enumerate(choices, 1):
            require(f'{i}. {choice}' in content, 'student choice mismatch')
        require('정답:' not in content and '정답은' not in content and '상세 해설' not in content, 'possible answer leak')


def main():
    files = sorted((ROOT / 'questions' / '_instructor').glob('*.json'))
    require(bool(files), 'no questions found')
    seen, failures = set(), []
    for path in files:
        try:
            q = json.loads(path.read_text(encoding='utf-8'))
            require(path.stem == q.get('id'), 'filename/ID mismatch')
            check(q, seen)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            failures.append((path.stem, str(exc)))
    for qid, message in failures:
        print(f'FAIL {qid}: {message}')
    if failures:
        raise SystemExit(1)
    print(f'PASS: {len(files)} items; schema, unique choices, satisfiable models, unique answers, student text checked.')
    print('Scope: explicit rule models only; natural-language correspondence requires manual review.')


if __name__ == '__main__':
    main()
