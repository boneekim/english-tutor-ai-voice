#!/usr/bin/env python3
"""
Supabase 연동 테스트 스크립트
실제 API 키를 입력받아 연결을 테스트합니다.
"""

import sys

def test_supabase_connection():
    try:
        from supabase import create_client
        
        print("🔍 Supabase 연결 테스트")
        print("=" * 50)
        
        # 사용자에게 실제 키 입력 요청
        print("\n�� 실제 Supabase 정보를 입력하세요:")
        url = input("Project URL (https://xxxxx.supabase.co): ").strip()
        key = input("Anon Key: ").strip()
        
        if not url or not key:
            print("❌ URL과 Key를 모두 입력해주세요.")
            return False
        
        print(f"\n🔗 연결 시도: {url}")
        
        # Supabase 클라이언트 생성
        supabase = create_client(url, key)
        
        # english_tutor 테이블 확인
        print("📊 english_tutor 테이블 데이터 확인...")
        result = supabase.table('english_tutor').select("*").limit(5).execute()
        
        print(f"✅ 연결 성공!")
        print(f"📦 테이블 데이터: {len(result.data)}개 행 발견")
        
        if result.data:
            print("\n📋 샘플 데이터:")
            for i, item in enumerate(result.data[:3], 1):
                print(f"  {i}. {item.get('korean', 'N/A')} - {item.get('english', 'N/A')}")
        else:
            print("📝 테이블이 비어있습니다.")
        
        return True
        
    except ImportError:
        print("❌ supabase 패키지가 설치되지 않았습니다.")
        print("설치 명령어: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    if success:
        print("\n🎉 Supabase 연동이 성공적으로 완료되었습니다!")
        print("이제 .streamlit/secrets.toml 파일에 실제 키를 설정하세요.")
    else:
        print("\n🔧 Supabase 설정을 다시 확인해주세요.")
