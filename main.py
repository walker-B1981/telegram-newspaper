import os
import sys
import logging
import requests
import feedparser

# 로깅 설정 (GitHub Actions 실행 로그 확인용)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# 기본 수집 대상 RSS 피드 URL (원하는 IT 뉴스 RSS 피드로 변경 가능)
RSS_FEED_URL = "https://news.ycombinator.com/rss"  # 예: Hacker News RSS

def get_latest_news(limit=5):
    """RSS 피드에서 최신 IT 뉴스 헤드라인과 링크를 수집합니다."""
    try:
        logging.info(f"RSS 피드 수집 시작: {RSS_FEED_URL}")
        feed = feedparser.parse(RSS_FEED_URL)
        
        entries = feed.entries[:limit]
        if not entries:
            logging.warning("수집된 뉴스 항목이 없습니다.")
            return []
            
        news_items = []
        for entry in entries:
            title = entry.get("title", "제목 없음").strip()
            link = entry.get("link", "#").strip()
            # HTML 태그 형식을 적용하여 텔레그램 링크 하이퍼링크 생성
            news_items.append(f"• <a href=\"{link}\">{title}</a>")
            
        return news_items
    except Exception as e:
        logging.error(f"RSS 뉴스 수집 중 오류 발생: {e}")
        return []

def send_telegram_message(bot_token, chat_id, text):
    """텔레그램 Bot API를 호출하여 메시지를 보냅니다."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()  # HTTP 상태 코드가 200이 아닌 경우 예외 발생
        
        result = response.json()
        if result.get("ok"):
            logging.info("텔레그램 메시지 전송 완료")
            return True
        else:
            logging.error(f"텔레그램 API 오류 응답: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"텔레그램 네트워크 통신 실패: {e}")
        return False

def main():
    # 1. 환경변수에서 텔레그램 API 토큰 및 Chat ID 로드
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logging.error("필수 환경변수(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)가 설정되지 않았습니다.")
        sys.exit(1)
        
    # 2. 뉴스 수집
    news_items = get_latest_news(limit=5)
    if not news_items:
        logging.error("전송할 뉴스 데이터가 없어 프로그램을 종료합니다.")
        sys.exit(1)
        
    # 3. 메시지 본문 구성
    message_header = "<b>📢 오늘의 IT 뉴스 브리핑</b>\n\n"
    message_body = "\n\n".join(news_items)
    full_message = message_header + message_body
    
    # 4. 텔레그램 전송
    success = send_telegram_message(bot_token, chat_id, full_message)
    if not success:
        logging.error("메시지 전송에 실패했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()
