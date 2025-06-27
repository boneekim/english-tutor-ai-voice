# 🚀 Streamlit Community Cloud 배포 가이드

## 📋 준비사항

### 1. 파일 구조 확인
```
english_tutor/
├── app.py                          # 메인 Streamlit 앱
├── requirements.txt                # Python 패키지 의존성
├── .streamlit/
│   ├── config.toml                # Streamlit 설정
│   └── secrets.toml               # 보안 키 (GitHub에 업로드 안됨)
├── README.md                      # 프로젝트 설명
└── 기타 파일들...
```

## 🔧 Step 1: GitHub 리포지토리 준비

### 현재 상태 확인
```bash
git status
git add .
git commit -m "🚀 Streamlit 앱으로 변환

✅ 주요 변경사항:
- app.py: Streamlit 기반 메인 앱
- requirements.txt: Python 패키지 의존성
- .streamlit/config.toml: Streamlit 설정
- TTS 기능: Google Translate API 활용
- Supabase 연동: Python 라이브러리 사용
- 로컬 저장: JSON 파일 + st.session_state

🎯 기능:
- 키워드 추가/삭제
- 음성 재생 (한국어/영어)
- 상황별 필터링
- Supabase 데이터 동기화
- 실시간 통계"

git push origin main
```

## 🌐 Step 2: Streamlit Community Cloud 배포

### 1. Streamlit Community Cloud 접속
1. https://share.streamlit.io 방문
2. GitHub 계정으로 로그인 (boneekim 계정)

### 2. 새 앱 배포
1. **"New app"** 버튼 클릭
2. 설정 정보 입력:
   - **Repository**: `boneekim/english-tutor-ai-voice`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: `english-tutor-ai-voice` (또는 원하는 URL)

### 3. Secrets 설정
배포 전에 **"Advanced settings"** 클릭 후 **Secrets** 탭에서 설정:

```toml
# 이 내용을 Secrets 박스에 입력
SUPABASE_URL = "https://your-actual-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-actual-anon-key"
```

⚠️ **중요**: 실제 Supabase URL과 API Key로 교체해야 합니다!

### 4. 배포 실행
- **"Deploy!"** 버튼 클릭
- 약 2-3분 후 앱이 배포됩니다

## 🔍 Step 3: 배포 후 확인사항

### 1. 기본 기능 테스트
- [ ] 앱이 정상적으로 로드되는지 확인
- [ ] 키워드 추가 기능 테스트
- [ ] 삭제 기능 테스트
- [ ] 필터링 기능 테스트

### 2. Supabase 연동 확인
- [ ] Supabase 연결 상태 확인 (사이드바에서)
- [ ] 데이터 동기화 버튼 테스트
- [ ] 실제 데이터가 Supabase에 저장되는지 확인

### 3. TTS 기능 확인
- [ ] '🔊 듣기' 버튼 클릭 시 음성 재생되는지 확인
- [ ] 한국어와 영어 모두 재생되는지 확인

## 🛠️ 문제 해결

### 배포 실패 시
```
❌ ModuleNotFoundError
✅ requirements.txt에서 패키지 버전 확인 및 수정
```

```
❌ Supabase 연결 오류
✅ Secrets 설정에서 URL과 Key 재확인
```

```
❌ TTS 재생 안됨
✅ 브라우저 설정에서 자동재생 허용
```

## 📱 Step 4: 도메인 설정 (선택사항)

### 커스텀 도메인 사용
1. Streamlit Community Cloud에서 "Settings" 클릭
2. "Custom domain" 섹션에서 도메인 설정
3. DNS 설정에 CNAME 레코드 추가

## 🔄 Step 5: 자동 배포 설정

### GitHub와 자동 동기화
- GitHub 리포지토리에 push할 때마다 자동으로 재배포됩니다
- 코드 변경 후 약 1-2분 내에 반영됩니다

## 🎯 완료된 배포 URL

배포 완료 후 접속 가능한 URL:
- **앱 URL**: `https://english-tutor-ai-voice.streamlit.app`
- **GitHub**: `https://github.com/boneekim/english-tutor-ai-voice`

## 📊 모니터링

### 사용량 확인
1. Streamlit Community Cloud 대시보드에서 확인
2. 사용자 수, 세션 시간 등 통계 제공

### 로그 확인
1. 앱 설정에서 "Logs" 탭 클릭
2. 오류 발생 시 로그에서 원인 파악 가능

---

## 🎉 축하합니다!

영어 AI음성지원 프로그램이 성공적으로 배포되었습니다!

### 다음 단계 제안:
- [ ] 사용자 피드백 수집
- [ ] 추가 기능 개발 (발음 평가, 게임 모드 등)
- [ ] 모바일 최적화
- [ ] 다국어 지원

💡 **Tip**: 배포된 앱의 URL을 친구들과 공유하여 함께 영어 학습을 즐겨보세요!
