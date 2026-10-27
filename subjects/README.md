# 통합 학습 인덱스

기존 lessons/, questions/, sessions/는 그대로 사용한다. 과목 폴더는 인덱스이며 파일을 옮기거나 중복 복제하지 않는다. 기존 NCS 시도에는 exam_track 필드가 없으므로 NCS- 문제 ID를 ncs로 읽는다. 원본 기록은 수정하지 않는다.

| 조회 구분 | exam_track | 인덱스 |
| --- | --- | --- |
| NCS | ncs | ncs/README.md |
| 전산 전공 | computer-science | computer-science/README.md |
| 정보보안기사 필기 | security-written | security-engineer/README.md |
| 정보보안기사 실기 | security-practical | security-engineer/README.md |
| TOEIC | toeic | toeic/README.md |

```powershell
python scripts/study_manager.py stats
python scripts/study_manager.py stats --subject ncs
python scripts/study_manager.py plan
python scripts/study_manager.py plan --hours 10
python scripts/study_manager.py concepts
```

plan은 미리보기다. 사용자가 시간 변경을 요청하면 Codex가 study_profile.json의 weekly_hours와 시간 배분, curriculum.md와 progress.md를 갱신하고 다시 실행한다. 일정이 확정되면 exam_schedule.json에 공식 근거와 함께 기록한다. 학습 시작 시 실행하며 백그라운드 조정은 없다.

## 기록 확장 규약

신규 문제/시도에는 subject, exam_track, concept_ids, scoring_format(choice/rubric), question_version을 추가한다. 기존 필드와 ID는 유지한다. 과목별 성적은 exam_track 기준이고 개념 학습은 concepts.json의 concept_id로 공유한다. 공통 강의의 시간은 실제 한 번만 세며 복수 과목에 중복 합산하지 않는다. 전산+보안 6시간은 합계다.

공통 개념: not_started → learning → learned → mastered. 강의를 들은 것과 시험 문제 숙달을 구분한다. lesson_file, evidence_attempt_ids, last_studied_on은 실제 학습 때만 채운다. 이미 learned인 개념은 짧은 확인 후 시험별 문제로 넘어가고, 확인 실패 시 해당 부분만 보강한다. 필기와 실기 숙달은 별도 근거를 요구한다.

서술형 시도에는 score, max_score, rubric_scores, grading_uncertain, grading_notes를 추가한다. 키워드 3점·기술 정확성 4점·필수 내용 2점·명확성 1점(합계 10점)을 기본 연습 기준으로 쓰되 문제마다 배점과 허용 답안을 강사용 파일에 미리 정한다. AI 참고 평가이며 공식 배점으로 표시하지 않는다. 불확실한 경우 확정 정오/숙달로 처리하지 않는다. 객관식 정답률과 서술형 득점률을 합치지 않는다.

wrong_answers.md는 기존 표를 유지하며 아래 과목별 구역에 신규 항목을 기록한다. review_schedule.md의 단일 표에 모든 과목을 모으고 복습 ID에 과목을 포함한다. 동일 문제 활성 일정 하나, 1→3→7→14일 규칙은 동일하다. 실기는 힌트 없이 필수 요소 충족과 기술적 오류 없음이 확인될 때 성공이며 채점 불확실이면 확인 대기로 두고 다음 날 재검토한다.

오류 정정: 문제 버전을 올리고 원본/기존 시도를 보존한다. 영향받는 attempt_id를 보고서에 열거하고 정정 평가를 별도 correction 필드로 연결한다. 통계 도구에도 정정 반영 방식을 구현·검증한 뒤 수정 통계를 낸다. 그 전에는 영향받은 통계를 잠정치로 표시한다.


TOEIC 최신 예외:평일 데일리 제외, 주말 합계 RC50문항 진단. 복습 명목기한을 보존하면서 실제 수행일은 주말로 배치한다. 자세한 운영은 toeic/README.md, 명령은 ../COMMANDS.md.
