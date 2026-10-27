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
    elif v['model'] == 'document_submission':
        keys = ('application', 'employment_proof', 'confirmation', 'online')
        require(all(set(f) == set(keys) and all(type(x) is bool for x in f.values())
                    for f in facts), 'invalid document facts')

        def valid(f):
            return f['application'] and (f['employment_proof'] or f['confirmation']) and f['online']

        states = [dict(zip(keys, bits)) for bits in itertools.product([False, True], repeat=4)]
        require(sum(map(valid, states)) == 3, 'document rule inconsistency')
    elif v['model'] == 'tcp_handshake_ack':
        modulus = 2 ** 32
        require(all(type(v[k]) is int and 0 <= v[k] < modulus
                    for k in ('client_isn', 'server_isn')), 'invalid initial sequence number')
        require(v.get('syn_payload_bytes') == 0, 'this verifier assumes SYN without data')
        require(all(set(f) == {'ack'} and type(f['ack']) is int and 0 <= f['ack'] < modulus
                    for f in facts), 'invalid ACK choice')

        def valid(f):
            return f['ack'] == (v['server_isn'] + 1) % modulus

    elif v['model'] == 'tcp_data_ack':
        modulus = 2 ** 32
        require(type(v['sequence_start']) is int and 0 <= v['sequence_start'] < modulus,
                'invalid data sequence')
        require(type(v['payload_bytes']) is int and 0 < v['payload_bytes'] < modulus,
                'invalid payload length')
        require(v.get('prior_expected') == v['sequence_start'] and v.get('all_received_in_order') is True
                and v.get('syn') is False and v.get('fin') is False, 'unsupported data ACK conditions')
        require(all(set(f) == {'ack'} and type(f['ack']) is int and 0 <= f['ack'] < modulus
                    for f in facts), 'invalid ACK choice')

        def valid(f):
            return f['ack'] == (v['sequence_start'] + v['payload_bytes']) % modulus

    elif v['model'] == 'tcp_cumulative_ack':
        expected = v['initial_expected']
        require(type(expected) is int and 0 <= expected < 2 ** 32, 'invalid initial ACK')
        require(v.get('syn') is False and v.get('fin') is False, 'SYN/FIN not supported here')
        segments = v['received_segments']
        require(bool(segments), 'no received segments')
        for segment in segments:
            start, length = segment['seq'], segment['payload_bytes']
            require(type(start) is int and type(length) is int and start >= expected
                    and 0 < length <= 10000 and start + length < 2 ** 32,
                    'invalid/non-wrapping segment assumptions')
        for segment in sorted(segments, key=lambda item: item['seq']):
            if segment['seq'] > expected:
                break
            expected = max(expected, segment['seq'] + segment['payload_bytes'])
        require(all(set(f) == {'ack'} and type(f['ack']) is int and 0 <= f['ack'] < 2 ** 32
                    for f in facts), 'invalid cumulative ACK choice')

        def valid(f):
            return f['ack'] == expected

    elif v['model'] == 'manual_source_review':
        # Only checks consistency of recorded manual verdicts, not technical truth.
        require(bool(q.get('references')), 'missing technical references')
        for fact in facts:
            require(type(fact.get('supported')) is bool, 'missing manual verdict')
            require(bool(fact.get('reason')) and bool(fact.get('source_url')), 'missing manual rationale')

        def valid(f):
            return f['supported']

    elif v['model'] == 'text_lookup':
        require(isinstance(v.get('target'), str) and v['target'], 'missing lookup target')
        require(all(set(f) == {'value'} and isinstance(f['value'], str)
                    for f in facts), 'invalid text lookup facts')

        def valid(f):
            return f['value'] == v['target']

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
    print('Scope: rule models and consistency of recorded source-review verdicts; technical truth and natural language require manual review.')


if __name__ == '__main__':
    main()
