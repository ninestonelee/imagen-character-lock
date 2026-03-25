# imagen-character-lock

AI 이미지 생성 시 **캐릭터 외형 일관성**을 자동으로 보장하는 Claude Code 스킬.

Google Imagen 4.0으로 스토리/영상용 이미지를 만들 때, 매 장면마다 인물이 다르게 생성되는 문제를 해결합니다.

## 문제

AI로 여러 장면의 이미지를 생성하면 **같은 인물이 매번 다른 얼굴, 나이, 체형**으로 나옵니다.
영상이나 스토리 제작에 치명적입니다.

| | 수동 프롬프트 (v1) | character_lock (v2) |
|---|---|---|
| 캐릭터 일관성 | **44%** (8/18) | **100%** (6/6) |
| 성별 오류 | 2건 | 0건 |
| 재생성 필요 | 50% | 0% |

## 작동 원리

캐릭터를 한 번 정의하고, 각 장면에서 이름으로 참조하면 파이프라인이 자동으로 외형 묘사를 주입합니다.

```
character_lock (한 번 정의)       scenes (이름으로 참조)
┌───────────────────────┐       ┌──────────────────────────┐
│ jina:                 │       │ 씬 1:                    │
│   morning: "35세,     │──────▶│   characters: [jina.morning]│
│     후드, 안경..."    │       │   prompt: "새벽 책상..."  │
│   office: "35세,      │       │                          │
│     블레이저..."      │──────▶│ 씬 3:                    │
│                       │       │   characters: [jina.office]│
└───────────────────────┘       │   prompt: "프레젠테이션"  │
                                └──────────────────────────┘
```

최종 프롬프트 = `style_prefix` + `캐릭터 묘사` + `장면 프롬프트`

---

## 빠른 시작

### 1. 설치

```bash
# Claude Code 스킬로 설치
claude mcp add-skill github:ninestonelee/imagen-character-lock

# 또는 직접 클론
git clone https://github.com/ninestonelee/imagen-character-lock.git
pip install google-genai
```

### 2. API 키 설정

```bash
# 방법 A: .env 파일 (프로젝트 루트)
echo "GOOGLE_API_KEY=AIzaSy..." > .env

# 방법 B: 환경변수
export GOOGLE_API_KEY=AIzaSy...
```

### 3. prompts.json 작성

프로젝트 폴더에 `storyboard/prompts.json`을 만듭니다.
전체 스키마는 [templates/prompts.json](templates/prompts.json) 참조.

```json
{
  "schema_version": "2.0",
  "style_prefix": "Cinematic Korean drama, 16:9 widescreen",
  "character_lock": {
    "jina": {
      "morning": "Korean woman age 35, shoulder-length black hair, almond eyes, grey hoodie, round glasses",
      "office": "Korean woman age 35, shoulder-length black hair neatly styled, almond eyes, charcoal blazer, pearl earrings"
    }
  },
  "scenes": [
    {
      "scene": 1,
      "title": "새벽 코딩",
      "images": [{
        "filename": "01_dawn_coding.jpg",
        "characters": ["jina.morning"],
        "prompt_en": "Sitting at cluttered desk at 4am, laptop illuminating face..."
      }]
    }
  ]
}
```

### 4. 생성

```bash
# 프롬프트 미리보기 (API 호출 안 함)
python3 scripts/generate_images.py my_project --dry-run

# 전체 생성
python3 scripts/generate_images.py my_project

# 미생성분만
python3 scripts/generate_images.py my_project --missing

# 특정 컷만
python3 scripts/generate_images.py my_project --only 01,04
```

---

## CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `<project>` | 프로젝트 폴더 경로 | (필수) |
| `--missing` | `images/`에 없는 파일만 생성 | off |
| `--only` | 쉼표 구분 파일 접두사 (예: `03,07`) | 전체 |
| `--dry-run` | 주입된 프롬프트만 출력, API 미호출 | off |
| `--backup` | 기존 이미지를 `images_backup/`으로 복사 | off |
| `--aspect-ratio` | 화면비 (16:9, 9:16, 1:1, 4:3, 3:4) | 16:9 |
| `--env` | .env 파일 경로 | 자동 탐색 |

---

## character_lock 작성 가이드

### 좋은 예: 구체적, 불변 속성 반복

```json
{
  "seoyeon": {
    "present": "Korean woman age 58, short salt-and-pepper bob ending at jawline, deep-set almond eyes with crow's feet, high cheekbones, slim build 163cm, faded navy work vest over grey shirt",
    "flashback": "Korean woman age 45, short black bob ending at jawline, deep-set almond eyes, high cheekbones, slim build 163cm, tailored navy suit with pinstripes"
  }
}
```

**불변 속성** (모든 타임라인에 반복): 민족, 나이대, 얼굴형, 눈 모양, 광대, 체형, 키, 피부톤

**가변 속성** (타임라인별 변경): 머리 색상/스타일, 의상, 액세서리, 표정, 메이크업

### 나쁜 예: 모호한 묘사

```json
{
  "seoyeon": {
    "present": "an older Korean woman in work clothes",
    "flashback": "a younger version of Seoyeon"
  }
}
```

이렇게 쓰면 매번 다른 사람이 나옵니다.

---

## 비용

| 모델 | 단가 | 비고 |
|------|------|------|
| Imagen 4.0 | ~$0.04/장 | 실패/필터 거부 = 무료 |

6컷 숏폼 = ~$0.24 / 18컷 시네마틱 = ~$0.72

---

## 알려진 제한사항

1. **텍스트 묘사만 가능** — Imagen 4.0은 레퍼런스 이미지를 지원하지 않음. 텍스트 묘사의 정밀도에 의존
2. **100% 동일 얼굴은 불가** — 같은 프롬프트라도 미세하게 다를 수 있음. 극도로 상세한 묘사로 편차 최소화
3. **안전 필터** — "black turtleneck", "authority" 등 일부 조합이 거부될 수 있음. 단어 조정으로 해결
4. **프롬프트 길이** — 캐릭터 묘사가 너무 길면 뒷부분이 무시될 수 있음. 핵심만 간결하게

---

## 프로젝트 구조

```
imagen-character-lock/
├── SKILL.md                    # Claude Code 스킬 정의
├── README.md                   # 이 문서
├── scripts/
│   └── generate_images.py      # 이미지 생성 스크립트
├── templates/
│   └── prompts.json            # 스키마 템플릿
└── examples/
    └── jina-day-in-life.json   # 실전 검증 예제 (6컷, 100% 일관성)
```

## 라이선스

MIT
