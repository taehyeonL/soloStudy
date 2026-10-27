# 학습 명령과 터미널 명령

## Codex 채팅에 입력하는 학습 명령

아래는 AGENTS.md에 정의한 자연어 운영 명령이다. PowerShell 실행 파일이나 슬래시 명령으로 설치한 것은 아니다. 정확히 일치하지 않아도 같은 의도로 처리한다.

| 명령 | 동작 |
| --- | --- |
| 오늘 공부 시작 / 수업 재개 | 진도·복습·일정 확인 후 재개. 평일 기본 대상은 NCS·전산·보안 |
| 강의 시작 | 현재 학습 단위의 개념·시범 강의 |
| 문제 풀기 | 현재 과목의 검수된 문제 한 개 |
| 힌트 | 단계별 힌트 |
| 다시 설명 | 다른 예시로 재설명 |
| 오답 복습 | 도래·기한 경과 복습부터 진행. TOEIC은 주말 처리 |
| 오늘 공부 끝 | 과목별 기록·오답·복습·진도 저장, Git 상태 확인 |
| 진도 확인 / 전산 전공 진도 확인 | 전체 또는 과목별 진도 |
| 주간 분석 | 최근7일 보고서 저장 |
| 모의고사 시작 | 범위·문항 수·시간 안내 후 한 문제씩 |
| 취약점 분석 | 기록에 근거한 약점 분석 |
| 다음 주 계획 | 시간·진도·복습을 반영한 계획 |
| 주말 토익 시작 | 주말 합계 RC50문항 진단 세트 생성·검수 후 한 문제씩 진행 |
| 토익 이어서 | 진행 중인 주말 세트/보류 문항 재개. 평일에는 명시적 요청 때만 |
| 토익 약점 분석 | 세트별 유형·개념 정답률, 오답·불안정 답, 시간 미확인 구분 보고서 |
| GitHub에 push해 줘 | 변경 확인·검증·커밋·안전한 push |

`주당10시간으로 변경`, `TOEIC 성적 확보` 같은 설정 변경도 자연어로 요청할 수 있다. 시간·공식 점수는 실제 확인한 값만 반영한다.

## PowerShell에서 실제 실행하는 CLI

프로젝트 폴더 `C:\Users\lthBe\personal`에서 실행한다.

```powershell
python scripts/study_manager.py --help
python scripts/study_manager.py plan
python scripts/study_manager.py plan --hours 10
python scripts/study_manager.py plan --date 2026-10-31
python scripts/study_manager.py stats
python scripts/study_manager.py stats --subject ncs
python scripts/study_manager.py stats --subject computer-science
python scripts/study_manager.py stats --subject security-written
python scripts/study_manager.py stats --subject security-practical
python scripts/study_manager.py stats --subject toeic
python scripts/study_manager.py concepts
python scripts/study_manager.py toeic-report
python scripts/verify_questions.py
```

`toeic-report --set TOEIC-RC-YYYY-MM-DD-01`은 실제 등록된 세트 ID로 조회한다. 아직 세트가 없으면 전체 조회는0문항이며 가상의 성적을 만들지 않는다. 세트 생성·문제 출제·채점·Markdown 보고서 저장은 위 채팅 명령으로 수행한다.

`plan`은 저장 없는 미리보기다. `--hours`와 `--date`를 줘도 프로필이나 시험 일정이 바뀌지 않는다. 평일에는 `daily_available_groups`에 TOEIC이 없고, 주간 시간 예산에는 주말 TOEIC2시간이 남는다. `toeic-report`는 읽기 전용 JSON 요약이며 공식 TOEIC 점수 환산을 하지 않는다.

Git 조회/동기화는 `git status --short --branch`, 작업이 깨끗할 때 `git pull --ff-only`를 사용한다. 대화 내용 전체가 Git에 저장되는 것은 아니다.

오늘 할당량 조회: `python scripts/study_manager.py today` 또는 `today --date 2026-10-27`. 일일 목표 파일과 채점된 세션 기록으로 작업량 진행률을 조회하며 학습시간이나 정답률을 뜻하지 않는다. 채팅에서는 과목명과 함께 표시한다.
