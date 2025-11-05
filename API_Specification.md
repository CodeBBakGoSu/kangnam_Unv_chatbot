## API 요약표

### 인증 (Auth) API

| 기능                   | 메서드 | 경로              | 인증 필요 | 비고 |
|----------------------|--------|-------------------|-----------|------|
| 로그인 및 토큰 발급       | POST   | /auth/login       | ❌        | run_etl 쿼리 지원 |
| 사용자 데이터 강제 갱신    | POST   | /auth/refresh     | ❌        | run_full_etl 쿼리 지원 |
| 사용자 데이터 완전 삭제    | POST   | /auth/clear-data  | ❌        | -    |
| 사용자 데이터 상태 확인    | GET    | /auth/data-status | ✅        | 청크 수 등 반환 |
| 현재 사용자 정보 확인     | GET    | /auth/me          | ✅        | JWT 페이로드 정보 |

### 챗봇 (Chat) API

| 기능               | 메서드 | 경로         | 인증 필요 | 비고 |
|------------------|--------|--------------|-----------|------|
| 챗봇 메시지 처리     | POST   | /chat/        | ✅        | RAG 정보 포함 가능 |
| 테스트 메시지 처리   | POST   | /chat/test    | ❌        | 개발/테스트 전용 |

## Base URL

`/api` (예: `http://localhost:8000/api`)

## 인증

대부분의 API 엔드포인트는 JWT(JSON Web Token) 기반의 Bearer 토큰 인증을 사용합니다.
인증이 필요한 요청의 경우, `Authorization` 헤더에 `Bearer <your_token>` 형태로 토큰을 포함해야 합니다.

## 1. 인증 (Auth) API

엔드포인트 경로: `/auth`

### 1.1. 로그인 및 토큰 발급

*   **Endpoint:** `POST /login`
*   **Description:** 사용자 로그인 후 JWT 토큰을 발급합니다. ETL 파이프라인 실행 여부를 선택할 수 있습니다.
*   **Request Body:**
    ```json
    {
        "username": "string (학번)",
        "password": "string (비밀번호)"
    }
    ```
*   **Query Parameters:**
    *   `run_etl`: `boolean` (선택 사항, 기본값: `false`)
        *   `true`: 로그인 시 전체 ETL 파이프라인 (크롤링, 전처리, 청크 생성, 벡터DB 저장)을 실행합니다.
        *   `false`: ETL 파이프라인을 실행하지 않거나, 캐시된 데이터를 사용합니다.
*   **Success Response (200 OK):**
    ```json
    {
        "access_token": "string (JWT 액세스 토큰)",
        "token_type": "bearer"
    }
    ```
*   **Error Responses:**
    *   `401 Unauthorized`: 잘못된 학번 또는 비밀번호
        ```json
        {
            "detail": "잘못된 학번 또는 비밀번호입니다"
        }
        ```

### 1.2. 사용자 데이터 강제 갱신

*   **Endpoint:** `POST /refresh`
*   **Description:** 사용자의 강의 데이터 및 관련 정보를 강제로 새로고침합니다.
*   **Request Body:**
    ```json
    {
        "username": "string (학번)",
        "password": "string (비밀번호)"
    }
    ```
*   **Query Parameters:**
    *   `run_full_etl`: `boolean` (선택 사항, 기본값: `true`)
        *   `true`: 크롤링부터 벡터DB 저장까지 전체 ETL 파이프라인을 실행합니다.
        *   `false`: 크롤링을 통해 사용자 정보만 갱신합니다.
*   **Success Response (200 OK):**
    ```json
    {
        "message": "데이터가 성공적으로 갱신되었습니다",
        "details": "string (상세 메시지, 예: 'Crawling completed for user XXX. Processed YYY courses. Generated ZZZ chunks and stored in vector DB.')",
        "etl_stages": {
            "login": "completed",
            "crawling": "completed",
            "processing": "completed",
            "vectorizing": "completed",
            "storing": "completed"
        },
        "chunks_count": "integer (생성된 청크 수, 선택적)"
    }
    ```
*   **Error Responses:**
    *   `401 Unauthorized`: 잘못된 학번 또는 비밀번호
    *   `500 Internal Server Error`: 데이터 갱신 중 오류 발생

### 1.3. 사용자 데이터 완전 삭제

*   **Endpoint:** `POST /clear-data`
*   **Description:** 사용자의 모든 관련 데이터(특히 벡터 DB에 저장된 청크)를 삭제합니다.
*   **Request Body:**
    ```json
    {
        "username": "string (학번)",
        "password": "string (비밀번호)"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
        "message": "사용자 데이터가 성공적으로 삭제되었습니다",
        "remaining_chunks": "integer (삭제 후 남은 청크 수, 일반적으로 0)"
    }
    ```
*   **Error Responses:**
    *   `401 Unauthorized`: 잘못된 학번 또는 비밀번호
    *   `500 Internal Server Error`: 데이터 삭제 중 오류 발생

### 1.4. 현재 사용자 데이터 상태 확인

*   **Endpoint:** `GET /data-status`
*   **Authentication:** Bearer Token 필요
*   **Description:** 현재 로그인된 사용자의 데이터 처리 상태(저장된 청크 수, 관련 파일 정보 등)를 반환합니다.
*   **Success Response (200 OK):**
    ```json
    {
        "username": "string (학번)",
        "name": "string (사용자 이름)",
        "status": "string (데이터 상태: 'ready', 'not_ready', 'partial')",
        "stored_chunks": "integer (벡터 DB에 저장된 청크 수)",
        "file_exists": "boolean (개인 데이터 파일 존재 여부)",
        "last_modified": "string (YYYY-MM-DD HH:MM:SS 형식의 파일 최종 수정 시간, 파일 존재 시)",
        "file_size_kb": "float (KB 단위의 파일 크기, 파일 존재 시)"
    }
    ```
*   **Error Responses:**
    *   `400 Bad Request`: 사용자 정보 누락
    *   `401 Unauthorized`: 유효하지 않은 토큰
    *   `500 Internal Server Error`: 상태 확인 중 오류 발생

### 1.5. 현재 로그인 사용자 정보 확인

*   **Endpoint:** `GET /me`
*   **Authentication:** Bearer Token 필요
*   **Description:** 현재 인증된 사용자의 정보를 반환합니다.
*   **Success Response (200 OK):**
    ```json
    {
        // 사용자 정보 객체 (JWT 페이로드에 포함된 내용)
        // 예:
        "username": "string",
        "name": "string",
        "department": "string",
        "courses": [
            {"title": "string", "professor": "string"},
            // ...
        ]
        // ... 기타 정보
    }
    ```
*   **Error Responses:**
    *   `401 Unauthorized`: 유효하지 않은 토큰

## 2. 챗봇 (Chat) API

엔드포인트 경로: `/chat`

### 2.1. 챗봇 메시지 처리

*   **Endpoint:** `POST /`
*   **Authentication:** Bearer Token 필요
*   **Description:** 사용자의 메시지를 받아 챗봇의 응답을 생성합니다.
*   **Request Body:**
    ```json
    {
        "message": "string (사용자 메시지)"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
        "message": "string (원본 사용자 메시지)",
        "response": "string (챗봇 응답 메시지)",
        "current_flow": "string (응답 생성에 사용된 에이전트/플로우)",
        "rag_chunks": [
            // RAG (Retrieval Augmented Generation)에 사용된 청크 정보 배열 (선택적)
            // 예: {"chunk_type": "string", "content": "string", ...}
        ]
    }
    ```
*   **Error Responses:**
    *   `401 Unauthorized`: 유효하지 않은 토큰
    *   `500 Internal Server Error`: 응답 생성 중 오류 발생

### 2.2. 테스트용 챗봇 메시지 처리

*   **Endpoint:** `POST /test`
*   **Authentication:** 없음
*   **Description:** 인증 없이 챗봇 메시지 처리를 테스트합니다. 개발 및 테스트 환경에서만 사용해야 합니다.
*   **Request Body:**
    ```json
    {
        "message": "string (사용자 메시지)"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
        "message": "string (원본 사용자 메시지)",
        "response": "string (챗봇 응답 메시지)",
        "current_flow": "string (응답 생성에 사용된 에이전트/플로우)",
        "rag_chunks": [ /* ... */ ],
        "debug": {
            "test_mode": true,
            "user": "test_user",
            "timestamp": "string (ISO 8601 형식 타임스탬프)"
        }
    }
    ```
*   **Error Responses:**
    *   `500 Internal Server Error`: 응답 생성 중 오류 발생