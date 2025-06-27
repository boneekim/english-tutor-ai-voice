import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from supabase import create_client, Client
import requests
from io import BytesIO
import base64

# Streamlit 페이지 설정
st.set_page_config(
    page_title="🎯 영어 AI음성지원 프로그램",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Supabase 설정
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://your-project-id.supabase.co")
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY", "your-anon-key")

# Supabase 클라이언트 초기화
@st.cache_resource
def init_supabase():
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return supabase
    except Exception as e:
        st.error(f"Supabase 연결 오류: {e}")
        return None

# 개선된 TTS 기능 - JavaScript로 직접 음성 재생
def create_tts_js(korean_text, english_text, gender='female'):
    """한국어와 영어 TTS를 위한 JavaScript 함수 생성"""
    
    html_code = f"""
    <script>
    // 음성 재생 함수들
    function playKorean_{abs(hash(korean_text + english_text)) % 100000}() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance('{korean_text}');
            utterance.lang = 'ko-KR';
            utterance.rate = 0.8;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            const voices = window.speechSynthesis.getVoices();
            let selectedVoice = voices.find(voice => 
                voice.lang.includes('ko') && 
                ({'true' if gender == 'female' else 'false'} ? 
                    (voice.name.includes('Female') || voice.name.includes('여성') || voice.name.includes('Google')) :
                    (voice.name.includes('Male') || voice.name.includes('남성'))
                )
            );
            
            if (selectedVoice) utterance.voice = selectedVoice;
            window.speechSynthesis.speak(utterance);
        }}
    }}
    
    function playEnglish_{abs(hash(korean_text + english_text)) % 100000}() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance('{english_text}');
            utterance.lang = 'en-US';
            utterance.rate = 0.8;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            const voices = window.speechSynthesis.getVoices();
            let selectedVoice = voices.find(voice => 
                voice.lang.includes('en') && 
                ({'true' if gender == 'female' else 'false'} ? 
                    (voice.name.includes('Female') || voice.name.includes('Google')) :
                    (voice.name.includes('Male'))
                )
            );
            
            if (selectedVoice) utterance.voice = selectedVoice;
            window.speechSynthesis.speak(utterance);
        }}
    }}
    
    function playBoth_{abs(hash(korean_text + english_text)) % 100000}() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            
            // 한국어 먼저 재생
            const koreanUtterance = new SpeechSynthesisUtterance('{korean_text}');
            koreanUtterance.lang = 'ko-KR';
            koreanUtterance.rate = 0.8;
            koreanUtterance.pitch = 1.0;
            koreanUtterance.volume = 1.0;
            
            const voices = window.speechSynthesis.getVoices();
            let koreanVoice = voices.find(voice => 
                voice.lang.includes('ko') && 
                ({'true' if gender == 'female' else 'false'} ? 
                    (voice.name.includes('Female') || voice.name.includes('여성') || voice.name.includes('Google')) :
                    (voice.name.includes('Male') || voice.name.includes('남성'))
                )
            );
            
            if (koreanVoice) koreanUtterance.voice = koreanVoice;
            
            // 한국어 재생 완료 후 영어 재생
            koreanUtterance.onend = function() {{
                const englishUtterance = new SpeechSynthesisUtterance('{english_text}');
                englishUtterance.lang = 'en-US';
                englishUtterance.rate = 0.8;
                englishUtterance.pitch = 1.0;
                englishUtterance.volume = 1.0;
                
                let englishVoice = voices.find(voice => 
                    voice.lang.includes('en') && 
                    ({'true' if gender == 'female' else 'false'} ? 
                        (voice.name.includes('Female') || voice.name.includes('Google')) :
                        (voice.name.includes('Male'))
                    )
                );
                
                if (englishVoice) englishUtterance.voice = englishVoice;
                window.speechSynthesis.speak(englishUtterance);
            }};
            
            window.speechSynthesis.speak(koreanUtterance);
        }}
    }}
    
    // 음성 로드 대기
    if (window.speechSynthesis.getVoices().length === 0) {{
        window.speechSynthesis.onvoiceschanged = function() {{
            console.log('음성 로드 완료');
        }};
    }}
    </script>
    """
    return html_code

# 세션 상태 초기화
def init_session_state():
    if 'keywords' not in st.session_state:
        st.session_state.keywords = []
    if 'supabase_connected' not in st.session_state:
        st.session_state.supabase_connected = False
    if 'voice_gender' not in st.session_state:
        st.session_state.voice_gender = '여성'

# 로컬 데이터 로드
def load_local_data():
    """로컬 JSON 파일에서 데이터 로드"""
    try:
        if os.path.exists('keywords_data.json'):
            with open('keywords_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                st.session_state.keywords = data.get('keywords', [])
    except Exception as e:
        st.error(f"로컬 데이터 로드 오류: {e}")

# 로컬 데이터 저장
def save_local_data():
    """로컬 JSON 파일에 데이터 저장"""
    try:
        data = {
            'keywords': st.session_state.keywords,
            'saved_at': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        with open('keywords_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"로컬 데이터 저장 오류: {e}")

# Supabase에 키워드 저장
def save_to_supabase(keyword_data):
    """Supabase에 키워드 저장"""
    supabase = init_supabase()
    if supabase:
        try:
            result = supabase.table('english_tutor').insert({
                'korean': keyword_data['korean'],
                'english': keyword_data['english'],
                'situation': keyword_data['situation'],
                'user_email': 'doyousee2@naver.com',
                'created_at': keyword_data['createdAt']
            }).execute()
            # 저장된 데이터에서 Supabase ID 반환
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            return True
        except Exception as e:
            st.error(f"Supabase 저장 오류: {e}")
            return False
    return False

# Supabase에서 키워드 로드
def load_from_supabase():
    """Supabase에서 키워드 로드"""
    supabase = init_supabase()
    if supabase:
        try:
            result = supabase.table('english_tutor').select("*").eq('user_email', 'doyousee2@naver.com').execute()
            return result.data
        except Exception as e:
            st.error(f"Supabase 로드 오류: {e}")
            return []
    return []

# 키워드 추가 함수
def add_keyword(korean, english, situation):
    """새 키워드 추가"""
    new_keyword = {
        'id': str(int(datetime.now().timestamp() * 1000)),
        'korean': korean,
        'english': english,
        'situation': situation,
        'createdAt': datetime.now().isoformat()
    }
    
    # 로컬에 추가
    st.session_state.keywords.insert(0, new_keyword)
    
    # 로컬 파일에 저장
    save_local_data()
    
    # Supabase에 저장 시도
    supabase_id = save_to_supabase(new_keyword)
    if supabase_id and isinstance(supabase_id, int):
        # Supabase ID로 로컬 데이터 업데이트
        new_keyword['id'] = str(supabase_id)
        new_keyword['supabase_id'] = supabase_id
        st.session_state.keywords[0] = new_keyword  # 첫 번째 항목 업데이트
    
    return True

# 키워드 삭제 함수
def delete_keyword(keyword_id):
    """키워드 삭제"""
    # 삭제할 키워드 찾기
    keyword_to_delete = None
    for k in st.session_state.keywords:
        if k['id'] == keyword_id:
            keyword_to_delete = k
            break
    
    # Supabase에서 삭제 시도
    supabase = init_supabase()
    if supabase and keyword_to_delete:
        try:
            # 먼저 ID로 삭제 시도
            try:
                result = supabase.table('english_tutor').delete().eq('id', int(keyword_id)).execute()
                st.success("✅ Supabase에서 ID로 삭제 완료")
            except:
                # ID로 삭제 실패 시 한국어와 영어로 매칭해서 삭제
                result = supabase.table('english_tutor').delete().match({
                    'korean': keyword_to_delete['korean'],
                    'english': keyword_to_delete['english'],
                    'user_email': 'doyousee2@naver.com'
                }).execute()
                st.success("✅ Supabase에서 내용 매칭으로 삭제 완료")
        except Exception as e:
            st.error(f"❌ Supabase 삭제 오류: {e}")
            
    # 로컬에서 삭제
    st.session_state.keywords = [k for k in st.session_state.keywords if k['id'] != keyword_id]
    save_local_data()

# 메인 앱
def main():
    # 세션 상태 초기화
    init_session_state()
    
    # 앱 시작 시 Supabase 데이터 우선 로드, 실패 시 로컬 데이터 로드
    if not st.session_state.keywords:
        # 먼저 Supabase에서 데이터 로드 시도
        supabase = init_supabase()
        if supabase:
            try:
                supabase_data = load_from_supabase()
                if supabase_data:
                    # Supabase 데이터를 로컬 형식으로 변환
                    converted_data = []
                    for item in supabase_data:
                        converted_data.append({
                            'id': str(item['id']),
                            'supabase_id': item['id'],
                            'korean': item['korean'],
                            'english': item['english'],
                            'situation': item['situation'],
                            'createdAt': item['created_at']
                        })
                    st.session_state.keywords = converted_data
                    # 로컬에도 저장 (백업용)
                    save_local_data()
                    # 자동 로드 성공 표시
                    if 'auto_loaded' not in st.session_state:
                        st.session_state.auto_loaded = True
                        st.success(f"🎯 데이터베이스에서 {len(converted_data)}개 키워드를 자동으로 불러왔습니다!")
                else:
                    # Supabase에 데이터가 없으면 로컬 데이터 로드
                    load_local_data()
                    if 'auto_loaded' not in st.session_state:
                        st.session_state.auto_loaded = True
                        st.info("📭 데이터베이스가 비어있어 로컬 데이터를 불러왔습니다")
            except Exception as e:
                # Supabase 연결 실패 시 로컬 데이터 로드
                st.warning(f"⚠️ 데이터베이스 연결 실패, 로컬 데이터를 로드합니다: {e}")
                load_local_data()
        else:
            # Supabase 초기화 실패 시 로컬 데이터 로드
            load_local_data()
    
    # 헤더
    st.title("🎯 영어 AI음성지원 프로그램")
    st.markdown("**한국어와 영어 키워드를 추가하고 AI 음성으로 학습하세요!**")
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # Supabase 연결 상태
        supabase = init_supabase()
        if supabase:
            st.success("✅ Supabase 연결됨")
            st.session_state.supabase_connected = True
        else:
            st.warning("⚠️ Supabase 연결 필요")
            st.session_state.supabase_connected = False
        
        # 데이터 수동 동기화 (앱 시작 시 자동 로드됨)
        st.info("💡 앱 시작 시 데이터베이스에서 자동으로 키워드를 불러옵니다")
        
        if st.button("🔄 수동으로 데이터 새로고침"):
            if supabase:
                supabase_data = load_from_supabase()
                if supabase_data:
                    # Supabase 데이터를 로컬 형식으로 변환 (Supabase ID 유지)
                    converted_data = []
                    for item in supabase_data:
                        converted_data.append({
                            'id': str(item['id']),  # Supabase ID 사용
                            'supabase_id': item['id'],  # 원본 Supabase ID 보존
                            'korean': item['korean'],
                            'english': item['english'],
                            'situation': item['situation'],
                            'createdAt': item['created_at']
                        })
                    st.session_state.keywords = converted_data
                    save_local_data()
                    st.success(f"✅ {len(supabase_data)}개 키워드 새로고침 완료")
                    st.rerun()
                else:
                    st.info("📭 데이터베이스에 저장된 키워드가 없습니다")
            else:
                st.error("❌ Supabase 연결이 필요합니다")
        
        # 음성 설정
        st.header("🔊 음성 설정")
        st.session_state.voice_gender = st.selectbox(
            "기본 음성 성별", 
            ["여성", "남성"], 
            index=0 if st.session_state.voice_gender == "여성" else 1,
            key="global_voice_gender"
        )
        
        # 통계
        st.header("📊 통계")
        total_keywords = len(st.session_state.keywords)
        st.metric("총 키워드 수", total_keywords)
        
        if st.session_state.keywords:
            situations = {}
            for keyword in st.session_state.keywords:
                sit = keyword['situation']
                situations[sit] = situations.get(sit, 0) + 1
            
            st.write("**상황별 분포:**")
            for situation, count in situations.items():
                st.write(f"• {situation}: {count}개")
    
    # 키워드 추가 섹션
    st.header("➕ 키워드 추가")
    
    with st.form("keyword_form"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            korean_input = st.text_input("한국어", placeholder="한국어 키워드를 입력하세요")
            english_input = st.text_input("영어", placeholder="영어 키워드를 입력하세요")
        
        with col2:
            situation_options = [
                "일상대화", "비즈니스", "여행", "쇼핑", 
                "레스토랑", "병원", "학교", "취미"
            ]
            situation_input = st.selectbox("상황 카테고리", situation_options)
            st.info("💡 사이드바에서 기본 음성 성별을 선택할 수 있습니다")
        
        submitted = st.form_submit_button("📝 키워드 추가", use_container_width=True)
        
        if submitted:
            if korean_input and english_input and situation_input:
                if add_keyword(korean_input, english_input, situation_input):
                    st.success("✅ 키워드가 성공적으로 추가되었습니다!")
                    st.rerun()
            else:
                st.error("❌ 모든 필드를 입력해주세요.")
    
    # 구분선
    st.markdown("---")
    
    # 저장된 키워드 목록 섹션
    st.header("📚 저장된 키워드 목록")
    
    # 검색 및 필터링 섹션
    col_search, col_situation, col_clear = st.columns([3, 2, 1])
    
    with col_search:
        search_query = st.text_input(
            "🔍 키워드 검색", 
            placeholder="한국어 또는 영어로 검색하세요...",
            key="search_input",
            help="입력한 검색어가 포함된 키워드를 찾습니다"
        )
    
    with col_situation:
        all_situations = ["전체"] + list(set([k['situation'] for k in st.session_state.keywords]))
        selected_situation = st.selectbox("🎯 상황 필터", all_situations, key="filter")
    
    with col_clear:
        st.write("")  # 공백 추가 (높이 맞춤)
        if st.button("🔄 전체보기", help="검색 및 필터 초기화"):
            # 검색창 초기화 및 페이지 새로고침
            st.session_state.search_input = ""
            st.rerun()
    
    # 검색 및 필터링 적용
    filtered_keywords = st.session_state.keywords
    
    # 상황 필터링
    if selected_situation != "전체":
        filtered_keywords = [k for k in filtered_keywords if k['situation'] == selected_situation]
    
    # 검색어 필터링
    if search_query:
        search_query_lower = search_query.lower()
        filtered_keywords = [
            k for k in filtered_keywords 
            if search_query_lower in k['korean'].lower() or search_query_lower in k['english'].lower()
        ]
    
    # 검색 상태 표시
    if search_query:
        if filtered_keywords:
            st.success(f"🔍 '{search_query}' 검색 결과: **{len(filtered_keywords)}개** 키워드 발견")
        else:
            st.warning(f"❌ '{search_query}'에 대한 검색 결과가 없습니다")
    elif selected_situation != "전체":
        st.info(f"📂 '{selected_situation}' 카테고리: **{len(filtered_keywords)}개** 키워드")
    
    if not filtered_keywords:
        st.info("📭 저장된 키워드가 없습니다. 위에서 새 키워드를 추가해보세요!")
    else:
        st.write(f"🔢 **{len(filtered_keywords)}개 키워드 발견**")
        
        # 키워드 표시
        for i, keyword in enumerate(filtered_keywords):
            with st.container():
                # 고유 ID 생성
                unique_id = abs(hash(keyword['korean'] + keyword['english'])) % 100000
                gender = 'female' if st.session_state.voice_gender == '여성' else 'male'
                
                # TTS JavaScript 생성
                tts_js = create_tts_js(keyword['korean'], keyword['english'], gender)
                st.components.v1.html(tts_js, height=0)
                
                # 키워드 카드와 삭제 버튼을 함께 표시
                col_card, col_del = st.columns([9, 1])
                
                with col_card:
                    # 키워드 카드 디자인
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                               padding: 20px; border-radius: 15px; margin-bottom: 15px; color: white;">
                        <h3 style="margin: 0; font-size: 1.5em;">{keyword['korean']}</h3>
                        <p style="margin: 8px 0; font-size: 1.2em; opacity: 0.9;">{keyword['english']}</p>
                        
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px;">
                            <span style="background-color: rgba(255,255,255,0.2); padding: 6px 12px; 
                                       border-radius: 20px; font-size: 0.9em;">📂 {keyword['situation']}</span>
                            <span style="opacity: 0.7; font-size: 0.8em;">
                                {datetime.fromisoformat(keyword['createdAt']).strftime('%Y-%m-%d %H:%M')}
                            </span>
                        </div>
                        
                        <div style="margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
                            <button onclick="playKorean_{unique_id}()" 
                                    style="background-color: rgba(255,255,255,0.2); color: white; border: none; 
                                           padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 14px;
                                           transition: all 0.3s;"
                                    onmouseover="this.style.backgroundColor='rgba(255,255,255,0.4)'"
                                    onmouseout="this.style.backgroundColor='rgba(255,255,255,0.2)'">
                                🔊 한국어
                            </button>
                            
                            <button onclick="playEnglish_{unique_id}()" 
                                    style="background-color: rgba(255,255,255,0.2); color: white; border: none; 
                                           padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 14px;
                                           transition: all 0.3s;"
                                    onmouseover="this.style.backgroundColor='rgba(255,255,255,0.4)'"
                                    onmouseout="this.style.backgroundColor='rgba(255,255,255,0.2)'">
                                🔊 영어
                            </button>
                            
                            <button onclick="playBoth_{unique_id}()" 
                                    style="background-color: rgba(255,255,255,0.3); color: white; border: none; 
                                           padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 14px;
                                           font-weight: bold; transition: all 0.3s;"
                                    onmouseover="this.style.backgroundColor='rgba(255,255,255,0.5)'"
                                    onmouseout="this.style.backgroundColor='rgba(255,255,255,0.3)'">
                                🔊 둘 다
                            </button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_del:
                    # 삭제 버튼 (Streamlit 버튼)
                    if st.button("🗑️", key=f"del_{keyword['id']}", help="키워드 삭제", use_container_width=True):
                        delete_keyword(keyword['id'])
                        st.success("🗑️ 키워드가 삭제되었습니다.")
                        st.rerun()
                
                st.markdown("---")
    
    # 하단 정보
    st.markdown("""
    <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-top: 30px;">
        <h3 style="color: #495057; margin-bottom: 15px;">💡 사용 팁</h3>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
            <div style="margin: 10px; text-align: center;">
                <div style="font-size: 2em; margin-bottom: 5px;">🔊</div>
                <p style="margin: 0; font-weight: bold;">음성 듣기</p>
                <p style="margin: 0; font-size: 0.9em; color: #6c757d;">각 언어별로 들을 수 있어요</p>
            </div>
            <div style="margin: 10px; text-align: center;">
                <div style="font-size: 2em; margin-bottom: 5px;">🔍</div>
                <p style="margin: 0; font-weight: bold;">키워드 검색</p>
                <p style="margin: 0; font-size: 0.9em; color: #6c757d;">한국어/영어로 빠른 검색</p>
            </div>
            <div style="margin: 10px; text-align: center;">
                <div style="font-size: 2em; margin-bottom: 5px;">⚙️</div>
                <p style="margin: 0; font-weight: bold;">음성 설정</p>
                <p style="margin: 0; font-size: 0.9em; color: #6c757d;">사이드바에서 남성/여성 선택</p>
            </div>
            <div style="margin: 10px; text-align: center;">
                <div style="font-size: 2em; margin-bottom: 5px;">☁️</div>
                <p style="margin: 0; font-weight: bold;">자동 로드</p>
                <p style="margin: 0; font-size: 0.9em; color: #6c757d;">앱 시작 시 데이터베이스에서 자동 로드</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
