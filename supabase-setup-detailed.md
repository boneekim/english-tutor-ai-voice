# 🗃️ Supabase english_tutor 테이블 설정 완전 가이드

## 📋 현재 상황
- ✅ Supabase에 `english_tutor` 테이블이 이미 생성되어 있음
- ⚙️ 프로그램에 맞게 테이블 구조를 수정해야 함
- 🔗 boneekim (doyousee2@naver.com) 계정과 연동 필요

## 🎯 목표 테이블 구조
```
english_tutor 테이블
├── id (bigint, primary key, auto increment)
├── korean (text, not null) - 한국어 텍스트
├── english (text, not null) - 영어 텍스트
├── situation (text, not null) - 상황 분류
├── user_email (text, not null) - 사용자 이메일
├── created_at (timestamp) - 생성 시간
└── updated_at (timestamp) - 수정 시간
```

## 🔧 단계별 설정

### 1단계: Supabase 프로젝트 접속
1. https://supabase.com 접속
2. boneekim (doyousee2@naver.com) 계정으로 로그인
3. 기존 프로젝트 선택 또는 새 프로젝트 생성

### 2단계: SQL Editor에서 테이블 수정
Dashboard > SQL Editor로 이동 후 다음 쿼리 실행:

```sql
-- 1. 기존 테이블에 필요한 컬럼 추가
ALTER TABLE public.english_tutor ADD COLUMN IF NOT EXISTS korean text;
ALTER TABLE public.english_tutor ADD COLUMN IF NOT EXISTS english text;
ALTER TABLE public.english_tutor ADD COLUMN IF NOT EXISTS situation text;
ALTER TABLE public.english_tutor ADD COLUMN IF NOT EXISTS user_email text DEFAULT 'doyousee2@naver.com';
ALTER TABLE public.english_tutor ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT timezone('utc'::text, now());
ALTER TABLE public.english_tutor ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT timezone('utc'::text, now());

-- 2. 필수 컬럼 NOT NULL 설정
ALTER TABLE public.english_tutor ALTER COLUMN korean SET NOT NULL;
ALTER TABLE public.english_tutor ALTER COLUMN english SET NOT NULL;
ALTER TABLE public.english_tutor ALTER COLUMN situation SET NOT NULL;
ALTER TABLE public.english_tutor ALTER COLUMN user_email SET NOT NULL;
ALTER TABLE public.english_tutor ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE public.english_tutor ALTER COLUMN updated_at SET NOT NULL;

-- 3. RLS (Row Level Security) 활성화
ALTER TABLE public.english_tutor ENABLE ROW LEVEL SECURITY;

-- 4. 기존 정책 삭제
DROP POLICY IF EXISTS "Users can insert their own keywords" ON public.english_tutor;
DROP POLICY IF EXISTS "Users can view their own keywords" ON public.english_tutor;
DROP POLICY IF EXISTS "Users can update their own keywords" ON public.english_tutor;
DROP POLICY IF EXISTS "Users can delete their own keywords" ON public.english_tutor;
DROP POLICY IF EXISTS "Users can insert their own english_tutor" ON public.english_tutor;
DROP POLICY IF EXISTS "Users can view their own english_tutor" ON public.english_tutor;
DROP POLICY IF EXISTS "Users can update their own english_tutor" ON public.english_tutor;
DROP POLICY IF EXISTS "Users can delete their own english_tutor" ON public.english_tutor;

-- 5. 새로운 보안 정책 생성
CREATE POLICY "Users can insert their own english_tutor" ON public.english_tutor
    FOR INSERT WITH CHECK (user_email = 'doyousee2@naver.com');

CREATE POLICY "Users can view their own english_tutor" ON public.english_tutor
    FOR SELECT USING (user_email = 'doyousee2@naver.com');

CREATE POLICY "Users can update their own english_tutor" ON public.english_tutor
    FOR UPDATE USING (user_email = 'doyousee2@naver.com');

CREATE POLICY "Users can delete their own english_tutor" ON public.english_tutor
    FOR DELETE USING (user_email = 'doyousee2@naver.com');

-- 6. 업데이트 시간 자동 갱신 함수
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language plpgsql;

-- 7. 트리거 생성
DROP TRIGGER IF EXISTS keywords_updated_at ON public.english_tutor;
DROP TRIGGER IF EXISTS english_tutor_updated_at ON public.english_tutor;
CREATE TRIGGER english_tutor_updated_at
    BEFORE UPDATE ON public.english_tutor
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();
```

### 3단계: API 키 확인
1. Dashboard > Settings > API로 이동
2. 다음 정보 복사:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### 4단계: 프로젝트에 API 키 적용
`script.js` 파일에서 다음 부분 수정:

```javascript
// 이 부분을 찾아서
const SUPABASE_URL = 'https://your-project-id.supabase.co';
const SUPABASE_ANON_KEY = 'your-anon-key';

// 실제 값으로 교체
const SUPABASE_URL = 'https://xxxxx.supabase.co'; // 실제 URL
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIs...'; // 실제 키

// 그리고 이 부분의 주석 해제
// supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
// isSupabaseConnected = true;
↓
supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
isSupabaseConnected = true;
```

## 🧪 테스트

### 1. 브라우저에서 테스트
1. http://localhost:8000 접속
2. 개발자 도구 (F12) 열기
3. Console 탭에서 오류 확인
4. 키워드 추가 테스트

### 2. Supabase에서 데이터 확인
1. Dashboard > Table Editor > english_tutor 테이블 선택
2. 추가한 데이터가 표시되는지 확인

## 🔍 문제 해결

### 연결 오류 시
```
❌ 증상: "Failed to fetch" 오류
✅ 해결: URL과 API 키 재확인, 네트워크 상태 확인
```

### 권한 오류 시
```
❌ 증상: "Row Level Security policy violation" 오류
✅ 해결: RLS 정책 재설정, 이메일 주소 확인
```

### 테이블 구조 오류 시
```
❌ 증상: "column does not exist" 오류
✅ 해결: ALTER TABLE 쿼리 다시 실행
```

## 📊 샘플 데이터 추가 (선택사항)

테스트용 샘플 데이터를 추가하려면:

```sql
INSERT INTO public.english_tutor (korean, english, situation, user_email) VALUES
('안녕하세요', 'Hello', '일상대화', 'doyousee2@naver.com'),
('감사합니다', 'Thank you', '일상대화', 'doyousee2@naver.com'),
('회의실은 어디인가요?', 'Where is the meeting room?', '비즈니스', 'doyousee2@naver.com'),
('공항으로 가주세요', 'Please take me to the airport', '여행', 'doyousee2@naver.com');
```

## ✅ 완료 확인 체크리스트

- [ ] Supabase 테이블 구조 수정 완료
- [ ] RLS 정책 설정 완료
- [ ] API 키 확인 및 적용 완료
- [ ] script.js 파일 수정 완료
- [ ] 브라우저에서 연결 테스트 완료
- [ ] 키워드 추가/삭제 테스트 완료
- [ ] Supabase 대시보드에서 데이터 확인 완료

---

🎉 **설정 완료!** 이제 프로그램에서 Supabase에 데이터를 저장하고 불러올 수 있습니다.
