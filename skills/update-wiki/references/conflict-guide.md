# 충돌 감지 및 처리 가이드

wiki를 업데이트할 때 기존 내용과 새 source가 충돌하는 경우 처리 방법.

---

## 충돌 유형

### 유형 A: 명확한 업데이트 (Superseded)
기존 내용이 틀렸거나 더 정확한 정보가 생긴 경우.

**처리 방법:** `Superseded Notes` 섹션에 변경 이력 기록.

```markdown
## Superseded Notes
- **Old:** Deep Agents는 LangGraph 위에서 동작한다.
- **New:** Deep Agents는 LangChain building blocks와 LangGraph runtime을 함께 사용한다.
- **Source:** `deepagents-docs-overview-2026-05-18`
- **Date:** 2026-05-18
```

---

### 유형 B: 불확실한 충돌 (Possible Conflict)
기존 내용과 새 source가 다르게 보이지만, 어느 쪽이 맞는지 아직 불분명한 경우.

**처리 방법:** `Possible Conflict` 섹션에 양쪽 모두 보존.

```markdown
## Possible Conflict
기존 문서에서는 [A]라고 정리했지만, 새 source [`source-id`]는 [B]처럼 보인다.
추가 확인 필요.

- 기존: [A]
- 새 source: [B] — Source: `source-id`
- 상태: Needs verification
```

---

### 유형 C: 보완 (Additive)
기존 내용이 틀리지 않지만, 새 source가 더 구체적인 정보를 추가하는 경우.

**처리 방법:** 기존 내용을 유지하면서 새 정보를 추가.

```markdown
## Updated Understanding
이전에는 [기존 이해]로 정리했지만,
새 source 기준으로 [더 구체적인 이해]로 보완할 수 있다.
Source: `source-id`
```

---

## 충돌 감지 체크리스트

업데이트 전 다음을 확인한다.

1. 기존 wiki 페이지에 같은 개념에 대한 설명이 있는가?
2. 새 source가 기존 설명을 부정하는가?
3. 새 source가 기존 설명보다 더 정확한가, 아니면 다른 관점인가?
4. 버전 차이로 인한 차이일 수 있는가?
5. 공식 문서 vs 블로그처럼 신뢰도 차이가 있는가?

---

## 절대 하지 말 것

- 기존 내용을 조용히 삭제하지 않는다.
- 기존 내용이 맞는지 확인 없이 덮어쓰지 않는다.
- 충돌을 발견했는데 표시 없이 그냥 넘어가지 않는다.
