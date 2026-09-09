import os
import time
import asyncio
import threading
from datetime import datetime
import pytz
from flask import Flask
from waitress import serve
from playwright.async_api import async_playwright
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ==============================================================================
# CHANGE YOUR DETAILS HERE
# ==============================================================================
STUDENT_NAME = "Labib 7182"  # PUT YOUR INDEX NUMBER & NAME HERE

SCHEDULES = [
    {
        "topic": "Morning Class",
        "days": "sat,mon,wed",
        "time": "07:30",
        "meeting_id": "7114732370",       # PUT YOUR MORNING MEETING ID HERE
        "passcode": "white",         # PUT YOUR MORNING PASSCODE HERE
        "duration_minutes": 60             # STAY TIME IN MINUTES
    }
    
]
# ==============================================================================

# 1. Production Web Server Setup (For Render Health Checks)
app = Flask(__name__)

@app.route("/")
def home():
    return "Zoom Attendance Bot is running 24/7!"

def start_web_server():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host="0.0.0.0", port=port)


# 2. Zoom Joiner Logic via Playwright
async def join_zoom_meeting(meeting_id, passcode, student_name, duration_min, topic):
    print(f"\n[{datetime.now()}] Joining: {topic}")
    clean_id = str(meeting_id).replace(" ", "").replace("-", "")
    zoom_web_url = f"https://zoom.us/wc/{clean_id}/join?pwd={passcode}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--use-fake-ui-for-media-stream", "--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(permissions=["microphone", "camera"])
        page = await context.new_page()

        try:
            await page.goto(zoom_web_url, wait_until="networkidle", timeout=60000)
            name_input = page.locator("input[id='input-for-name']")
            await name_input.wait_for(state="visible", timeout=30000)
            await name_input.fill(student_name)
            
            join_button = page.locator("button.preview-join-button")
            await join_button.click()
            print(f"Successfully joined '{topic}' as '{student_name}'!")
            
            await asyncio.sleep(duration_min * 60)
            print(f"Finished duration ({duration_min} mins). Leaving: {topic}")

        except Exception as e:
            print(f"Error joining meeting: {str(e)}")
        finally:
            await browser.close()


# 3. APScheduler Task Automation Setup
def start_scheduler():
    dhaka_tz = pytz.timezone("Asia/Dhaka")
    scheduler = AsyncIOScheduler(timezone=dhaka_tz)
    
    for s in SCHEDULES:
        hour, minute = s["time"].split(":")
        scheduler.add_job(
            join_zoom_meeting,
            trigger="cron",
            day_of_week=s["days"],
            hour=int(hour),
            minute=int(minute),
            args=[s["meeting_id"], s["passcode"], STUDENT_NAME, s["duration_minutes"], s["topic"]]
        )
        print(f"Scheduled: {s['topic']} ({s['days']}) at {s['time']} (Asia/Dhaka)")
    scheduler.start()


# 4. Main Entrypoint
async def main():
    # Run the Waitress web server in a background thread
    threading.Thread(target=start_web_server, daemon=True).start()
    
    print("Bot is starting...")
    start_scheduler()
    
    # Keep the event loop running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
