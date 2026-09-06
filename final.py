import subprocess
import requests
import os

def create_and_send_newsletter():
    print("⏳ 데이터를 수집 중입니다...")

    try:
        yesterday_result = subprocess.run(["python3", "어제경기리뷰.py"], capture_output=True, text=True, check=True)
        yesterday_text = yesterday_result.stdout.strip()
    except Exception as e:
        yesterday_text = f"어제 경기 리뷰를 불러오지 못했습니다: {e}"

    try:
        schedule_result = subprocess.run(["python3", "경기일정.py"], capture_output=True, text=True, check=True)
        schedule_text = schedule_result.stdout.strip()
    except Exception as e:
        schedule_text = f"경기 일정을 불러오지 못했습니다: {e}"

    final_newsletter = (
        f"========================================\n"
        f"🐻 [미라클 두산 통합 데일리 리포트]\n"
        f"========================================\n\n"
        f"{yesterday_text}\n\n"
        f"----------------------------------------\n\n"
        f"🔜 [오늘의 경기 일정]\n"
        f"{schedule_text}\n\n"
        f"========================================"
    )
    
    # 깃허브에 숨겨둔 디스코드 웹훅 URL을 불러옴
    webhook_url = os.environ.get("DISCORD_WEBHOOK")
    
    if webhook_url:
        payload = {"content": final_newsletter}
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            print("🚀 디스코드 메시지 전송 성공!")
        else:
            print(f"❌ 디스코드 전송 실패: {response.status_code}")
    else:
        print(final_newsletter)
        print("⚠️ 디스코드 웹훅 URL이 설정되지 않아 텍스트만 출력합니다.")

if __name__ == "__main__":
    create_and_send_newsletter()