from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import re

def get_today_doosan_ment():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.koreabaseball.com/Schedule/Schedule.aspx")
        wait = WebDriverWait(driver, 10)
        
        doosan_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '두산') or .//img[@alt='두산']] | //span[contains(text(), '두산')]"))
        )
        doosan_btn.click()
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblScheduleList")))
        
        table = driver.find_element(By.CSS_SELECTOR, "#tblScheduleList")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        today = datetime.now()
        today_str = today.strftime("%m.%d")
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        today_weekday = weekdays[today.weekday()]
        
        current_date = ""
        team_mapping = {
            "두산": "두산베어스", "SSG": "SSG 랜더스", "LG": "LG 트윈스", 
            "KT": "KT 위즈", "NC": "NC 다이노스", "KIA": "KIA 타이거즈", 
            "롯데": "롯데 자이언츠", "삼성": "삼성 라이온즈", "한화": "한화 이글스", "키움": "키움 히어로즈"
        }
        
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if not tds:
                continue
                
            try:
                day_cell = row.find_element(By.CLASS_NAME, "day")
                if day_cell.text.strip():
                    current_date = day_cell.text.strip()
            except:
                pass
                
            if today_str in current_date:
                try:
                    play_cell = row.find_element(By.CLASS_NAME, "play")
                    play_text = play_cell.text
                    
                    if '두산' in play_text:
                        pattern = re.compile(r'(두산|SSG|LG|KT|NC|KIA|롯데|삼성|한화|키움)')
                        found_teams = pattern.findall(play_text)
                        
                        if len(found_teams) >= 2:
                            team1 = team_mapping.get(found_teams[0], "두산베어스")
                            team2 = team_mapping.get(found_teams[1], "상대팀")
                        else:
                            team1, team2 = "두산베어스", "상대팀"
                            
                        try:
                            time_cell = row.find_element(By.CLASS_NAME, "time")
                            match_time = time_cell.text.strip()
                        except:
                            match_time = "시간 미정"
                            
                        stadium = tds[-2].text.strip() if len(tds) >= 2 else "구장 미상"
                        stadium_details = {
                            "문학": "인천 문학", "잠실": "서울 잠실", "수원": "수원 KT위즈파크",
                            "창원": "창원 NC파크", "광주": "광주 기아챔피언스필드", "사직": "부산 사직",
                            "대구": "대구 삼성라이온즈파크", "대전": "대전 한화생명이글스파크", "고척": "서울 고척 스카이돔"
                        }
                        stadium = stadium_details.get(stadium, stadium)
                        
                        return (f"오늘은 {today.month}월 {today.day}일 {today_weekday}, "
                                f"오늘의 경기는 {team1} VS {team2}의 경기입니다! "
                                f"경기는 {stadium} 구장에서 {match_time}에 열리며, 오늘도 두산베어스의 승리를 응원합니다! 🐻⚾")
                except:
                    continue
                    
        return (f"오늘은 {today.month}월 {today.day}일 {today_weekday}입니다. "
                f"오늘은 두산 베어스의 경기 일정이 없습니다. 재충전의 하루 보내세요! 🐻")
        
    except Exception as e:
        return f"오류 발생: {e}"
    finally:
        driver.quit()

if __name__ == "__main__":
    print(get_today_doosan_ment())