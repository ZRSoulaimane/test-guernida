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


def crawl_linkedin_posts():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--kiosk')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get('https://www.linkedin.com/login/fr?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')
    driver.execute_script("window.scrollBy(0,300)","")

    connexion = dotenv_values("connexion.env")
    time.sleep(10)
    email = connexion["EMAIL"]
    username = driver.find_element(By.XPATH, '//*[@id="username"]')
    username.send_keys(email)
    time.sleep(10)
    conn_password = connexion["PASSWORD"]
    password = driver.find_element(By.XPATH, '//*[@id="password"]')
    password.send_keys(conn_password)

    logging.info('info insered')

    time.sleep(15)
    login_button = driver.find_element(By.XPATH, '//*[@id="organic-div"]/form/div[3]/button')
    login_button.click()
    logging.info('login done')
        
    driver.execute_script("window.scrollBy(0,300)","")
    time.sleep(15)

    analytics = driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/div/div[2]/div/div/div/section/footer/a')

    analytics.click()

    time.sleep(15)
    page_posts = driver.find_element(By.XPATH, '/html/body/div[5]/div[3]/div/div/section/div/div[1]/div[2]/nav/ul/li[1]/a')
    page_posts.click()

    connection = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',
            password='salma',
            database='guernida'
        )
    
    cursor_obj = connection.cursor()

    logging.info('Connextion established to the database')

    # keep track of found elements
    found_elements = set() 

    posts = []
 
    initialScroll=0
    finalScroll=900
    i=0

    # scroll the page and find new elements
    while True:
        # get current number of found elements
        num_found = len(found_elements)
        # keep scrolling till we get all the new elements
        driver.execute_script(f"window.scrollTo({initialScroll},{finalScroll})")
        # wait for new content to load
        time.sleep(10)
        # find new elements on the page
        containers = driver.find_elements(By.CLASS_NAME, "artdeco-card.mb2")
        # loop through new elements and click on buttons to load more information
        for container in containers:
            if container not in found_elements:
                found_elements.add(container)
                i = i+1
                logging.info('iteration %s of the posts loop', i)

                ##extracting date
                date_box = container.find_element(By.CSS_SELECTOR,'div.org-update-posted-by-selector')
                date = date_box.find_element(By.CSS_SELECTOR,'span.org-update-posted-by-selector__date').text.split()
                date_converted = datetime.strptime(date[0], '%m/%d/%Y').date().strftime("%Y-%m-%d")

                #extracting text
                text_box = container.find_element(By.CSS_SELECTOR,'div.update-components-text.relative.feed-shared-update-v2__commentary')
                texte = text_box.find_element(By.CSS_SELECTOR, 'span[dir="ltr"]')
                texte_content = texte.get_attribute('textContent')
                hashtags = [hash for hash in texte_content.split(" ") if "#" in hash]
                keywords = ' '.join(hashtags)
                
                cursor_obj.execute("INSERT INTO posts (date_pub, contenu, keywords) VALUES (%s, %s, %s) ON CONFLICT (contenu) DO NOTHING", (date_converted,texte_content,keywords,))
                connection.commit()
                logging.info("post insered")

                cursor_obj.execute("SELECT post_id FROM posts WHERE contenu = %s", (texte_content,))
                post_id = cursor_obj.fetchall()
                
                #extracting stats
                #clicking on the button
                stats_button = container.find_element(By.CSS_SELECTOR,'button.org-update-analytics__toggle-details-btn.t-14.t-black--light.t-bold')
                stats_button.click()
                
                #loop sur les stats
                stats = container.find_elements(By.CSS_SELECTOR, 'li.org-update-analytics-engagement__item')  

                stats_dict = extract_stats_values(stats)
                
                cursor_obj.execute("INSERT INTO impressions (post_id, impressions, click_rate, nb_comments, nb_reposts, nb_click, engagement_rate) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (post_id) DO UPDATE SET impressions = EXCLUDED.impressions, click_rate = EXCLUDED.click_rate, nb_comments = EXCLUDED.nb_comments,nb_reposts = EXCLUDED.nb_reposts, nb_click = EXCLUDED.nb_click, engagement_rate = EXCLUDED.engagement_rate", (post_id[0],stats_dict['impression'],stats_dict['click_rate'],stats_dict['comment'],stats_dict['repost'],stats_dict['click'],stats_dict['engagement']))
                connection.commit()
                logging.info('stats insered')
                
                #extracting reactions
                wait = WebDriverWait(driver, 10)

                try:
                    react_button = container.find_element(By.CLASS_NAME, 'social-details-social-counts__reactions-count')
                except:
                    react_button = container.find_element(By.CLASS_NAME, 'social-details-social-counts__social-proof-container')
                react_button.click()

                reactions_page = driver.page_source   
                linkedin_soup = bs(reactions_page.encode("utf-8"), "html")
                linkedin_soup.prettify()

                try:
                    #if there are many types of reactions 
                    nb_react_container = linkedin_soup.find("div", {"class":"social-details-reactors-tab__icon-container social-details-reactors-tab__reaction-tab"})
                    total_react = nb_react_container.findAll("span")[1].string.strip()
                    reactions = linkedin_soup.findAll("button",{"class":"ml0 p3 artdeco-tab ember-view"})
                except:
                    # if there is just one type
                    nb_react_container = linkedin_soup.find("div", {"class":"social-details-reactors-tab__icon-container"})
                    total_react = nb_react_container.findAll("span")[1].string.strip()
                    reactions = linkedin_soup.findAll("button",{"class":"ml0 p3 artdeco-tab active artdeco-tab--selected ember-view"})                    
                
                reactions_dict = extract_reaction_values(reactions)
                    
                cursor_obj.execute("INSERT INTO reactions(post_id, nb_like, nb_love, nb_support, nb_celebrate, nb_insightful, nb_funny, total) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (post_id) DO UPDATE SET nb_like = EXCLUDED.nb_like, nb_love = EXCLUDED.nb_love, nb_support= EXCLUDED.nb_support, nb_celebrate=EXCLUDED.nb_celebrate, nb_insightful = EXCLUDED.nb_insightful, nb_funny = EXCLUDED.nb_funny, total = EXCLUDED.total " , (post_id[0], reactions_dict['nb_like'], reactions_dict['nb_love'], reactions_dict['nb_support'], reactions_dict['nb_celebrate'], reactions_dict['nb_insightful'], reactions_dict['nb_funny'], int(total_react) ))
                connection.commit()
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
    
            initialScroll = finalScroll
            finalScroll += 900
        # check if we've found all elements
        if len(found_elements) == num_found:
            break
    
    cursor_obj.close()
    connection.close()
    driver.quit()

    return posts

crawled_posts = crawl_linkedin_posts()
print(crawled_posts)
