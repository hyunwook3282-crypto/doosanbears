from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from urllib.parse import quote
import requests
import re
import time

def get_news_commentary(month, day, opponent_team):
    search_keyword = f"{month}월 {day}일 두산베어스 {opponent_team}"
    encoded_keyword = quote(search_keyword)
    url = f"https://search.naver.com/search.naver?where=news&query={encoded_keyword}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.select('.news_area')
        
        if not news_items:
            return "💬 현재 매치에 대한 주요 언론 리뷰가 집계되지 않았습니다."
            
        commentary = ""
        for i, item in enumerate(news_items[:2]):
            title_element = item.select_one('.news_tit')
            title = title_element.text.strip() if title_element else "제목 없음"
            
            desc_element = item.select_one('.api_txt_lines.dsc_txt_wrap')
            desc = desc_element.text.strip() if desc_element else "내용 요약 없음"
            short_desc = desc[:60] + "..." if len(desc) > 60 else desc
            
            commentary += f"📌 {title}\n📝 {short_desc}\n\n"
            
        return commentary.strip()
    except Exception as e:
        return f"뉴스 리뷰를 불러오는 중 오류 발생: {e}"

def generate_final_newsletter():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # 무조건 한국 표준시(KST)를 기준으로 어제 날짜 계산
        KST = timezone(timedelta(hours=9))
        now_kst = datetime.now(KST)
        yesterday = now_kst - timedelta(days=1)
        yesterday_str = yesterday.strftime("%m.%d")
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        yesterday_weekday = weekdays[yesterday.weekday()]
        
        driver.get("https://www.koreabaseball.com/Schedule/Schedule.aspx")
        wait = WebDriverWait(driver, 10)
        
        doosan_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '두산') or .//img[@alt='두산']] | //span[contains(text(), '두산')]"))
        )
        doosan_btn.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblScheduleList")))
        
        table = driver.find_element(By.CSS_SELECTOR, "#tblScheduleList")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        target_row = None
        current_date = ""
        
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if not tds: continue
                
            try:
                day_cell = row.find_element(By.CLASS_NAME, "day")
                if day_cell.text.strip(): current_date = day_cell.text.strip()
            except: pass
                
            if yesterday_str in current_date:
                try:
                    play_cell = row.find_element(By.CLASS_NAME, "play")
                    if '두산' in play_cell.text:
                        target_row = row
                        break
                except: continue
                    
        if not target_row:
            return f"========================================\n🐻 [미라클 두산 데일리 리포트]\n========================================\n\n📰 어제({yesterday.month}월 {yesterday.day}일 {yesterday_weekday})는 두산 베어스의 경기 일정이 없었거나 우천 취소되었습니다. 🐻\n"

        play_text = target_row.find_element(By.CLASS_NAME, "play").text
        team_mapping = {
            "두산": "두산베어스", "SSG": "SSG 랜더스", "LG": "LG 트윈스", 
            "KT": "KT 위즈", "NC": "NC 다이노스", "KIA": "KIA 타이거즈", 
            "롯데": "롯데 자이언츠", "삼성": "삼성 라이온즈", "한화": "한화 이글스", "키움": "키움 히어로즈"
        }
        pattern = re.compile(r'(두산|SSG|LG|KT|NC|KIA|롯데|삼성|한화|키움)')
        found_teams = pattern.findall(play_text)
        team1 = team_mapping.get(found_teams[0], "두산베어스") if len(found_teams) > 0 else "두산베어스"
        team2 = team_mapping.get(found_teams[1], "상대팀") if len(found_teams) > 1 else "상대팀"
        opponent = team2 if team1 == "두산베어스" else team1
        
        try:
            score_match = re.search(r'\d+\s*(vs|:)\s*\d+', play_text, re.IGNORECASE)
            if score_match:
                score = score_match.group(0).replace('vs', ':').replace('VS', ':')
            else:
                numbers = re.findall(r'\d+', play_text)
                score = f"{numbers[0]}:{numbers[1]}" if len(numbers) >= 2 else "결과 집계 중"
        except:
            score = "확인 불가"

        game_link = "상세 링크 업데이트 전"
        try:
            links = target_row.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and ("GameCenter" in href or "game" in href or "BoxScore" in href):
                    game_link = href
                    break
        except: pass

        pitcher_info = "상세 기록 업데이트 전"
        if "http" in game_link:
            driver.get(game_link)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".game-cont.on")))
                time.sleep(2)
                away_pitcher = driver.find_element(By.CSS_SELECTOR, ".game-cont.on .team.away .today-pitcher").text.replace('\n', ' ').strip()
                home_pitcher = driver.find_element(By.CSS_SELECTOR, ".game-cont.on .team.home .today-pitcher").text.replace('\n', ' ').strip()
                pitcher_info = f"{away_pitcher} / {home_pitcher}" if away_pitcher and home_pitcher else "투수 기록 집계 중"
            except Exception:
                pitcher_info = "투수 정보 크롤링 실패"

        news_reviews = get_news_commentary(yesterday.month, yesterday.day, opponent)
        editor_comment = "장단 18안타 맹폭격! 끝까지 포기하지 않는 '미라클 두산'의 뚝심이 가을야구 청신호를 완벽하게 켰습니다 🚦⚾"

        report = (
            f"========================================\n"
            f"🐻 [미라클 두산 데일리 리포트]\n"
            f"========================================\n"
            f"📅 [어제의 두산 베어스 경기 리뷰]\n"
            f"날짜: {yesterday.month}월 {yesterday.day}일 {yesterday_weekday}\n"
            f"⚾ 매치업: {team1} VS {team2}\n"
            f"📊 경기 결과: {team1} {score} {team2}\n"
            f"🎯 승/패 투수: {pitcher_info}\n\n"
            f"----------------------------------------\n"
            f"🎙️ [전문가 & 미디어 코멘트]\n"
            f"{news_reviews}\n"
            f"----------------------------------------\n"
            f"🔥 [에디터의 찐텐션 한 줄 평]\n"
            f"\"{editor_comment}\"\n\n"
            f"👉 상세 매치 리뷰 보기: {game_link}"
        )
        return report
        
    except Exception as e:
        return f"데이터 크롤링 중 오류가 발생했습니다: {e}"
    finally:
        driver.quit()

if __name__ == "__main__":
    print(generate_final_newsletter())
