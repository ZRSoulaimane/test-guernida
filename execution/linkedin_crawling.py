from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import time 
import psycopg2
import regex as re 
from dotenv import dotenv_values
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging
from selenium.webdriver.common.keys import Keys



# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Save logs to a file
        logging.StreamHandler()  # Print logs to console
    ]
)

def extract_reaction_values(reactions):
    """
    Extracts the values of different reactions from a list of reaction elements.
    
    Args:
        reactions (list): List of reaction elements.
    
    Returns:
        dict: Dictionary containing the counts of different reactions.
    """
    reaction_dict = {
        'nb_like': 0,
        'nb_love': 0,
        'nb_support': 0,
        'nb_celebrate': 0,
        'nb_insightful': 0,
        'nb_funny': 0
    }

    for reaction in reactions:
        span_tags = reaction.findAll("span")
        nb_react = int(span_tags[1].text.strip())
        img_react = span_tags[0].find("img")
        react_name = img_react["alt"]

        if react_name == 'like':
            reaction_dict['nb_like'] = nb_react
        elif react_name == 'love':
            reaction_dict['nb_love'] = nb_react
        elif react_name == 'support':
            reaction_dict['nb_support'] = nb_react
        elif react_name == 'celebrate':
            reaction_dict['nb_celebrate'] = nb_react
        elif react_name == 'insightful':
            reaction_dict['nb_insightful'] = nb_react
        elif react_name == 'funny':
            reaction_dict['nb_funny'] = nb_react

    return reaction_dict

def extract_stats_values(stats):
    """
    Extracts the values of different stats from a list of stat elements.
    
    Args:
        stats (list): List of stat elements.
    
    Returns:
        dict: Dictionary containing the values of different stats.
    """
    stats_dict = {
        'impression': 0,
        'click_rate': 0,
        'comment': 0,
        'repost': 0,
        'click': 0,
        'engagement': 0,
        'stat_title': '',
        'value': ''
    }

    for stat in stats:
        stat_title = stat.find_element(By.TAG_NAME, 'dd').text.strip()
        value = stat.find_element(By.TAG_NAME, 'dt').text.strip()

        if stat_title == 'Impressions':
            stats_dict['impression'] = float(re.sub(r',', '', value))
        elif stat_title == 'Reactions':
            pass
        elif stat_title == 'Click-through rate':
            stats_dict['click_rate'] = float(re.sub(r'%', '', value))
        elif stat_title == 'Comments':
            stats_dict['comment'] = int(re.sub(r',', '', value))
        elif stat_title == 'Reposts' or stat_title == 'Repost':
            stats_dict['repost'] = int(re.sub(r',', '', value))
        elif stat_title == 'Clicks':
            stats_dict['click'] = int(re.sub(r',', '', value))
        elif stat_title == 'Engagement rate':
            stats_dict['engagement'] = float(re.sub(r'%', '', value))

    return stats_dict

def get_chromedriver():
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-agent=%s' % user_agent)
    chrome_options.add_argument(f'--proxy-server=zproxy.lum-superproxy.io:9222')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    # chrome_options.add_argument('--headless')

    return webdriver.Chrome(options=chrome_options)


def crawl_linkedin_posts():
    driver = get_chromedriver()
    driver.get('https://www.linkedin.com/login')
    driver.execute_script("window.scrollBy(0,300)","")

    connexion = dotenv_values("connexion.env")
    time.sleep(3)
    email = connexion["EMAIL"]

    elem = driver.find_element(By.XPATH, '//*[@id="username"]')
    elem.send_keys(email)
    logging.info('insert email info')
    conn_password = connexion["PASSWORD"]
    elem = driver.find_element(By.XPATH, '//*[@id="password"]')
    elem.send_keys(conn_password)
    logging.info('insert password info')
    elem.send_keys(Keys.RETURN)
    logging.info('accessing to the home page')

    time.sleep(7)
    if "/checkpoint/challenge" in driver.current_url:
        logging.info("you need to solve the puzzle")
        return

    logging.info('login done')
    time.sleep(4)

    driver.get('https://www.linkedin.com/company/14051854/admin/')

    # connection = psycopg2.connect(
    #         host='host.docker.internal',
    #         port='5432',
    #         user='postgres',
    #         password='salma',
    #         database='guernida'
    #     )
    
    # cursor_obj = connection.cursor()

    logging.info('Connextion established to the database')

    # keep track of found elements
    found_elements = set() 

    posts = []
 
    initialScroll=0
    finalScroll=900
    i=0

    # scroll the page and find new elements
    while True:
        logging.info("Scrolling the page...")
        # get current number of found elements
        num_found = len(found_elements)
        # keep scrolling till we get all the new elements
        driver.execute_script(f"window.scrollTo({initialScroll},{finalScroll})")
        logging.info("Waiting for new content to load...")
        # wait for new content to load
        time.sleep(10)
        # find new elements on the page
        containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'artdeco-card') and contains(@class, 'mb2')]")
        logging.info("Found %s new elements", len(containers))
        for container in containers:
            if container not in found_elements:
                found_elements.add(container)
                logging.info("Container added to found_elements")

                i = i + 1
                logging.info('Iteration %s of the posts loop', i)

                ##extracting date
                date_box = container.find_element(By.CSS_SELECTOR,'div.org-update-posted-by-selector')
                logging.info("Date box element found")

                date = date_box.find_element(By.CSS_SELECTOR,'span.org-update-posted-by-selector__date').text.split()
                logging.info("Date extracted: %s", date)

                date_converted = datetime.strptime(date[0], '%m/%d/%Y').date().strftime("%Y-%m-%d")
                logging.info("Date converted: %s", date_converted)

                #extracting text
                text_box = container.find_element(By.CSS_SELECTOR,'div.update-components-text.relative.feed-shared-update-v2__commentary')
                logging.info("Text box element found")

                texte = text_box.find_element(By.CSS_SELECTOR, 'span[dir="ltr"]')
                logging.info("Text element found")

                texte_content = texte.get_attribute('textContent')
                logging.info("Text extracted: %s", texte_content)

                hashtags = [hash for hash in texte_content.split(" ") if "#" in hash]
                keywords = ' '.join(hashtags)
                logging.info("Keywords extracted: %s", keywords)

                # cursor_obj.execute("INSERT INTO posts (date_pub, contenu, keywords) VALUES (%s, %s, %s) ON CONFLICT (contenu) DO NOTHING", (date_converted,texte_content,keywords,))
                # connection.commit()
                logging.info("Post inserted")


                # cursor_obj.execute("SELECT post_id FROM posts WHERE contenu = %s", (texte_content,))
                # post_id = cursor_obj.fetchall()
                
                #extracting stats
                #clicking on the button
                stats_button = container.find_element(By.CSS_SELECTOR, 'button.org-update-analytics__toggle-details-btn.t-14.t-black--light.t-bold')
                stats_button.click()
                logging.info("Clicked on stats_button")

                # loop sur les stats
                stats = container.find_elements(By.CSS_SELECTOR, 'li.org-update-analytics-engagement__item')
                logging.info("Stats elements found")

                stats_dict = extract_stats_values(stats)
                logging.info("Stats values extracted: %s", stats_dict)

                # cursor_obj.execute("INSERT INTO impressions (post_id, impressions, click_rate, nb_comments, nb_reposts, nb_click, engagement_rate) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (post_id) DO UPDATE SET impressions = EXCLUDED.impressions, click_rate = EXCLUDED.click_rate, nb_comments = EXCLUDED.nb_comments,nb_reposts = EXCLUDED.nb_reposts, nb_click = EXCLUDED.nb_click, engagement_rate = EXCLUDED.engagement_rate", (post_id[0],stats_dict['impression'],stats_dict['click_rate'],stats_dict['comment'],stats_dict['repost'],stats_dict['click'],stats_dict['engagement']))
                # connection.commit()
                logging.info("Stats inserted")

                # extracting reactions
                wait = WebDriverWait(driver, 10)

                try:
                    react_button = container.find_element(By.CLASS_NAME, 'social-details-social-counts__reactions-count')
                except:
                    react_button = container.find_element(By.CLASS_NAME, 'social-details-social-counts__social-proof-container')
                react_button.click()
                logging.info("Clicked on react_button")

                reactions_page = driver.page_source
                linkedin_soup = bs(reactions_page.encode("utf-8"), "html")
                linkedin_soup.prettify()

                try:
                    # if there are many types of reactions
                    nb_react_container = linkedin_soup.find("div", {"class": "social-details-reactors-tab__icon-container social-details-reactors-tab__reaction-tab"})
                    total_react = nb_react_container.findAll("span")[1].string.strip()
                    reactions = linkedin_soup.findAll("button", {"class": "ml0 p3 artdeco-tab ember-view"})
                except:
                    # if there is just one type
                    nb_react_container = linkedin_soup.find("div", {"class": "social-details-reactors-tab__icon-container"})
                    total_react = nb_react_container.findAll("span")[1].string.strip()
                    reactions = linkedin_soup.findAll("button", {"class": "ml0 p3 artdeco-tab active artdeco-tab--selected ember-view"})

                reactions_dict = extract_reaction_values(reactions)
                logging.info("Reactions values extracted: %s", reactions_dict)
                # cursor_obj.execute("INSERT INTO reactions(post_id, nb_like, nb_love, nb_support, nb_celebrate, nb_insightful, nb_funny, total) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (post_id) DO UPDATE SET nb_like = EXCLUDED.nb_like, nb_love = EXCLUDED.nb_love, nb_support= EXCLUDED.nb_support, nb_celebrate=EXCLUDED.nb_celebrate, nb_insightful = EXCLUDED.nb_insightful, nb_funny = EXCLUDED.nb_funny, total = EXCLUDED.total " , (post_id[0], reactions_dict['nb_like'], reactions_dict['nb_love'], reactions_dict['nb_support'], reactions_dict['nb_celebrate'], reactions_dict['nb_insightful'], reactions_dict['nb_funny'], int(total_react) ))
                # connection.commit()
                logging.info("reaction insered")    
                    
                post = { 
                    "content" : texte_content ,
                    "keywords" : keywords,
                    "date" : date_converted ,
                    "reactions": {
                        "total": total_react,
                        "like" : reactions_dict['nb_like'],
                        "love" : reactions_dict['nb_love'], 
                        "support" : reactions_dict['nb_support'],
                        "celebrate" : reactions_dict['nb_celebrate'],
                        "insightful" : reactions_dict['nb_insightful'],
                        "funny" : reactions_dict['nb_funny']
                    },
                    "stats" : {
                    "impressions": stats_dict['impression'],
                    "Click_rate" : stats_dict['click_rate'],
                    "Comments" : stats_dict['comment'],
                    "Reposts" : stats_dict['repost'], 
                    "Click" : stats_dict['click'],
                    "Engagement_rate" : stats_dict['engagement']  
                    }
                }
                
                posts.append(post)
                
                close_button = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'button.artdeco-modal__dismiss.artdeco-button.artdeco-button--circle.artdeco-button--muted.artdeco-button--2.artdeco-button--tertiary.ember-view')))
                close_button.click()

                logging.info("Clicked on close_button")

            initialScroll = finalScroll
            finalScroll += 900
            logging.info("Updated initialScroll: %s, finalScroll: %s", initialScroll, finalScroll)

        # check if we've found all elements
        if len(found_elements) == num_found:
            break
        logging.info("Checking if all elements are found")
    
    # cursor_obj.close()
    # connection.close()
    driver.quit()
    logging.info("Closed cursor_obj, connection, and driver")

    return posts


if __name__ == "__main__":
    crawled_posts = crawl_linkedin_posts()
    print(crawled_posts)
