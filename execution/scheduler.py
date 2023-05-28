import schedule
import time
from linkedin_crawling import crawl_linkedin_posts

crawl_linkedin_posts()

schedule.every(1).days.do(crawl_linkedin_posts)

while 1:
    schedule.run_pending()
    print("Pending")
    time.sleep(1)