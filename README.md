# CRUX 워크샵 2025 안내 페이지

## 📋 프로젝트 소개
CRUX 워크샵 2025 행사 정보를 공유하기 위한 웹 애플리케이션입니다. 차량 배치, 팀 구성, 일정, 준비물 목록 등의 정보를 제공합니다.

## 🛠 기술 스택
- Backend: FastAPI
- Frontend: Jinja2 Templates, Bootstrap 5
- 서버: Uvicorn
- 프록시: Nginx

## 🔧 설치 및 실행 방법

### 1. 환경 설정
```bash
# Conda 환경 생성
conda create -n workshop python=3.9
conda activate workshop

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
# 서버 시작
./workshop.sh start

# 서버 상태 확인
./workshop.sh status

# 서버 중지
./workshop.sh stop

# 서버 재시작
./workshop.sh restart
```

## 🌐 주요 기능

### 1. 차량 이동
- 차량별 탑승자 정보
- 펜션 위치 정보
- 펜션 예약 페이지 링크

### 2. 팀 배치
- 팀별 구성원 목록
- 비밀번호 보호 기능
- 진행자 정보

### 3. 스케줄
- 시간대별 일정 안내

### 4. 준비물 목록
- 장보기 목록
- 장비/전자기기
- 공동 준비물
- 개인 준비물
- 기타 체크리스트

## 🔒 보안
- 민감한 정보(팀 배치, 스케줄)는 비밀번호로 보호

## 📱 반응형 디자인
- 모바일/태블릿/데스크톱 환경 모두 지원
- 부트스트랩 기반의 반응형 레이아웃
- 모바일에서도 최적화된 사용자 경험

## 🔍 접속 정보
- 포트: 10328
- URL: `http://ns3.cruxdata.co.kr:10328`

## 📄 라이선스
CRUX Data 내부용
