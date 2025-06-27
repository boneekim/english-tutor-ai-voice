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

# TTS 기능을 위한 함수
def text_to_speech_url(text, lang='en'):
    """Google Translate TTS API를 사용하여 음성 URL 생성"""
    try:
        # Google Translate TTS (무료, 제한적)
        base_url = "https://translate.google.com/translate_tts"
        params = {
            'ie': 'UTF-8',
            'tl': lang,
            'client': 'tw-ob',
            'q': text
        }
        url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return url
    except Exception as e:
        st.error(f"TTS URL 생성 오류: {e}")
        return None

# 세션 상태 초기화
def init_session_state():
    if 'keywords' not in st.session_state:
        st.session_state.keywords = []
    if 'supabase_connected' not in st.session_state:
        st.session_state.supabase_connected = False

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
    save_to_supabase(new_keyword)
    
    return True

# 키워드 삭제 함수
def delete_keyword(keyword_id):
    """키워드 삭제"""
    st.session_state.keywords = [k for k in st.session_state.keywords if k['id'] != keyword_id]
    save_local_data()

# 메인 앱
def main():
    # 세션 상태 초기화
    init_session_state()
    
    # 앱 시작 시 로컬 데이터 로드
    if not st.session_state.keywords:
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
        
        # 데이터 동기화
        if st.button("�� Supabase에서 데이터 동기화"):
            if supabase:
                supabase_data = load_from_supabase()
                if supabase_data:
                    # Supabase 데이터를 로컬 형식으로 변환
                    converted_data = []
                    for item in supabase_data:
                        converted_data.append({
                            'id': str(item['id']),
                            'korean': item['korean'],
                            'english': item['english'],
                            'situation': item['situation'],
                            'createdAt': item['created_at']
                        })
                    st.session_state.keywords = converted_data
                    save_local_data()
                    st.success(f"✅ {len(supabase_data)}개 키워드 동기화 완료")
                    st.rerun()
            else:
                st.error("❌ Supabase 연결이 필요합니다")
        
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
    
    # 메인 컨텐츠를 두 개 컬럼으로 분할
    col1, col2 = st.columns([1, 1])
    
    # 키워드 추가 섹션
    with col1:
        st.header("➕ 키워드 추가")
        
        with st.form("keyword_form"):
            korean_input = st.text_input("한국어", placeholder="한국어를 입력하세요")
            english_input = st.text_input("영어", placeholder="English words here")
            
            situation_options = [
                "일상대화", "비즈니스", "여행", "쇼핑", 
                "레스토랑", "병원", "학교", "취미"
            ]
            situation_input = st.selectbox("상황", situation_options)
            
            submitted = st.form_submit_button("추가", use_container_width=True)
            
            if submitted:
                if korean_input and english_input and situation_input:
                    if add_keyword(korean_input, english_input, situation_input):
                        st.success("✅ 키워드가 성공적으로 추가되었습니다!")
                        st.rerun()
                else:
                    st.error("❌ 모든 필드를 입력해주세요.")
    
    # 저장된 키워드 목록 섹션
    with col2:
        st.header("📚 저장된 키워드 목록")
        
        # 필터링
        all_situations = ["전체"] + list(set([k['situation'] for k in st.session_state.keywords]))
        selected_situation = st.selectbox("상황 필터", all_situations, key="filter")
        
        # 필터링된 키워드
        filtered_keywords = st.session_state.keywords
        if selected_situation != "전체":
            filtered_keywords = [k for k in st.session_state.keywords if k['situation'] == selected_situation]
        
        if not filtered_keywords:
            st.info("저장된 키워드가 없습니다.")
        else:
            # 키워드 표시
            for i, keyword in enumerate(filtered_keywords):
                with st.container():
                    col_text, col_actions = st.columns([3, 1])
                    
                    with col_text:
                        st.markdown(f"""
                        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                            <h4 style="margin: 0; color: #333;">{keyword['korean']}</h4>
                            <p style="margin: 5px 0; color: #667eea; font-style: italic;">{keyword['english']}</p>
                            <small style="background-color: #e9ecef; padding: 2px 8px; border-radius: 12px; color: #6c757d;">{keyword['situation']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_actions:
                        # TTS 버튼
                        if st.button("🔊", key=f"tts_{keyword['id']}", help="듣기"):
                            # 영어 TTS
                            english_url = text_to_speech_url(keyword['english'], 'en')
                            if english_url:
                                st.markdown(f"""
                                <audio controls autoplay style="width: 100%;">
                                    <source src="{english_url}" type="audio/mpeg">
                                    Your browser does not support the audio element.
                                </audio>
                                """, unsafe_allow_html=True)
                            
                            # 한국어 TTS
                            korean_url = text_to_speech_url(keyword['korean'], 'ko')
                            if korean_url:
                                st.markdown(f"""
                                <audio controls style="width: 100%;">
                                    <source src="{korean_url}" type="audio/mpeg">
                                    Your browser does not support the audio element.
                                </audio>
                                """, unsafe_allow_html=True)
                        
                        # 삭제 버튼
                        if st.button("🗑️", key=f"del_{keyword['id']}", help="삭제"):
                            delete_keyword(keyword['id'])
                            st.success("키워드가 삭제되었습니다.")
                            st.rerun()
    
    # 하단 정보
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d;">
        <p>💡 <strong>Tip:</strong> 매일 꾸준히 사용하여 영어 실력을 향상시켜보세요!</p>
        <p>🔊 '듣기' 버튼을 클릭하면 영어와 한국어 발음을 들을 수 있습니다.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
