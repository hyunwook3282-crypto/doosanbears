import os
import re
import html
import requests
from google import genai

# =========================================================
# 🔥 깃허브 환경 변수(Secrets)를 불러오는 코드로 변경
# =========================================================
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def fetch_naver_news_api(keyword="두산베어스", display_count=10):
    client_id = NAVER_CLIENT_ID.strip()
    client_secret = NAVER_CLIENT_SECRET.strip()
    
    if not client_id or not client_secret:
        return "⚠️ 네이버 Client ID 및 Client Secret이 올바르게 설정되지 않았습니다."
    
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        "query": keyword,
        "display": display_count,  # 최신 기사 10개 제한
        "sort": "date"             # 최신순 정렬
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # 401 에러 발생 시 원인 안내
        if response.status_code == 401:
            return (
                f"❌ 네이버 API 호출 실패 (401 인증 오류):\n"
                f"1. 네이버 개발자 센터 [내 애플리케이션] -> [API 설정]에서 '검색' API가 추가되어 있는지 확인하세요.\n"
                f"2. Client ID와 Secret 값이 정확히 입력되었는지 확인하세요.\n"
                f"응답 본문: {response.text}"
            )
        elif response.status_code != 200:
            return f"❌ 네이버 API 호출 실패 ({response.status_code}): {response.text}"
            
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            return f"💬 '{keyword}' 관련 최신 뉴스가 검색되지 않았습니다."
            
        raw_news_data = ""
        for i, item in enumerate(items[:display_count]):
            clean_title = re.sub(r'<[^>]+>', '', html.unescape(item.get("title", ""))).strip()
            clean_desc = re.sub(r'<[^>]+>', '', html.unescape(item.get("description", ""))).strip()
            raw_news_data += f"[기사 {i+1}]\n제목: {clean_title}\n요약: {clean_desc}\n\n"
            
        return raw_news_data.strip()
        
    except Exception as e:
        return f"뉴스 데이터 수집 중 오류 발생: {e}"

# ---------------------------------------------------------
# 2. Gemini AI 미디어 총평 및 에디터 코멘트 생성 함수
# ---------------------------------------------------------
def generate_news_summary(raw_news_data):
    api_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else None
    if not api_key or "본인의_" in api_key:
        return "⚠️ GEMINI_API_KEY가 등록되지 않았습니다."
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        당신은 두산 베어스 전문 스포츠 뉴스레터 에디터입니다.
        아래 제공된 10개의 최신 두산 베어스 언론 기사들의 제목과 요약을 종합적으로 분석하여,
        팬들이 가장 주목해야 할 핵심 이슈를 요약하고 에디터 코멘트를 작성해 주세요.

        [수집된 최신 기사 10개 데이터]
        {raw_news_data}

        [작성 지침]
        1. 총평 요약은 10개 기사 중 중복되거나 가장 비중이 큰 핵심 주제 3가지를 선정해 작성하세요.
        2. 각 항목 앞에는 반드시 명확한 핵심 키워드를 볼드체(**키워드:**)로 시작하세요.
        3. 단순 사실 나열이 아닌, 미디어와 전문가 시각의 맥락(원인, 전망, 팀 영향)을 명료하게 서술하세요.
        4. 에디터 코멘트는 두산 팬덤의 감정을 대변하는 재치 있고 뚝심 있는 어투로 작성하세요.

        [출력 양식] (반드시 아래 형태를 유지할 것)
        🎙️ [미디어 & 전문가 총평 요약]
        • **(첫 번째 핵심 주제 키워드):** (해당 이슈에 대한 미디어 시각 및 구체적 내용 요약)
        • **(두 번째 핵심 주제 키워드):** (선수 활약, 투타 전력, 코칭스태프 관련 내용 요약)
        • **(세 번째 핵심 주제 키워드):** (향후 일정, 팀 분위기, 순위 싸움 또는 드래프트 등 전망 요약)

        🔥 [에디터의 찐텐 코멘트]
        • (두산 팬들의 가슴을 뛰게 하거나 공감할 수 있는 도파민 가득한 코멘트 1줄 🐻)
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        return response.text.strip()
        
    except Exception as e:
        return f"요약 생성 오류: {e}"

# ---------------------------------------------------------
# 3. 메인 실행 블록
# ---------------------------------------------------------
def get_doosan_news_report():
    news_data = fetch_naver_news_api(keyword="두산베어스", display_count=10)
    
    if news_data.startswith("⚠️") or news_data.startswith("❌") or news_data.startswith("💬"):
        return news_data
        
    return generate_news_summary(news_data)

if __name__ == "__main__":
    print("⏳ '두산베어스' 최신 기사 10개를 수집하고 요약을 생성하는 중입니다...\n")
    report = get_doosan_news_report()
    print(report)
