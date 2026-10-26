# NCS STUDY

2027년 공공기관 일반직 정규직 전산직 준비를 위한 12주 학습 공간입니다. Codex Windows에서 이 폴더를 열고 자연어로 말하면 됩니다. 웹앱 설치나 실행은 필요 없습니다.

## 매일 사용법

1. 다른 PC에서는 학습 시작 전 Git 상태를 확인하고, 변경이 없으면 `git pull --ff-only`로 파일을 받습니다.
2. `오늘 공부 시작` — 진도와 기한 지난 항목을 포함한 복습부터 확인하고 수업을 시작합니다.
3. 문제에 `3번 / 이유: … / 약 50초`처럼 답합니다. 시간은 모르면 생략해도 됩니다.
4. `힌트`, `다시 설명`을 자유롭게 요청합니다. 한 문제씩 진행합니다.
5. `오늘 공부 끝` — 학습 기록·오답·복습·진도 저장과 Git 상태 확인을 요청합니다.
6. 원격 설정 후 `GitHub에 동기화해 줘`라고 요청하면 변경 검토 후 안전하게 동기화합니다.

| 명령 | 하는 일 |
| --- | --- |
| 오늘 공부 시작 | 현재 수업 재개 또는 새 세션 시작, 도래 복습 우선 |
| 강의 시작 | 현재 Day 개념과 풀이 시범 |
| 문제 풀기 | 검수한 문제 한 개 제시 |
| 힌트 | 답을 밝히지 않는 단계별 도움 |
| 다시 설명 | 다른 사례로 개념 설명 |
| 오답 복습 | 정답을 가린 재풀이 |
| 오늘 공부 끝 | 기록 확정 및 Git 상태 안내 |
| 진도 확인 | 완료한 학습과 현재 위치 |
| 주간 분석 | 최근 7일 보고서 저장 |
| 모의고사 시작 | 범위·분량 안내 후 한 문제씩 실전 연습 |
| 취약점 분석 | 실제 풀이 기록으로 약점 분석 |
| 다음 주 계획 | 진도·오답·시간을 반영한 계획 |

## 파일 안내

- AGENTS.md: 이후 Codex가 따라야 할 수업 운영 규칙
- curriculum.md: 12주·84학습일 계획과 기존/개편 영역 설명
- progress.md: 현재 위치와 다음 행동
- study_profile.json: 목표·경력·선호·운영 설정
- wrong_answers.md / review_schedule.md: 오답과 1→3→7→14일 복습
- lessons/: 강의, 공식 근거, 풀이 시범
- questions/: 학생용 문제, `_instructor/`의 정답·해설 JSON
- sessions/: 세션별 Markdown 요약과 JSON 시도 원장
- reports/: 주간 분석과 검수 보고서
- scripts/: 수리·논리 문제 검증 코드

풀이 전에는 `questions/_instructor/` 파일을 열지 마세요. 정답 파일은 로컬에 보관되며 암호화하지 않습니다. 채팅에서는 답변 전 정답을 공개하지 않습니다. 수업 예제의 풀이 공개는 별도입니다.

복습 알림이나 백그라운드 실행은 없습니다. Codex에서 시작할 때 일정을 읽습니다. 중요한 내용은 파일로 저장하므로 다른 PC에서도 이어갈 수 있습니다. 학습시간과 풀이시간은 실측 또는 본인 보고가 있을 때만 기록합니다.

## GitHub 연결

현재 로컬 Git 저장소로 초기화합니다. 계정이나 원격은 임의로 설정하지 않습니다. GitHub에서 빈 Private 저장소를 만든 뒤 다음을 실행합니다. `YOUR_ID`와 `YOUR_PRIVATE_REPO`를 실제 값으로 바꾸세요. 회사 PC에서는 보안정책을 먼저 따르세요.

```powershell
git status --short --branch
git add AGENTS.md README.md curriculum.md progress.md wrong_answers.md review_schedule.md study_profile.json lessons questions sessions reports scripts .gitignore .gitattributes
git commit -m "Initialize NCS study workspace"
git branch -M main
git remote add origin https://github.com/YOUR_ID/YOUR_PRIVATE_REPO.git
git push -u origin main
```

인증은 GitHub의 정상 로그인 절차를 이용합니다. Git 사용자 이름/이메일이 없다면 본인 값으로 설정해야 합니다. 이미 로컬 초기 커밋이 있다면 위 초기 커밋 단계는 생략합니다. 원격 연결과 push 상태는 실제 Git 상태로 확인합니다. 빈 저장소가 아닌 원격에 연결할 때는 기존 이력을 먼저 확인합니다.

다른 PC에서 처음 받을 때:

```powershell
git clone https://github.com/YOUR_ID/YOUR_PRIVATE_REPO.git
cd YOUR_PRIVATE_REPO
git status --short --branch
git pull --ff-only
```

이미 받았다면 해당 폴더에서 상태 확인 후 pull합니다. 로컬 변경·충돌이 있으면 기록을 삭제하지 말고 Codex에 병합을 요청하세요. 대화 기록 자체는 Git에 포함되지 않습니다.

## 문제 검증

```powershell
python scripts/verify_questions.py
```

성공/실패와 검수 범위만 출력하며 정답은 출력하지 않습니다. 자연어 지문 대조는 강사의 수동 검수도 필요합니다.
