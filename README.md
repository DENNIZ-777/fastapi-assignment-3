# FastAPI 세미나 과제 3 — EC2 자동 배포

## 과제 개요

이 저장소에는 **과제 2의 정답 코드**가 들어 있습니다. 이번 과제에서는 이미 구현된 FastAPI API를 기반으로 진행됩니다. `main` 브랜치에 코드가 push될 때 Docker 이미지 빌드부터 EC2 배포까지 자동으로 수행하는 CD 파이프라인을 구축합니다.

완성된 파이프라인은 다음 순서로 동작해야 합니다.

1. GitHub Actions가 `main` 브랜치의 새 커밋을 감지합니다.
2. 해당 커밋의 코드로 Docker 이미지를 빌드합니다.
3. 이미지를 **본인의 Docker Hub 저장소**에 push합니다.
4. EC2가 새 이미지를 pull하고 실행 중인 서비스를 교체합니다.
5. 외부에서 EC2의 `http://<서버 IP>/health`로 요청하여 정상 응답을 받을 수 있습니다.

위 과정은 `main`에 push한 뒤 별도의 수동 빌드, 이미지 push 또는 EC2 접속 없이 완료되어야 합니다.

## 제공 코드

- `src/`: 과제 2 FastAPI 정답 코드
- `pyproject.toml`, `uv.lock`: Python 의존성
- `deployment_info.py`: 제출할 EC2 주소와 Docker Hub 이미지 저장소를 적는 파일

## 구현 요구 사항

### 1. Docker 이미지

프로젝트 루트에 `Dockerfile`을 작성하세요. Docker 이미지는 저장소의 코드와 의존성을 포함하고 FastAPI 서버를 실행해야 합니다.

- Python 3.12를 사용하고, 제공된 `uv.lock`을 기준으로 의존성을 설치하세요.
- 이미지 안에서 `src.main:app`이 정상적으로 시작되어야 합니다. 컨테이너 내부에서는 `0.0.0.0:8000`으로 요청을 받고, EC2의 80번 포트를 컨테이너의 8000번 포트에 연결하세요.
- 제공된 `/health`의 해시 계산 동작을 유지하세요. `GET /health`가 HTTP 200과 `{"status":"ok", "hash":"..."}` 형식의 JSON을 반환해야 합니다.
- `.dockerignore`를 작성하여 `.git`, `.venv`, 로컬 비밀 파일 등 빌드에 필요하지 않은 파일을 이미지 빌드 컨텍스트에서 제외하세요.


### 2. GitHub Actions workflow

`.github/workflows/` 아래에 workflow 파일을 작성하세요. `main` 브랜치에 push가 발생하면 다음 작업이 자동으로 실행되어야 합니다.

1. push된 커밋의 소스 코드를 checkout합니다.
2. Docker 이미지를 빌드합니다.
3. 본인의 Docker Hub 저장소에 이미지를 push합니다.
4. EC2에서 새 이미지를 pull하고 서비스를 새 이미지로 교체합니다.
5. 배포 후 `GET /health`로 정상 동작을 확인합니다. 확인에 실패하면 workflow도 실패해야 합니다.

이미지에는 **전체 커밋 SHA**를 태그로 붙이세요. 예를 들어 `<계정>/<이미지>:<40자리 커밋 SHA>` 형식입니다. `latest` 태그를 추가로 사용하는 것은 허용하지만, 배포 대상 이미지를 특정할 수 있도록 해당 커밋 SHA 태그도 반드시 push하고 배포에 사용해야 합니다. 채점기가 이미지 존재 여부를 확인할 수 있도록 **Docker Hub 저장소는 공개 상태로 설정**하세요.

GitHub Actions에서는 `${{ github.sha }}`가 이번 push의 커밋 SHA입니다. 예를 들어 이미지 빌드 단계의 `tags`에 다음처럼 사용하세요.

```yaml
tags: ${{ secrets.DOCKERHUB_USERNAME }}/fastapi-assignment-3:${{ github.sha }}
```

EC2의 `docker pull`과 `docker run`에도 **같은 SHA 태그**를 사용하면 됩니다. SHA를 직접 복사해 적을 필요는 없습니다.

이미지 이름은 본인의 Docker Hub 저장소에 맞게 변경하고, 빌드·배포 단계에서 사용한 `<계정>/<저장소>`를 `deployment_info.py`의 `image_repository`에도 똑같이 기록하세요.

Docker Hub 인증 정보와 EC2 접속 정보는 GitHub Actions의 Secrets로 전달하세요. **토큰, 비밀번호, SSH 개인 키를 Git에 commit하거나 로그에 출력하면 안 됩니다.**

### 3. EC2 서비스

- 본인의 EC2에서 Docker로 이미지를 실행하세요.
- 외부에서 EC2의 **80번 포트**로 FastAPI 서버에 접근할 수 있어야 합니다.
- 배포 workflow가 종료된 뒤에도 서비스가 계속 실행되어야 합니다.
- 다음 push가 발생하면 새 커밋의 이미지로 자동 교체되어야 합니다.
- `GET /health`뿐 아니라 과제 2의 회원가입 및 인증 API도 사용 가능해야 합니다.

### 자동 배포 직접 확인하기

최초 배포가 성공한 뒤 `http://<서버 IP>/`에서 `{"message":"Hello, World!"}`를 확인하세요. 그다음 `src/main.py`의 `get_root()`가 반환하는 메시지를 다른 문구로 바꿔 `main`에 한 번 더 push하세요. EC2에 직접 접속하지 않은 상태에서 workflow가 완료된 뒤 `/`의 응답도 새 문구로 바뀌어야 합니다. 기존 API와 `/health`의 동작은 유지하세요.

**최초 배포와 메시지 변경 배포, 두 push 커밋의 GitHub Actions 성공 실행 기록을 채점 완료까지 남겨두세요.** 두 커밋에 해당하는 Docker Hub SHA 태그도 삭제하지 마세요.

### 4. 제출 정보

프로젝트 루트의 `deployment_info.py`에 실제 배포 정보를 기록하세요.

```python
server_ip = "203.0.113.10"  # 실제 EC2의 공인 IP로 변경
image_repository = "your-dockerhub-id/fastapi-assignment-3"
```

두 값은 위 예시처럼 Python 문자열 리터럴로 작성하세요. `server_ip`에는 프로토콜이나 포트 없이 공인 IP 주소만 적습니다. `image_repository`에는 Docker Hub의 `<계정>/<저장소>`를 적고, 태그는 붙이지 않습니다.

## 완료 기준 및 채점

채점 시 제출된 저장소의 `main` 브랜치를 기준으로 아래 항목을 확인합니다.

- `Dockerfile`로 이미지를 빌드할 수 있는가?
- 최초 배포와 메시지 변경 배포에 해당하는 서로 다른 두 `main` push 커밋의 GitHub Actions 실행이 모두 성공했는가?
- `image_repository`의 Docker Hub 저장소에 두 커밋의 SHA 태그가 모두 존재하는가?
- 제출 시점 `main`의 최신 커밋도 GitHub Actions 배포가 성공하고 같은 SHA 태그의 이미지가 존재하는가?
- `http://<server_ip>/health`가 외부에서 정상 응답하는가?
- `/health`의 `hash`가 제출된 `src/` 코드의 해시와 일치하는가? 채점기는 제출 커밋의 Python 소스 파일로 값을 계산해 비교합니다.
- `GET /`의 메시지가 제출된 `src/main.py`의 내용과 일치하는가?
- 메시지 변경 커밋의 배포 후 EC2에 수동 접속하지 않고도 `/`의 응답이 새 문구로 바뀌었는가?

workflow 파일의 내용이나 GitHub Actions의 성공 표시만으로 배포 완료를 판단하지 않습니다. 실제 Docker Hub 이미지와 EC2 응답을 함께 확인합니다.

## 제출 방법

1. 과제 저장소의 `main` 브랜치에 구현 파일과 수정한 `deployment_info.py`를 push합니다.
2. 디스코드에 fork한 **과제 저장소 링크**를 제출합니다.
3. 채점이 끝날 때까지 EC2 서버와 배포된 서비스를 실행 상태로 유지합니다.
