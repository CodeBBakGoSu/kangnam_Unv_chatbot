# 🔧 트러블슈팅 가이드

## 세션 생성 실패 (Session Creation Failed)

### 증상
```bash
🧪 새 버전 테스트 중...
❌ 세션 생성 실패!
   새 배포를 삭제합니다...
```

### 가능한 원인

#### 1. **Import 에러**
가장 흔한 원인은 서브 에이전트나 도구를 import할 때 발생하는 에러입니다.

**확인 방법**:
```bash
# 로컬에서 import 테스트
cd /Users/hong-gihyeon/Desktop/cap
python -c "from test_rag.agent import root_agent; print('✅ Import 성공!')"
```

**해결 방법**:
- `test_rag/__init__.py` 파일이 모든 서브 디렉토리에 있는지 확인
- 순환 import가 없는지 확인
- 모든 경로가 올바른지 확인

#### 2. **환경 변수 문제**
`PROJECT_ID`나 `VERTEX_AI_LOCATION`이 제대로 설정되지 않았을 수 있습니다.

**확인 방법**:
```bash
# config.py 확인
cat test_rag/config.py
```

**해결 방법**:
```python
# test_rag/config.py에서 하드코딩된 값 확인
PROJECT_ID = "kangnam-backend"  # 올바른 프로젝트 ID
VERTEX_AI_LOCATION = "us-east4"  # 올바른 리전
```

#### 3. **Vertex AI Search 엔드포인트 문제**
서브 에이전트의 Vertex AI Search 엔드포인트가 잘못되었을 수 있습니다.

**확인 방법**:
```bash
# 각 에이전트의 search_tools.py 확인
grep -r "VERTEX_SEARCH_ENDPOINT" test_rag/agents/
```

**해결 방법**:
- 각 엔드포인트 URL이 올바른지 확인
- 프로젝트 ID가 맞는지 확인
- 엔진 ID가 존재하는지 확인

#### 4. **의존성 패키지 누락**
필요한 패키지가 `deploy.py`의 requirements에 포함되지 않았을 수 있습니다.

**확인 방법**:
```bash
# deploy.py의 requirements 확인
grep -A 10 "requirements=" deploy.py
```

**현재 requirements**:
```python
requirements=[
    "google-cloud-aiplatform[adk,agent_engines]",
    "requests",
    "beautifulsoup4",
    "python-dotenv",
]
```

**해결 방법**:
- 필요한 패키지가 모두 포함되어 있는지 확인
- 버전 충돌이 없는지 확인

#### 5. **Agent 정의 오류**
Agent 정의 시 문법 오류나 잘못된 파라미터가 있을 수 있습니다.

**확인 방법**:
```bash
# 각 에이전트 파일 문법 체크
python -m py_compile test_rag/agents/*/agent.py
```

**해결 방법**:
- Agent의 `model`, `name`, `description`, `instruction` 파라미터 확인
- `tools` 리스트가 올바른지 확인
- `sub_agents` 리스트가 올바른지 확인

---

## 디버깅 방법

### 1. 로컬에서 테스트

```bash
cd /Users/hong-gihyeon/Desktop/cap

# 가상환경 활성화
source .venv/bin/activate

# Import 테스트
python -c "
from test_rag.agent import root_agent
print('✅ Root agent import 성공!')
print(f'Agent name: {root_agent.name}')
print(f'Sub-agents: {len(root_agent.sub_agents)}')
"

# 각 서브 에이전트 테스트
python -c "
from test_rag.agents.graduation import graduation_agent
from test_rag.agents.subject import subject_agent
from test_rag.agents.professor.agent import professor_agent
from test_rag.agents.basic_info.agent import basic_info_agent
print('✅ 모든 서브 에이전트 import 성공!')
"
```

### 2. 에러 로그 확인

이제 `update_deployment.sh`가 에러 로그를 표시합니다:

```bash
./update_deployment.sh
```

에러 발생 시:
```bash
❌ 세션 생성 실패!

📋 에러 로그:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Traceback (most recent call last):
  File "deploy.py", line 113, in create_session
    remote_session = remote_app.create_session(user_id=user_id)
  ...
ImportError: cannot import name 'basic_info_agent' from 'test_rag.agents'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. 단계별 배포

문제를 격리하기 위해 단계별로 테스트:

```bash
# 1단계: 배포만 (테스트 없이)
python deploy.py --create

# 2단계: 세션 생성 테스트
python deploy.py --create_session --resource_id="프로젝트ID"

# 3단계: 메시지 전송 테스트
python deploy.py --send \
  --resource_id="프로젝트ID" \
  --session_id="세션ID" \
  --message="안녕"
```

---

## 일반적인 해결 방법

### 방법 1: Import 경로 확인

모든 서브 에이전트가 올바르게 export되는지 확인:

```bash
# test_rag/agents/__init__.py 확인
cat test_rag/agents/__init__.py
```

**올바른 예시**:
```python
from .graduation import graduation_agent
from .subject import subject_agent
from .professor.agent import professor_agent
from .basic_info.agent import basic_info_agent
from .admission.agent import admission_agent

__all__ = [
    'graduation_agent',
    'subject_agent',
    'professor_agent',
    'basic_info_agent',
    'admission_agent',
]
```

### 방법 2: 의존성 확인

```bash
# 로컬에서 필요한 패키지가 모두 설치되어 있는지 확인
pip list | grep -E "(google-cloud-aiplatform|requests|beautifulsoup4|python-dotenv)"
```

### 방법 3: 이전 버전으로 롤백

```bash
# .env.backup에서 이전 Resource ID 확인
cat .env.backup

# .env 복원
cp .env.backup .env

# Backend 재배포
cd agent-backend
./deploy_backend.sh
```

### 방법 4: 깨끗한 재배포

```bash
# 1. 가상환경 재생성
rm -rf .venv
python -m venv .venv
source .venv/bin/activate

# 2. 의존성 재설치
pip install -r requirements.txt

# 3. Import 테스트
python -c "from test_rag.agent import root_agent; print('✅ 성공!')"

# 4. 재배포
./update_deployment.sh
```

---

## 특정 에러별 해결 방법

### ImportError: cannot import name 'X'

**원인**: 모듈 import 경로가 잘못됨

**해결**:
1. `__init__.py` 파일이 모든 디렉토리에 있는지 확인
2. Import 경로가 올바른지 확인
3. 순환 import가 없는지 확인

### ModuleNotFoundError: No module named 'X'

**원인**: 필요한 패키지가 설치되지 않음

**해결**:
1. `deploy.py`의 `requirements` 리스트에 패키지 추가
2. 재배포

### AttributeError: 'Agent' object has no attribute 'X'

**원인**: Agent 정의 시 잘못된 파라미터 사용

**해결**:
1. Agent 정의 확인
2. ADK 문서 참조하여 올바른 파라미터 사용

### ValueError: Invalid endpoint

**원인**: Vertex AI Search 엔드포인트가 잘못됨

**해결**:
1. 각 서브 에이전트의 `search_tools.py` 확인
2. 엔드포인트 URL 수정
3. 재배포

---

## 예방 방법

### 1. 배포 전 체크리스트

- [ ] 로컬에서 import 테스트 완료
- [ ] 모든 `__init__.py` 파일 존재 확인
- [ ] Vertex AI Search 엔드포인트 확인
- [ ] 의존성 패키지 확인
- [ ] 문법 에러 없음 확인

### 2. 테스트 스크립트 작성

```bash
#!/bin/bash
# test_imports.sh

echo "🧪 Import 테스트 시작..."

python -c "
try:
    from test_rag.agent import root_agent
    from test_rag.agents.graduation import graduation_agent
    from test_rag.agents.subject import subject_agent
    from test_rag.agents.professor.agent import professor_agent
    from test_rag.agents.basic_info.agent import basic_info_agent
    print('✅ 모든 import 성공!')
except Exception as e:
    print(f'❌ Import 실패: {e}')
    exit(1)
"
```

### 3. 단계적 배포

1. 로컬 테스트
2. 배포
3. 세션 생성 테스트
4. 메시지 전송 테스트
5. 환경변수 업데이트
6. Backend 재배포

---

## 도움이 필요한 경우

### 로그 수집

```bash
# 전체 배포 로그 저장
./update_deployment.sh 2>&1 | tee deployment.log

# 에러 부분만 추출
grep -A 10 "❌" deployment.log
```

### 환경 정보 수집

```bash
# Python 버전
python --version

# 설치된 패키지
pip list

# 프로젝트 구조
tree test_rag -L 2

# 환경 변수
cat .env
```

---

**마지막 업데이트**: 2025-11-10

