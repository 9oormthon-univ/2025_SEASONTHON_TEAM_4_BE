# RAG 임베딩 데이터 폴더

이 폴더는 RAG(Retrieval-Augmented Generation) 시스템에서 사용할 의료 지식 데이터를 저장합니다.

## 📁 폴더 구조

```
embedding_data/
├── diabetes_basics.json          # 당뇨 기본 지식
├── glucose_management.json       # 혈당 관리
├── nutrition_guidelines.json     # 영양 관리
├── exercise_guidelines.json      # 운동 관리
├── medication_management.json    # 약물 관리
├── lifestyle_management.json     # 생활 관리
├── pediatric_diabetes.json       # 소아 당뇨
├── emergency_management.json     # 응급 관리
└── README.md                     # 이 파일
```

## 📋 JSON 파일 형식

각 JSON 파일은 다음과 같은 구조를 가집니다:

```json
{
  "category": "카테고리명",
  "documents": [
    {
      "title": "문서 제목",
      "content": "문서 내용 (의료 지식)",
      "keywords": ["키워드1", "키워드2", "키워드3"]
    }
  ]
}
```

## 🔧 사용법

1. **새 데이터 추가**: 새로운 JSON 파일을 생성하거나 기존 파일을 수정
2. **서버 재시작**: 데이터 변경 후 서버를 재시작하면 자동으로 로드됨
3. **캐시 삭제**: `app/cache/rag/medical_knowledge.pkl` 파일을 삭제하여 강제 재로드

## 📊 현재 로드된 데이터

- **총 항목 수**: 31개
- **카테고리**: 8개
  - 당뇨 기본 지식: 3개
  - 혈당 관리: 4개
  - 영양 관리: 4개
  - 운동 관리: 4개
  - 약물 관리: 4개
  - 생활 관리: 4개
  - 소아 당뇨: 4개
  - 응급 관리: 4개

## 🎯 RAG 활용

이 데이터는 다음 API에서 활용됩니다:

- `/api/v1/child/report` - 아이용 혈당 보고서
- `/api/v1/parent/report` - 부모용 혈당 보고서
- `/api/v1/parent/analyze` - 부모용 혈당 분석
- `/api/v1/quest/` - 개인화된 퀘스트 생성

## 📝 데이터 추가 가이드

### 1. 새로운 카테고리 추가
```json
{
  "category": "새로운 카테고리",
  "documents": [
    {
      "title": "문서 제목",
      "content": "상세한 의료 지식 내용...",
      "keywords": ["관련", "키워드", "목록"]
    }
  ]
}
```

### 2. 기존 카테고리에 문서 추가
기존 JSON 파일의 `documents` 배열에 새로운 객체를 추가합니다.

### 3. 키워드 작성 팁
- 의료 용어와 일반 용어를 모두 포함
- 검색에 유용한 동의어 포함
- 영어 용어도 함께 포함 (예: "혈당", "glucose")

## ⚠️ 주의사항

1. **인코딩**: 모든 파일은 UTF-8 인코딩으로 저장
2. **JSON 형식**: 유효한 JSON 형식 준수
3. **의료 정확성**: 의료 지식의 정확성 확인
4. **키워드**: 검색 효율성을 위한 적절한 키워드 설정

## 🔄 업데이트 프로세스

1. JSON 파일 수정/추가
2. 서버 재시작 또는 캐시 삭제
3. API 테스트로 새로운 데이터 반영 확인
4. RAG 메타데이터에서 `knowledge_sources_used` 증가 확인

