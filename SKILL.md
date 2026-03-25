---
name: imagen-character-lock
description: "Google Imagen 4.0으로 AI 이미지를 생성할 때 캐릭터의 외형 일관성을 자동으로 보장하는 파이프라인. character_lock에 정의된 타임라인별 인물 묘사를 프롬프트에 자동 주입하여, 동일 인물이 다양한 장면에서도 일관된 외형을 유지한다. 'Imagen', '이미지 생성', '캐릭터 일관성', 'character lock', 'AI 이미지', '인물 고정' 시 활성화."
---

# Imagen Character Lock — AI 이미지 캐릭터 일관성 파이프라인

## 해결하는 문제

AI 이미지 생성(Imagen, DALL-E, Midjourney 등)에서 **동일 인물이 매 장면마다 다른 얼굴/체형/의상**으로 생성되는 문제.

### Before (v1 — 수동 묘사)
- 18장 생성 → 10장 불일치 (44%)
- 성별 오류 2건, 나이 편차 40~70대
- 9장 재생성 필요 (50% 낭비)

### After (v2 — character_lock 자동 주입)
- 6장 생성 → **6장 일관 (100%)**
- 성별/나이 오류 0건
- 재생성 0장 (0% 낭비)

---

## 핵심 개념: character_lock

`storyboard/prompts.json`에 캐릭터별 **타임라인 묘사**를 정의하면, 생성 스크립트가 각 장면의 프롬프트에 자동으로 주입한다.

```
┌─────────────────────────────────────────────────────┐
│  prompts.json                                        │
│                                                       │
│  character_lock:                                      │
│    jina:                                              │
│      morning: "age 35, grey hoodie, glasses..."       │
│      office:  "age 35, black blazer, pearl earrings"  │
│      evening: "age 35, white linen shirt..."          │
│    cat:                                               │
│      default: "orange tabby, white chest patch..."    │
│                                                       │
│  scenes:                                              │
│    scene 1:                                           │
│      image: { characters: ["jina.morning", "cat"] }   │
│            ↓ 자동 주입                                │
│      prompt = style + jina.morning묘사 + cat묘사 +    │
│               장면 프롬프트                            │
└─────────────────────────────────────────────────────┘
```

---

## 전제 조건

### 1. Python 패키지

```bash
pip3 install google-genai
```

### 2. API 키

프로젝트 루트(또는 video_creator 루트)에 `.env` 파일:

```
GOOGLE_API_KEY=AIzaSy...your-key
```

또는 환경변수:
```bash
export GOOGLE_API_KEY=AIzaSy...
```

---

## 빠른 실행

### A. 이미지 생성 (character_lock 자동 주입)

```bash
# 전체 생성
python3 scripts/generate_images.py <프로젝트폴더>

# 미생성분만
python3 scripts/generate_images.py <프로젝트폴더> --missing

# 특정 컷만
python3 scripts/generate_images.py <프로젝트폴더> --only 03,07

# 프롬프트 확인 (API 호출 안 함)
python3 scripts/generate_images.py <프로젝트폴더> --dry-run

# 기존 이미지 백업 후 재생성
python3 scripts/generate_images.py <프로젝트폴더> --backup
```

**옵션:**

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `<프로젝트폴더>` | storyboard/prompts.json이 있는 폴더 경로 | (필수) |
| `--missing` | images/ 폴더에 없는 파일만 생성 | off |
| `--only` | 쉼표 구분 파일 접두사 (예: `03,07`) | 전체 |
| `--dry-run` | 주입된 프롬프트만 출력, API 미호출 | off |
| `--backup` | 기존 이미지를 images_backup/으로 복사 | off |
| `--aspect-ratio` | 화면비 (16:9, 9:16, 1:1, 4:3, 3:4) | 16:9 |
| `--env` | .env 파일 경로 | 자동 탐색 |

### B. 프로젝트 초기화 (선택)

```bash
bash scripts/init-video-project.sh <프로젝트폴더명>
```

prompts.json v2 스키마 템플릿이 자동 생성된다.

---

## prompts.json 스키마 v2.0

```json
{
  "schema_version": "2.0",
  "style_prefix": "스타일 프리픽스 (모든 이미지에 적용)",
  "character_lock": {
    "캐릭터이름": {
      "default": "기본 외형 묘사 (영문)",
      "타임라인1": "타임라인별 의상/표정 변형",
      "타임라인2": "..."
    },
    "조연이름": {
      "default": "조연 외형 묘사"
    }
  },
  "scenes": [
    {
      "scene": 1,
      "title": "씬 제목",
      "time": "0:00-0:05",
      "images": [
        {
          "id": "s01_01",
          "filename": "01_장면명.jpg",
          "characters": ["캐릭터이름.타임라인1", "조연이름"],
          "prompt_en": "장면/배경만 기술. 캐릭터 외형은 character_lock에서 자동 주입됨",
          "prompt_ko": "한글 참고용 설명",
          "video_prompt": "영상 생성용 움직임 프롬프트"
        }
      ]
    }
  ]
}
```

### 핵심 규칙

1. **`characters` 필드** — `"캐릭터명.타임라인"` 형식. 타임라인 생략 시 `default` 사용
2. **`prompt_en`** — 장면/배경/구도만 기술. 인물 외형 묘사 금지 (자동 주입됨)
3. **`character_lock`** — 모든 타임라인에서 불변 속성(나이, 얼굴 특징)은 동일하게 반복
4. **`style_prefix`** — 모든 프롬프트 앞에 자동 삽입되는 공통 스타일

---

## character_lock 작성 가이드

### 좋은 예 (구체적, 불변 속성 반복)

```json
{
  "seoyeon": {
    "present": "Korean woman age 58, short salt-and-pepper bob cut ending at jawline, deep-set almond eyes with subtle crow's feet, high prominent cheekbones, slim but sturdy build 163cm, wearing a faded navy work vest over grey long-sleeve shirt, no jewelry except simple watch",
    "flashback": "Korean woman age 45, short black bob cut ending at jawline, deep-set almond eyes, high prominent cheekbones, slim but sturdy build 163cm, wearing a tailored navy suit with subtle pinstripes, minimal pearl brooch"
  }
}
```

**불변 속성** (모든 타임라인에 반복):
- 민족/나이대, 얼굴 형태(눈, 광대, 턱선)
- 체형, 키
- 피부톤

**가변 속성** (타임라인별 변경):
- 머리 색상/길이 (노화)
- 의상, 액세서리
- 표정, 자세, 분위기

### 나쁜 예 (모호, 불변 속성 누락)

```json
{
  "seoyeon": {
    "present": "an older Korean woman in work clothes",
    "flashback": "a younger version of Seoyeon in a suit"
  }
}
```

---

## 프롬프트 결합 로직

스크립트는 아래 순서로 최종 프롬프트를 조합한다:

```
[style_prefix] + [character_lock 묘사들] + [prompt_en]
```

예시:
```
style_prefix: "Cinematic Korean drama, 16:9"
characters: ["jina.morning", "cat"]
prompt_en: "Sitting at a cluttered desk at 4am..."

→ 최종 프롬프트:
"Cinematic Korean drama, 16:9. Korean woman age 35, shoulder-length
straight black hair, sharp almond eyes, grey hoodie and round glasses,
no makeup. Orange tabby cat with white chest patch, green eyes.
Sitting at a cluttered desk at 4am..."
```

---

## 비용 참고

| 모델 | 단가 | 비고 |
|------|------|------|
| Imagen 4.0 | ~$0.04/장 | 16:9 기준 |
| 실패/안전필터 거부 | $0.00 | 과금 안 됨 |

> 6컷 숏폼 = ~$0.24 / 18컷 시네마틱 = ~$0.72

---

## 알려진 제한사항

1. **Imagen 4.0은 reference image를 지원하지 않음** — 텍스트 묘사에만 의존
2. **동일 프롬프트라도 100% 동일 얼굴은 불가** — 최선은 극도로 상세한 물리 묘사
3. **안전 필터** — "black turtleneck", "authority" 등 일부 조합이 거부될 수 있음. 프롬프트 미세 조정으로 해결
4. **프롬프트 길이** — style + character + scene이 너무 길면 후반부가 무시될 수 있음. character_lock은 핵심 속성만 간결하게

---

## 실전 테스트 결과

### 테스트 프로젝트: "개발자 지나의 하루" (6컷)

| 타임라인 | 컷 | 머리 | 얼굴 | 의상 | 고양이 | 판정 |
|---------|-----|------|------|------|--------|------|
| morning | 3장 | 흑발 단발 | 일관 | 후드+안경 | 오렌지태비 | ✅ |
| office | 2장 | 단정 단발 | 일관 | 블레이저+진주 | — | ✅ |
| evening | 1장 | 흑발 단발 | 일관 | 린넨셔츠 | 오렌지태비 | ✅ |

**6/6 일관성 100% 달성** (비용 $0.24)
