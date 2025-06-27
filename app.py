import streamlit as st
import streamlit.components.v1 as components
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



# 세션 상태 초기화
def init_session_state():
    if 'keywords' not in st.session_state:
        st.session_state.keywords = []
    if 'supabase_connected' not in st.session_state:
        st.session_state.supabase_connected = False
    if 'voice_gender' not in st.session_state:
        st.session_state.voice_gender = '여성'
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'search_situation' not in st.session_state:
        st.session_state.search_situation = "전체"

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

# TTS 음성 재생 함수
def play_tts(text, lang='ko', voice_gender='여성'):
    """TTS 음성 재생"""
    # 텍스트 안전화 (JavaScript injection 방지)
    safe_text = text.replace('"', '\\"').replace("'", "\\'").replace('\n', ' ').replace('\r', ' ')
    
    # 언어 설정
    voice_lang = 'ko-KR' if lang == 'ko' else 'en-US'
    gender_filter = 'female' if voice_gender == '여성' else 'male'
    
    # JavaScript 코드로 TTS 실행
    tts_html = f"""
    <script>
    function playTTS() {{
        try {{
            // 이전 음성 중단
            window.speechSynthesis.cancel();
            
            // Speech Synthesis 지원 확인
            if (!window.speechSynthesis) {{
                alert('이 브라우저는 음성 합성을 지원하지 않습니다.');
                return;
            }}
            
            // 새 음성 생성
            const utterance = new SpeechSynthesisUtterance("{safe_text}");
            utterance.lang = "{voice_lang}";
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 1;
            
            // 음성 선택 (영어의 경우 성별 고려)
            const voices = window.speechSynthesis.getVoices();
            if (voices.length > 0 && "{lang}" === "en") {{
                const targetVoice = voices.find(voice => 
                    voice.lang.includes("{voice_lang}") && 
                    voice.name.toLowerCase().includes("{gender_filter}")
                );
                if (targetVoice) {{
                    utterance.voice = targetVoice;
                }}
            }}
            
            // 이벤트 핸들러
            utterance.onstart = function() {{
                console.log('🔊 음성 재생 시작: {safe_text}');
            }};
            
            utterance.onend = function() {{
                console.log('✅ 음성 재생 완료');
            }};
            
            utterance.onerror = function(e) {{
                console.error('❌ 음성 재생 오류:', e);
            }};
            
            // 음성 재생
            window.speechSynthesis.speak(utterance);
            
        }} catch (error) {{
            console.error('TTS 실행 오류:', error);
            alert('음성 재생 중 오류가 발생했습니다.');
        }}
    }}
    
    // 페이지 로드 후 즉시 실행
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', playTTS);
    }} else {{
        playTTS();
    }}
    </script>
    
    <div style="text-align: center; padding: 10px; background-color: #e8f5e8; border-radius: 5px; margin: 5px 0;">
        <span style="color: #28a745; font-weight: bold;">🔊 "{text}" 음성 재생 중...</span>
    </div>
    """
    
    # HTML 컴포넌트로 실행
    components.html(tts_html, height=60)

# 메인 앱
def main():
    # 세션 상태 초기화
    init_session_state()
    
    # 앱 시작 시 데이터베이스에서 자동 로드 (기본 모든 키워드 표시)
    if 'auto_loaded' not in st.session_state:
        st.session_state.auto_loaded = True
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
                    st.success(f"🎯 데이터베이스에서 {len(converted_data)}개 키워드를 자동으로 불러왔습니다!")
                else:
                    # Supabase에 데이터가 없으면 로컬 데이터 로드
                    load_local_data()
                    st.info("📭 데이터베이스가 비어있어 로컬 데이터를 불러왔습니다")
            except Exception as e:
                # Supabase 연결 실패 시 로컬 데이터 로드
                st.warning(f"⚠️ 데이터베이스 연결 실패, 로컬 데이터를 로드합니다: {e}")
                load_local_data()
        else:
            # Supabase 초기화 실패 시 로컬 데이터 로드
            load_local_data()
            st.warning("⚠️ Supabase 초기화 실패, 로컬 데이터를 불러왔습니다")
    
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
    col_search, col_situation = st.columns([3, 2])
    
    with col_search:
        search_input = st.text_input(
            "🔍 키워드 검색", 
            placeholder="한국어 또는 영어로 검색하세요...",
            key="search_input_field",
            help="입력한 검색어가 포함된 키워드를 찾습니다"
        )
    
    with col_situation:
        all_situations = ["전체"] + list(set([k['situation'] for k in st.session_state.keywords]))
        situation_input = st.selectbox("🎯 상황 필터", all_situations, key="situation_filter")
    
    # 검색 및 초기화 버튼
    col_search_btn, col_clear_btn = st.columns([1, 1])
    
    with col_search_btn:
        if st.button("🔍 검색", use_container_width=True, type="primary"):
            st.session_state.search_performed = True
            st.session_state.search_query = search_input
            st.session_state.search_situation = situation_input
            st.rerun()
    
    with col_clear_btn:
        if st.button("🔄 전체보기", use_container_width=True):
            st.session_state.search_performed = False
            st.session_state.search_query = ""
            st.session_state.search_situation = "전체"
            # 검색창과 상황 필터 초기화를 위해 키를 안전하게 처리
            if 'search_input_field' in st.session_state:
                del st.session_state.search_input_field
            if 'situation_filter' in st.session_state:
                del st.session_state.situation_filter
            st.rerun()
    
    # 검색 및 필터링 적용
    if st.session_state.search_performed:
        # 검색이 수행된 경우에만 필터링
        filtered_keywords = st.session_state.keywords
        
        # 상황 필터링 (AND 조건)
        if st.session_state.search_situation != "전체":
            filtered_keywords = [k for k in filtered_keywords if k['situation'] == st.session_state.search_situation]
        
        # 검색어 필터링 (AND 조건)
        if st.session_state.search_query:
            search_query_lower = st.session_state.search_query.lower()
            filtered_keywords = [
                k for k in filtered_keywords 
                if search_query_lower in k['korean'].lower() or search_query_lower in k['english'].lower()
            ]
        
        # 검색 결과 표시
        if st.session_state.search_query or st.session_state.search_situation != "전체":
            search_conditions = []
            if st.session_state.search_query:
                search_conditions.append(f"키워드: '{st.session_state.search_query}'")
            if st.session_state.search_situation != "전체":
                search_conditions.append(f"상황: '{st.session_state.search_situation}'")
            
            condition_text = " + ".join(search_conditions)
            
            if filtered_keywords:
                st.success(f"🔍 검색 조건 ({condition_text}) 결과: **{len(filtered_keywords)}개** 키워드 발견")
            else:
                st.warning(f"❌ 검색 조건 ({condition_text})에 대한 결과가 없습니다")
    else:
        # 검색이 수행되지 않은 경우 전체 키워드 표시
        filtered_keywords = st.session_state.keywords
    
    if not filtered_keywords:
        st.info("📭 저장된 키워드가 없습니다. 위에서 새 키워드를 추가해보세요!")
    else:
        st.write(f"🔢 **{len(filtered_keywords)}개 키워드 발견**")
        
        # 키워드 표시
        for i, keyword in enumerate(filtered_keywords):
            with st.container():
                # 고유 ID 생성
                unique_id = abs(hash(keyword['korean'] + keyword['english'])) % 100000
                
                # 키워드 카드와 삭제 버튼을 함께 표시
                col_card, col_del = st.columns([9, 1])
                
                with col_card:
                    # 키워드 정보를 Streamlit 컴포넌트로만 깔끔하게 표시
                    with st.container():
                        # 키워드 제목
                        st.markdown(f"### {keyword['korean']}")
                        st.markdown(f"**{keyword['english']}**")
                        
                        # 메타데이터
                        col_meta1, col_meta2 = st.columns([1, 1])
                        with col_meta1:
                            st.info(f"📂 {keyword['situation']}")
                        with col_meta2:
                            created_time = datetime.fromisoformat(keyword['createdAt']).strftime('%Y-%m-%d %H:%M')
                            st.caption(f"🕒 {created_time}")
                        
                        # 음성 버튼들
                        st.write("🔊 **음성 재생:**")
                        col_kr, col_en, col_both = st.columns([1, 1, 1])
                        
                        with col_kr:
                            if st.button("🇰🇷 한국어", key=f"kr_{unique_id}", use_container_width=True, 
                                        help=f"'{keyword['korean']}' 한국어 음성 재생"):
                                play_tts(keyword['korean'], lang='ko', voice_gender=st.session_state.voice_gender)
                        
                        with col_en:
                            if st.button("🇺🇸 영어", key=f"en_{unique_id}", use_container_width=True, 
                                        help=f"'{keyword['english']}' 영어 음성 재생"):
                                play_tts(keyword['english'], lang='en', voice_gender=st.session_state.voice_gender)
                        
                        with col_both:
                            if st.button("🌍 둘 다", key=f"both_{unique_id}", use_container_width=True, 
                                        help="한국어 + 영어 순서대로 연속 재생"):
                                # 텍스트 안전화
                                safe_korean = keyword['korean'].replace('"', '\\"').replace("'", "\\'")
                                safe_english = keyword['english'].replace('"', '\\"').replace("'", "\\'")
                                
                                # 한국어와 영어를 연속으로 재생하는 JavaScript 코드
                                tts_both_html = f"""
                                <script>
                                function playBothLanguages() {{
                                    try {{
                                        // Speech Synthesis 지원 확인
                                        if (!window.speechSynthesis) {{
                                            alert('이 브라우저는 음성 합성을 지원하지 않습니다.');
                                            return;
                                        }}
                                        
                                        // 이전 음성 중단
                                        window.speechSynthesis.cancel();
                                        
                                        // 한국어 먼저 재생
                                        const utterance1 = new SpeechSynthesisUtterance("{safe_korean}");
                                        utterance1.lang = "ko-KR";
                                        utterance1.rate = 0.9;
                                        utterance1.pitch = 1;
                                        utterance1.volume = 1;
                                        
                                        // 한국어 재생 완료 후 영어 재생
                                        utterance1.onend = function() {{
                                            setTimeout(function() {{
                                                const utterance2 = new SpeechSynthesisUtterance("{safe_english}");
                                                utterance2.lang = "en-US";
                                                utterance2.rate = 0.9;
                                                utterance2.pitch = 1;
                                                utterance2.volume = 1;
                                                
                                                // 영어 음성 선택 (성별 고려)
                                                const voices = window.speechSynthesis.getVoices();
                                                if (voices.length > 0) {{
                                                    const genderFilter = "{st.session_state.voice_gender}" === "여성" ? "female" : "male";
                                                    const targetVoice = voices.find(voice => 
                                                        voice.lang.includes("en-US") && 
                                                        voice.name.toLowerCase().includes(genderFilter)
                                                    );
                                                    if (targetVoice) {{
                                                        utterance2.voice = targetVoice;
                                                    }}
                                                }}
                                                
                                                window.speechSynthesis.speak(utterance2);
                                            }}, 500);
                                        }};
                                        
                                        // 오류 처리
                                        utterance1.onerror = function(e) {{
                                            console.error('한국어 음성 재생 오류:', e);
                                        }};
                                        
                                        // 한국어 재생 시작
                                        window.speechSynthesis.speak(utterance1);
                                        
                                    }} catch (error) {{
                                        console.error('연속 재생 오류:', error);
                                        alert('음성 연속 재생 중 오류가 발생했습니다.');
                                    }}
                                }}
                                
                                // 페이지 로드 후 즉시 실행
                                if (document.readyState === 'loading') {{
                                    document.addEventListener('DOMContentLoaded', playBothLanguages);
                                }} else {{
                                    playBothLanguages();
                                }}
                                </script>
                                
                                <div style="text-align: center; padding: 10px; background-color: #fff3cd; border-radius: 5px; margin: 5px 0;">
                                    <span style="color: #856404; font-weight: bold;">🌍 "{keyword['korean']}" → "{keyword['english']}" 연속 재생 중...</span>
                                </div>
                                """
                                components.html(tts_both_html, height=60)
                
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
