"""Read-only integrated study planning/statistics. No answers or credentials printed."""
import argparse
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ('ncs', 'cs_security', 'toeic')
TRACKS = ('ncs', 'computer-science', 'security-written', 'security-practical', 'toeic')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def allocate(total, weights):
    raw = [total * w / sum(weights) for w in weights]
    values = [math.floor(v) for v in raw]
    for i in sorted(range(len(raw)), key=lambda i: (raw[i] - values[i], -i), reverse=True)[:total-sum(values)]:
        values[i] += 1
    return dict(zip(GROUPS, values))


def toeic_review_date(nominal_due):
    """Preserve the nominal deadline; return its eligible weekend execution date."""
    return nominal_due if nominal_due.weekday() >= 5 else nominal_due + timedelta(days=5-nominal_due.weekday())


def plan(profile, schedule, today, hours=None):
    hours = profile['weekly_hours'] if hours is None else hours
    if not math.isfinite(hours) or hours <= 0:
        raise ValueError('weekly hours must be a positive finite number')
    total = round(hours * 60)
    if total < 1:
        raise ValueError('at least one minute is required')
    toeic = profile['toeic']
    score = toeic.get('confirmed_official_score')
    threshold = max(toeic['target_score_range'][0], toeic.get('confirmed_institution_requirement') or 0)
    secured = (isinstance(score, (int, float)) and 10 <= score <= 990
               and toeic.get('score_evidence_confirmed') is True and score >= threshold)
    weights = [7, 7, 0] if secured else [6, 6, 2]
    minutes = allocate(total, weights)
    candidates = []
    for event in schedule.get('events', []):
        if event.get('status') != 'confirmed' or not event.get('official_source_url') or not event.get('verified_on'):
            continue
        days = (date.fromisoformat(event['exam_date']) - today).days
        group = event.get('allocation_group')
        if 0 <= days <= profile['scheduling']['imminent_days'] and group in GROUPS:
            if group == 'toeic' and secured:
                continue
            candidates.append((days, event.get('id', ''), group))
    reason = 'base allocation; TOEIC secured' if secured else 'base allocation'
    if candidates:
        days, event_id, group = min(candidates)
        donors = [g for g in GROUPS if g != group and minutes[g] > 0]
        transfer = min(round(total / 7), sum(minutes[g] for g in donors))
        # Proportional donor reduction; last donor absorbs rounding remainder.
        remaining, donor_total = transfer, sum(minutes[g] for g in donors)
        for index, donor in enumerate(donors):
            take = remaining if index == len(donors)-1 else round(transfer * minutes[donor] / donor_total)
            take = min(take, minutes[donor])
            minutes[donor] -= take
            remaining -= take
        minutes[group] += transfer - remaining
        reason = f'confirmed exam {event_id} in {days} days; temporary priority'
    weekend_only = toeic.get('study_mode') == 'weekend_rc_diagnostic'
    weekend = today.weekday() >= 5
    eligible = [g for g in GROUPS if minutes[g] > 0
                and not (g == 'toeic' and weekend_only and not weekend)]
    return {'weekly_minutes': total, 'minutes': minutes, 'toeic_target_secured': secured,
            'daily_available_groups': eligible,
            'toeic_weekend_questions_target': 0 if secured else toeic.get('questions_per_weekend', 0),
            'toeic_weekend_only': weekend_only,
            'toeic_today_included': 'toeic' in eligible,
            'next_toeic_study_date': None if secured else (toeic_review_date(today) if weekend_only else today).isoformat(),
            'reason': reason, 'as_of': today.isoformat(), 'preview_only': True}


def stats(subject=None):
    result = {track: {'first_attempts': 0, 'correct': 0, 'incorrect': 0,
                      'unresolved': 0, 'review_attempts': 0, 'rubric_attempts': 0,
                      'rubric_earned': 0, 'rubric_max': 0} for track in TRACKS}
    seen = set()
    for path in sorted((ROOT / 'sessions').glob('*.json')):
        session = read_json(path)
        if session.get('_template_only'):
            continue
        for attempt in session.get('attempts', []):
            key = attempt.get('attempt_id')
            if not key or key in seen:
                raise ValueError('missing or duplicate attempt_id; resolve records before reporting')
            seen.add(key)
            track = attempt.get('exam_track')
            if track is None and attempt.get('question_id', '').startswith('NCS-'):
                track = 'ncs'  # Legacy compatibility; originals stay unchanged.
            if track not in result:
                raise ValueError('unknown exam_track; do not silently classify')
            row = result[track]
            if attempt.get('kind') == 'review':
                row['review_attempts'] += 1
                continue
            if attempt.get('kind') != 'first':
                raise ValueError('invalid attempt kind')
            row['first_attempts'] += 1
            if attempt.get('scoring_format') == 'rubric':
                row['rubric_attempts'] += 1
                if attempt.get('grading_uncertain') or attempt.get('score') is None:
                    row['unresolved'] += 1
                else:
                    earned, maximum = attempt['score'], attempt['max_score']
                    if not 0 <= earned <= maximum or maximum <= 0:
                        raise ValueError('invalid rubric score')
                    row['rubric_earned'] += earned
                    row['rubric_max'] += maximum
            elif attempt.get('correct') is True:
                row['correct'] += 1
            elif attempt.get('correct') is False:
                row['incorrect'] += 1
            else:
                row['unresolved'] += 1
    for row in result.values():
        graded = row['correct'] + row['incorrect']
        row['accuracy'] = row['correct'] / graded if graded else None
        row['rubric_ratio'] = row['rubric_earned'] / row['rubric_max'] if row['rubric_max'] else None
    return {subject: result[subject]} if subject else result


def daily_progress(today):
    """Task completion, never elapsed-time completion or mastery."""
    path = ROOT / 'subjects/daily_plans' / (today.isoformat() + '.json')
    if not path.is_file():
        return {'date': today.isoformat(), 'configured': False, 'percent': None,
                'note': 'Set explicit daily targets before calculating progress.'}
    daily = read_json(path)
    targets = daily['targets']
    if set(targets) != {'review', 'ncs', 'cs_security', 'wrapup'} or any(
            type(v) is not int or v < 0 for v in targets.values()) or sum(targets.values()) == 0:
        raise ValueError('invalid daily workload targets')
    actual = dict.fromkeys(targets, 0)
    sessions, seen = [], set()
    for session_path in sorted((ROOT / 'sessions').glob(today.isoformat() + '*.json')):
        session = read_json(session_path)
        if session.get('date') != today.isoformat() or session.get('_template_only'):
            continue
        sessions.append(session)
        for attempt in session.get('attempts', []):
            key = attempt.get('attempt_id')
            if not key or key in seen:
                raise ValueError('missing or duplicate daily attempt ID')
            seen.add(key)
            graded = type(attempt.get('correct')) is bool or (
                attempt.get('score') is not None and not attempt.get('grading_uncertain'))
            if not graded:
                continue
            track = attempt.get('exam_track')
            if track is None and attempt.get('question_id', '').startswith('NCS-'):
                track = 'ncs'
            if attempt.get('kind') == 'review' and track != 'toeic':
                actual['review'] += 1
            elif attempt.get('kind') == 'first':
                if track == 'ncs':
                    actual['ncs'] += 1
                elif track in ('computer-science', 'security-written', 'security-practical'):
                    actual['cs_security'] += 1
    actual['wrapup'] = int(bool(sessions) and all(s.get('status') in ('completed', 'interrupted')
                            for s in sessions) and any(s.get('status') == 'completed' for s in sessions))
    completed = {key: min(actual[key], targets[key]) for key in targets}
    total = sum(targets.values())
    done = sum(completed.values())
    return {'date': today.isoformat(), 'configured': True, 'targets': targets,
            'completed': completed, 'actual': actual, 'done': done, 'total': total,
            'percent': round(100 * done / total, 1), 'time_progress_percent': None,
            'extra_tasks': sum(max(0, actual[k] - targets[k]) for k in targets),
            'note': 'Graded work counts regardless of correctness; pending questions do not. Workload is not mastery or measured time.'}


def toeic_report(set_id=None):
    """Diagnostic counts only; no answer key or unofficial TOEIC score conversion."""
    config = read_json(ROOT / 'study_profile.json')['toeic']
    registry = read_json(ROOT / 'subjects/toeic/sets.json')
    if set_id is not None and set_id not in {item['set_id'] for item in registry['sets']}:
        raise ValueError('unknown study set; register the set before reporting')
    rows, seen, answered, wrong_ids = {}, set(), 0, []
    parts = {}
    for path in sorted((ROOT / 'sessions').glob('*.json')):
        session = read_json(path)
        if session.get('_template_only'):
            continue
        for attempt in session.get('attempts', []):
            if attempt.get('exam_track') != 'toeic' or attempt.get('kind') != 'first':
                continue
            if set_id is not None and attempt.get('study_set_id') != set_id:
                continue
            key = attempt.get('attempt_id')
            if not key or key in seen:
                raise ValueError('missing or duplicate TOEIC attempt ID')
            seen.add(key)
            correct = attempt.get('correct')
            if type(correct) is not bool:
                continue  # Unresolved grades do not enter accuracy.
            answered += 1
            qid = attempt.get('question_id', '')
            metadata_path = ROOT / 'questions/_instructor' / (qid + '.json')
            metadata = read_json(metadata_path) if metadata_path.is_file() else {}
            part = attempt.get('part') or metadata.get('part') or 'unclassified'
            parts[part] = parts.get(part, 0) + 1
            tags = attempt.get('skill_tags') or metadata.get('skill_tags') or [metadata.get('subtype', 'unclassified')]
            if not correct:
                wrong_ids.append(qid)
            for tag in set(tags):
                row = rows.setdefault(tag, {'answered': 0, 'correct': 0, 'incorrect': 0})
                row['answered'] += 1
                row['correct' if correct else 'incorrect'] += 1
    for row in rows.values():
        row['accuracy'] = row['correct'] / row['answered']
        row['small_sample'] = row['answered'] < 5
    return {'set_id': set_id, 'answered': answered,
            'target_per_weekend': config.get('questions_per_weekend', 50),
            'part_counts': parts,
            'skills': dict(sorted(rows.items(), key=lambda item: (item[1]['accuracy'], -item[1]['answered']))),
            'wrong_question_ids': wrong_ids, 'toeic_score_estimate': None,
            'note': 'Diagnostic practice only. Tags can overlap; do not sum them as question totals. Fewer than 5 items per skill is a small sample.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('plan')
    p.add_argument('--hours', type=float)
    p.add_argument('--date', type=date.fromisoformat,
                   default=datetime.now(timezone(timedelta(hours=9))).date())
    p = sub.add_parser('stats')
    p.add_argument('--subject', choices=TRACKS)
    sub.add_parser('concepts')
    p = sub.add_parser('toeic-report')
    p.add_argument('--set', dest='set_id', help='Registered weekend study set ID; omitted means all first attempts')
    p = sub.add_parser('today')
    p.add_argument('--date', type=date.fromisoformat,
                   default=datetime.now(timezone(timedelta(hours=9))).date())
    args = parser.parse_args()
    if args.command == 'plan':
        output = plan(read_json(ROOT / 'study_profile.json'),
                      read_json(ROOT / 'subjects/exam_schedule.json'), args.date, args.hours)
    elif args.command == 'stats':
        output = stats(args.subject)
    elif args.command == 'toeic-report':
        output = toeic_report(args.set_id)
    elif args.command == 'today':
        output = daily_progress(args.date)
    else:
        output = read_json(ROOT / 'subjects/concepts.json')
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
