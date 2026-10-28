# CS-DB-AVG-001-Q001

- 영역: 전산 전공·데이터베이스
- 세부 유형: GROUP BY와 그룹별 평균
- 난이도: 기초 응용
- 출처 유형: 독창 연습문제
- 검수 상태: 검수 완료

SERVICE_LOG 테이블에 다음 처리시간(분)이 저장되어 있다.

| category | minutes |
|---|---:|
| A | 10 |
| A | 20 |
| B | 30 |

아래 SQL의 결과로 옳은 것은?

```sql
SELECT category, AVG(minutes)
FROM SERVICE_LOG
GROUP BY category;
```

1. A의 평균 15분, B의 평균 30분
2. A의 평균 10분, B의 평균 20분
3. A와 B의 평균이 모두 20분
4. 전체 평균 20분만 한 행으로 반환

- 권장 풀이시간: 90초
