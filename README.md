# 🩸 [2025 kakao X 9oorm 시즌톤] 4팀 단짝이

<img width="876" height="488" alt="Image" src="https://github.com/user-attachments/assets/f2eb2c2c-f591-4187-8d76-ee94ee7b0b51" />


# 기술 구현

### 기술 스택 적합성

- **Flask (Python 3.11)** - AI 서비스 (LLM 기반 퀘스트 생성, RAG 기반 전문적 혈당 분석 후 피드백 제공)  
- **Spring Boot (Java 17)** - 기본적인 CRUD (도메인 중심 설계, 에러 헨들링·보안·로깅 준수)
- **MySQL** - 메인 데이터베이스  
- **ChromaDB** - 벡터 데이터베이스 (RAG용)  
- **Docker Compose** - 컨테이너화 
- **AWS Ec2** - 서버 배포 


### Python과 Java를 같이 사용하도록 구성한 이유: 각 기술의 강점과 목적에 맞춰 역할을 분리

**Flask (Python 3.11)**  
- AI 모델, LLM 기반 퀘스트 생성, RAG 기반 혈당 분석 등 Python 패키지 이용으로 머신러닝/데이터 처리 중심  
- Python 생태계의 AI 라이브러리 지원이 풍부해서 빠르고 효율적으로 AI 서비스를 구현 가능  

**Spring Boot (Java 17)**  
- 기본적인 CRUD, 도메인 중심 설계, 보안, 로깅 등 안정적인 웹 서비스 처리  
- Java의 타입 안정성과 풍부한 엔터프라이즈 기능 덕분에 백엔드의 비즈니스 로직을 신뢰성 있게 관리 가능
---

### 아키텍처 설계

#### AI-Service (Python) : **계층화된 아키텍처**

```plaintext
AI-Service/
├── main.py                          # 애플리케이션 진입점
├── app/
│   ├── __init__.py                  # Flask 앱 팩토리
│   ├── core/                        # 핵심 설정 및 AI 모듈
│   │   ├── config.py                # 환경 설정
│   │   ├── logging.py               # 로깅 설정 
│   │   └── ai.py                    # OpenAI API 클라이언트
│   ├── api/v1/                      # API 레이어
│   │   ├── router.py                # 라우터 등록
│   │   └── endpoints/               # 엔드포인트 구현
│   │       ├── health.py            # 헬스체크
│   │       ├── quests.py            # 퀘스트 관리
│   │       ├── parents.py           # 부모 관련 기능
│   │       └── children.py          # 아이 관련 기능
│   ├── database/                    # 데이터베이스 레이어
│   │   ├── database.py              # DB 연결 관리
│   │   ├── init.py                  # DB 초기화
│   │   └── database_utils.py        # DB 유틸리티
│   ├── models/                      # 데이터 모델
│   │   └── database_models.py       # SQLAlchemy 모델
│   ├── services/                    # 비즈니스 서비스
│   │   ├── chroma_rag_service.py    # RAG 서비스
│   │   └── glucose_service.py       # 혈당 서비스
│   ├── utils/                       # 유틸리티 모듈
│   │   ├── auth/                    # 인증/보안
│   │   ├── error/                   # 에러 처리
│   │   ├── monitoring/              # 모니터링
│   │   ├── business/                # 비즈니스 로직
│   │   └── common/                  # 공통 유틸리티
│   ├── prompts/                     # AI 프롬프트 템플릿
│   ├── embedding_data/              # RAG 임베딩 데이터
│   └── cache/                       # 캐시 디렉토리
└── requirements.txt                 # 의존성 관리
```

#### Spring-Service/danjjang (Java): **계층화된 아키텍처**
```plaintext
Spring-Service/danjjang/                                     
└── src/
    ├── main/
    │   ├── java/com/cloud/danjjang/
    │   │   ├── DanjjangApplication.java         
    │   │
    │   │   ├── common/                           # 공통 모듈
    │   │   │   ├── apiPayload/                   # API 응답 표준화
    │   │   │   │   ├── ApiResponse.java          # API 공통 응답 객체
    │   │   │   │   └── code/
    │   │   │   │       ├── BaseCode.java         # 기본 코드 인터페이스
    │   │   │   │       ├── BaseErrorCode.java    # 기본 에러 코드
    │   │   │   │       ├── ErrorReasonDTO.java   # 에러 사유 DTO
    │   │   │   │       ├── ReasonDTO.java        # 공통 사유 DTO
    │   │   │   │       └── status/
    │   │   │   │           ├── ErrorCode.java    # 에러 코드 정의
    │   │   │   │           └── SuccessCode.java  # 성공 코드 정의
    │   │   │   │
    │   │   │   ├── config/                       # 설정 클래스
    │   │   │   │   ├── SecurityConfig.java       # 시큐리티 설정
    │   │   │   │   ├── SwaggerConfig.java        # Swagger 설정
    │   │   │   │   └── WebConfig.java            # 웹 관련 설정
    │   │   │   │
    │   │   │   ├── entity/                       # 공통 엔티티
    │   │   │   │   └── BaseTimeEntity.java       # 생성/수정 시간 자동 관리 엔티티
    │   │   │   │
    │   │   │   ├── exception/                    # 예외 처리
    │   │   │   │   ├── ExceptionAdvice.java      # 예외 공통 처리
    │   │   │   │   ├── GeneralException.java     # 일반 예외 클래스
    │   │   │   │   └── handler/
    │   │   │   │       └── GeneralHandler.java   # 예외 핸들러
    │   │   │   │
    │   │   │   └── jwt/                          # JWT 인증 관련
    │   │   │       ├── LoginService.java         # 로그인 서비스
    │   │   │       ├── SecurityUtils.java       # 시큐리티 유틸
    │   │   │       ├── TokenDTO.java            # 토큰 DTO
    │   │   │       ├── TokenProvider.java       # JWT 토큰 생성/검증
    │   │   │       └── filter/
    │   │   │           ├── JwtAuthenticationFilter.java  # JWT 인증 필터
    │   │   │           ├── LoginFilter.java              # 로그인 필터
    │   │   │           └── LogoutFilter.java             # 로그아웃 필터
    │   │   │
    │   │   └── domain/                           # 도메인별 모듈
    │   │       ├── enums/                        # 열거형
    │   │       │   ├── DiabetesType.java
    │   │       │   ├── ExerciseType.java
    │   │       │   ├── Gender.java
    │   │       │   ├── Sensor.java
    │   │       │   └── Status.java
    │   │       │
    │   │       ├── exercise/                     # 운동 도메인
    │   │       │   ├── controller/
    │   │       │   │   └── ExerciseController.java  # 운동 API 컨트롤러
    │   │       │   ├── dto/
    │   │       │   │   ├── ExerciseRequestDTO.java  # 운동 요청 DTO
    │   │       │   │   └── ExerciseResponseDTO.java # 운동 응답 DTO
    │   │       │   ├── entity/
    │   │       │   │   └── Exercise.java           # 운동 엔티티
    │   │       │   ├── repository/
    │   │       │   │   └── ExerciseRepository.java # 운동 리포지토리
    │   │       │   └── service/
    │   │       │       └── ExerciseService.java    # 운동 서비스
    │   │       │
    │   │       ├── member/                       # 사용자 도메인
    │   │       │   ├── annotation/
    │   │       │   │   ├── AuthUser.java                   # 사용자 인증 어노테이션
    │   │       │   │   └── AuthUserArgumentResolver.java   # 인증 사용자 파라미터 처리
    │   │       │   ├── controller/
    │   │       │   │   └── MemberController.java          # 회원 API 컨트롤러
    │   │       │   ├── dto/
    │   │       │   │   ├── CustomUserDetails.java         # 사용자 상세 정보 DTO
    │   │       │   │   ├── MemberRequestDTO.java          # 회원 요청 DTO
    │   │       │   │   ├── MemberResponseDTO.java         # 회원 응답 DTO
    │   │       │   │   ├── MemberSignDTO.java             # 회원 가입 DTO
    │   │       │   │   └── RefreshTokenDTO.java           # 리프레시 토큰 DTO
    │   │       │   ├── entity/
    │   │       │   │   ├── Member.java                    # 회원 엔티티
    │   │       │   │   └── Refresh.java                   # 리프레시 토큰 엔티티
    │   │       │   ├── repository/
    │   │       │   │   ├── MemberRepository.java
    │   │       │   │   └── RefreshRepository.java
    │   │       │   └── service/
    │   │       │       ├── CodeGenerator.java
    │   │       │       ├── CustomUserDetailService.java
    │   │       │       ├── MemberMapper.java
    │   │       │       └── MemberService.java
    │   │       │
    │   │       ├── parent/                       # 부모 도메인
    │   │       │   └── entity/
    │   │       │       └── Parent.java
    │   │       │
    │   │       └── parentChild/                  # 부모-자녀 관계
    │   │           ├── entity/
    │   │           │   └── ParentChild.java
    │   │           └── repository/
    │   │               └── ParentChildRepository.java



      

```
---

### 확장성 고려

#### AI-Service (Python)
1. **새로운 API 엔드포인트 추가:** `app/api/v1/endpoints/`  
2. **새로운 서비스 추가:** `app/services/`  
3. **새로운 데이터 모델:** `app/models/database_models.py`  
4. **이에 대한 유틸리티:** `app/utils/`  

➡️ 새로운 API 구현은 위 순서로 유연하게 확장 가능  

#### Spring-Service/danjjang (Java)
1. 도메인 중심 설계 (DDD) 적용: `domain/` 패키지로 비즈니스 로직 분리
2. 인터페이스 기반 설계: `domain/member/repository/MemberRepository.java` - CrudRepository 확장
3. 커스텀 어노테이션으로 확장성 확보: `domain/member/annotation/AuthUser.java` - 인증 사용자 주입

---
### 효율성 고려 

#### AI-Service(Python): 
1. **캐싱 전략:** `app/utils/auth/jwt_auth.py` – 토큰 캐싱  
2. **성능 모니터링:** `app/utils/monitoring/performance_monitor.py` – 성능 추적  
3. **데이터베이스 성능 최적화:** `app/models/database_models.py` – 인덱스 설정  
4. **RAG 최적화:** `app/services/chroma_rag_service.py` – 벡터 검색 최적화

#### Spring-Service/danjjang (Java)
1. 공통 엔티티로 중복 제거: `common/entity/BaseTimeEntity.java`
2. 매핑 로직 분리로 서비스 계층 간소화: `domain/member/service/MemberMapper.java`
3. 커스텀 어노테이션으로 인증 간소화: `domain/member/annotation/AuthUserArgumentResolver.java`


---
### 코드 품질

#### AI-Service(Python): 
1. **가독성:** `app/utils/business/glucose_utils.py` - 명확한 함수명과 변수명  
2. **모듈화:** 계층별 모듈 분리  
3. **재사용성:** `app/utils/error/error_handler.py` - 공통 유틸리티 함수,
4. **데코레이터 패턴 활용:** `app/utils/auth/jwt_auth.py`

#### Spring-Service/danjjang (Java)
1. **가독성:** `domain/member/service/MemberService.java` - 비즈니스 로직의 명확한 표현
2. **모듈화:** 계층별 모듈 분리  
3. **재사용성:** `common/apiPayload/ApiResponse.java` - 공통 유틸리티 함수,
4. **데코레이터 패턴 활용:** `common/jwt/filter/JwtAuthenticationFilter.java` 

---

### 유지보수성

#### AI-Service(Python)
1. **의존성 주입:** `app/__init__.py` - 팩토리 패턴  
2. **인터페이스 분리:** `app/utils/auth/authorization.py` - 권한 시스템 (ISP 준수)

#### Spring-Service/danjjang (Java)
1. **의존성 주입:**: `domain/member/service/MemberService.java`
2. **인터페이스 분리:**: `domain/member/repository/MemberRepository.java` (ISP 준수)


---

### 에러 핸들링

#### AI-Service(Python)
1. **계층화된 에러 클래스:** `app/utils/error/error_handler.py`  
2. **API 레벨 예외 처리:** `app/api/v1/endpoints/parents.py`  
3. **전역 예외 핸들러 등록:** `app/__init__.py`

#### Spring-Service/danjjang (Java)
1. 중앙화된 예외 처리: `common/exception/ExceptionAdvice.java` - 전역 예외 처리 핵심
2. 에러 코드 표준화: `common/apiPayload/code/status/ErrorCode.java` - 에러 코드 정의
3. 입력 검증 예외 처리: `domain/member/dto/MemberRequestDTO.java` - 입력 검증(Bean Validation 활용)

---

### 사용자 경험

#### AI-Service(Python)
1. **구조화된 사용자 메시지:** `app/utils/error/user_messages.py`  
2. **상황별 맞춤 메시지:** `app/utils/error/error_handler.py`  

#### Spring-Service/danjjang (Java)
1. 명확하고 이해하기 쉬운 에러 메시지: `common/apiPayload/code/status/ErrorCode.java`
2. 예외 상황별 맞춤형 메시지: `domain/member/service/MemberService.java` - 도메인별 예외 메시지

---

### 보안 고려사항

#### AI-Service(Python)
1. **포괄적인 입력 검증:** `app/utils/auth/input_validator.py`  
2. **강력한 JWT 인증:** `app/utils/auth/jwt_auth.py`  
3. **역할 기반 접근 제어:** `app/utils/auth/authorization.py`  
4. **보안 이벤트 추적:** `app/utils/auth/security_logger.py`

#### Spring-Service/danjjang (Java)
1. JWT 기반 강력한 인증 시스템: `common/jwt/TokenProvider.java` - 보안 강화된 JWT 구현
2. 권한 기반 접근 제어: `common/jwt/TokenProvider.java` - 세분화된 권한 관리
3. 데이터베이스 보안: `domain/member/entity/Member.java` - 엔티티 레벨 보안

---

### 모니터링

#### AI-Service(Python)
1. **체계적인 로깅 설정:** `app/core/logging.py`  
2. **성능 추적:** `app/utils/monitoring/performance_monitor.py`  
3. **에러 통계 수집:** `app/utils/monitoring/monitoring.py`  
4. **시스템 상태 모니터링:** `app/api/v1/endpoints/health.py`

#### Spring-Service/danjjang (Java)
1. 보안 이벤트 로깅: `common/jwt/TokenProvider.java` - 보안 로깅
2. SLF4J 기반 로깅: `common/exception/ExceptionAdvice.java` - 전역 예외 로깅
3. Swagger를 통한 API 모니터링: `common/config/SwaggerConfig.java` - API 문서화 및 모니터링

---

# 핵심 로직

<img width="875" height="491" alt="스크린샷 2025-09-18 오전 9 26 26" src="https://github.com/user-attachments/assets/ef76c592-f469-428e-ae2f-694d2f333bd4" />
<img width="874" height="489" alt="스크린샷 2025-09-18 오후 11 12 54" src="https://github.com/user-attachments/assets/8d4ac7ac-d3b7-4017-a5d9-3cefb538e705" />


LLM을 활용한 수치·기록 기반 맞춤형 퀘스트 제공: 함수를 통해 계산된 혈당 지표들을 통계적으로 분석하여 개인별 맞춤 퀘스트 생성(통계적 혈당 분석 + LLM 창의성 + 게이미피케이션을 결합한 개인화된 혈당 관리 퀘스트 생성)

케릭터와 함께 성장하는 리포트: LLM에 RAG 기법 도입으로 ChromaDB를 활용한 벡터 검색과 지식 기반 컨텍스트 강화를 통해 개인화된 혈당 분석을 제공
1. 자동 쿼리 생성: 혈당 관련 데이터를 검색어로 자동 변환해 사용
2. 임베딩된 지식 검색: ChromaDB에서 관련 문서 검색
3. 프롬프트 강화: API에 맞는 프롬포트 + 의료 지식 컨텍스트
4. 개인화 응답: 아이/부모별 맞춤 톤앤매너(프롬포트로 LLM 톤앤매너 조절 용이)
5. 응답 제공: RAG 적용으로 사용자 맞춤형 응답 제공



---

### 👨‍💻 백엔드 개발자

-  AI-Service 🟢  
  🔗 [정준영](https://github.com/Jung0522)
- Spring-Service 🔵  
  🔗 [김채원](https://github.com/KimChaeWon12)

