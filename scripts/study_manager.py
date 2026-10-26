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
    return {'weekly_minutes': total, 'minutes': minutes, 'toeic_target_secured': secured,
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
    args = parser.parse_args()
    if args.command == 'plan':
        output = plan(read_json(ROOT / 'study_profile.json'),
                      read_json(ROOT / 'subjects/exam_schedule.json'), args.date, args.hours)
    elif args.command == 'stats':
        output = stats(args.subject)
    else:
        output = read_json(ROOT / 'subjects/concepts.json')
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
