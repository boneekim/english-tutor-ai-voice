#!/usr/bin/env python3
import os
import sys
from supabase import create_client
import toml

def load_secrets():
    """Load secrets from Streamlit secrets file"""
    try:
        with open('.streamlit/secrets.toml', 'r') as f:
            secrets = toml.load(f)
            return secrets.get('SUPABASE_URL'), secrets.get('SUPABASE_ANON_KEY')
    except Exception as e:
        print(f"❌ secrets.toml 파일 읽기 실패: {e}")
        return None, None

def check_database():
    """Check database contents"""
    print("🔍 데이터베이스 내용 확인")
    print("=" * 50)
    
    # Load secrets
    url, key = load_secrets()
    if not url or not key:
        print("❌ Supabase 설정 정보를 찾을 수 없습니다.")
        return False
    
    try:
        # Create client
        supabase = create_client(url, key)
        print(f"✅ Supabase 연결 성공: {url}")
        
        # Get all data
        result = supabase.table('english_tutor').select("*").eq('user_email', 'doyousee2@naver.com').execute()
        
        if result.data:
            print(f"\n📊 총 {len(result.data)}개 키워드 발견:")
            print("-" * 50)
            
            for i, item in enumerate(result.data, 1):
                print(f"{i}. 한국어: {item['korean']}")
                print(f"   영어: {item['english']}")
                print(f"   상황: {item['situation']}")
                print(f"   ID: {item['id']}")
                print(f"   생성일: {item['created_at']}")
                print()
                
            # Count by situation
            situations = {}
            for item in result.data:
                sit = item['situation']
                situations[sit] = situations.get(sit, 0) + 1
            
            print("📈 상황별 분포:")
            for sit, count in situations.items():
                print(f"   • {sit}: {count}개")
                
        else:
            print("📭 데이터베이스에 키워드가 없습니다.")
            
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 확인 실패: {e}")
        return False

if __name__ == "__main__":
    check_database() 