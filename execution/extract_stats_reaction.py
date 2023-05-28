import logging
import re
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO)

def extract_reaction_values(reactions):
    """
    Extracts the values of different reactions from a list of reaction elements.

    Args:
        reactions (list): List of reaction elements.

    Returns:
        dict: Dictionary containing the counts of different reactions.
    """
    logging.info("Extracting reaction values...")
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

    logging.info("Reaction values extracted successfully.")
    return reaction_dict

def extract_stats_values(stats):
    """
    Extracts the values of different stats from a list of stat elements.

    Args:
        stats (list): List of stat elements.

    Returns:
        dict: Dictionary containing the values of different stats.
    """
    logging.info("Extracting stats values...")
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

    logging.info("Stats values extracted successfully.")
    return stats_dict
