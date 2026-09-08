from datetime import datetime, timedelta, timezone
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

def get_doosan_entry_status():
    url = "https://www.koreabaseball.com/Player/Register.aspx"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    try:
        # 무조건 한국 표준시(KST) 기준 오늘 날짜만 사용
        KST = timezone(timedelta(hours=9))
        now_kst = datetime.now(KST)
        today_full = now_kst.strftime("%Y.%m.%d")
        today_short = now_kst.strftime("%m.%d")

        driver.get(url)
        wait = WebDriverWait(driver, 15)
        
        # 페이지 초기 데이터 컨테이너가 로드될 때까지 대기
        old_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$='udpRecord']")))

        # === 💡 핵심 해결책 ===
        # Strict mode 에러를 일으키는 __doPostBack()을 호출하지 않고, 
        # 직접 '날짜'와 '두산 구단' 값을 세팅한 후 폼(Form)을 제출하여 페이지를 안전하게 갱신합니다.
        bypass_js = f"""
            // 1. 날짜를 '오늘 날짜'로 세팅
            var dateInput = document.querySelector("input[id$='txtGameDate']");
            if(dateInput) dateInput.value = '{today_full}';

            // 2. 팀 선택 드롭다운에서 '두산' 선택
            var select = document.querySelector("select[id$='ddlTeam']");
            if(select) {{
                for(var i=0; i<select.options.length; i++) {{
                    if(select.options[i].text === '두산') {{
                        select.selectedIndex = i;
                        break;
                    }}
                }}
            }}

            // 3. 에러 우회를 위한 강제 Form Submit 조작
            var form = document.forms[0];
            
            // ASP.NET이 요구하는 Event Target을 직접 생성해 팀 변경 이벤트를 모방
            var target = document.getElementById('__EVENTTARGET');
            if(!target) {{
                target = document.createElement('input');
                target.type = 'hidden';
                target.name = '__EVENTTARGET';
                target.id = '__EVENTTARGET';
                form.appendChild(target);
            }}
            target.value = select ? select.name : '';

            var arg = document.getElementById('__EVENTARGUMENT');
            if(!arg) {{
                arg = document.createElement('input');
                arg.type = 'hidden';
                arg.name = '__EVENTARGUMENT';
                arg.id = '__EVENTARGUMENT';
                form.appendChild(arg);
            }}
            arg.value = '';

            // 폼 제출 진행 (안전하게 화면 새로고침)
            form.submit();
        """
        
        driver.execute_script(bypass_js)

        # 4. 이전 화면이 완전히 사라질 때까지 대기 (갱신 100% 보장)
        wait.until(EC.staleness_of(old_container))

        # 5. 두산 데이터로 필터링된 새로운 컨테이너가 뜰 때까지 대기
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[id$='udpRecord']")))
        time.sleep(2) # 돔(DOM) 렌더링 안정화를 위한 짧은 대기

        # 파싱 시작
        soup = BeautifulSoup(driver.page_source, "html.parser")

        registered = []
        expunged = []

        container = soup.select_one("div[id$='udpRecord']")
        if container:
            div_blocks = container.select("div.row.mt35")
            doosan_div = None
            
            for div in div_blocks:
                h4 = div.find("h4", class_="bul_history")
                # '두산' 키워드가 있는 블록만 추출
                if h4 and "두산" in h4.text:
                    doosan_div = div
                    break

            if doosan_div:
                h5_tags = doosan_div.find_all("h5", class_="bul_sub")
                for h5 in h5_tags:
                    section_title = h5.text.strip()
                    table = h5.find_next("table", class_="tNData")
                    if not table:
                        continue

                    rows = table.select("tbody tr")
                    for row in rows:
                        tds = row.find_all("td")
                        if len(tds) >= 2:
                            player_name = tds[1].text.strip()
                            if section_title == "등록":
                                if player_name and player_name not in registered:
                                    registered.append(player_name)
                            elif section_title == "말소":
                                if player_name and player_name not in expunged:
                                    expunged.append(player_name)

        # 결과 리포트 작성
        report = "📋 [오늘의 엔트리 및 선수단 체크]\n"
        if not registered and not expunged:
            report += f"오늘({today_short})은 1군 콜업 및 말소 내역이 없습니다. 🐻"
        else:
            report += f"📅 기준일: {today_short}\n"
            if registered:
                report += f"🔼 [등록] {', '.join(registered)}\n"
            if expunged:
                report += f"🔽 [말소] {', '.join(expunged)}"

        return report.strip()

    except Exception as e:
        return f"엔트리 정보 크롤링 중 오류가 발생했습니다: {e}"
    finally:
        driver.quit()


if __name__ == "__main__":
    print(get_doosan_entry_status())