def generate_final_newsletter():
    try:
        # 🔥 리눅스 서버에서 튕기는 것을 막기 위해 모든 설정을 try 문 안으로 이동
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu') # 👈 깃허브 서버용 필수 옵션 추가됨
        options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        KST = timezone(timedelta(hours=9))
        now_kst = datetime.now(KST)
        yesterday = now_kst - timedelta(days=1)
        # ... (이하 동일하게 원래 코드 유지) ...
        # (중간 코드 생략)
        
        editor_comment = get_gemini_insights(team1, team2, score, news_reviews)

        report = (
            f"📰 [어제의 두산 베어스 경기 리뷰]\n"
            f"📅 날짜: {yesterday.month}월 {yesterday.day}일 {yesterday_weekday}\n"
            f"⚾ 매치업: {team1} VS {team2}\n"
            f"📊 경기 결과: {team1} {score} {team2}\n"
            f"🎯 승/패 투수: {pitcher_info}\n\n"
            f"----------------------------------------\n"
            f"{editor_comment}\n"
            f"----------------------------------------\n\n"
            f"👉 상세 매치 리뷰 보기: {game_link}"
        )
        return report
        
    except Exception as e:
        # 가상 브라우저가 안 켜지는 에러가 나더라도 여기서 텍스트로 부드럽게 반환
        return f"데이터 크롤링 중 오류가 발생했습니다: {e}"
    finally:
        if 'driver' in locals():
            driver.quit()
