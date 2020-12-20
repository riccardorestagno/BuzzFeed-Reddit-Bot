import re
import requests
from bs4 import BeautifulSoup
from langdetect import detect, lang_detect_exception

from helpers.enums import ArticleType
from helpers.reddit import connect_to_reddit


# If the list article title from a specific website contains any of the words below, the list will not be posted to Reddit.
# This avoids posting content which contains lists of ads and images.
TITLE_EXCLUSION_WORDS_ALL = ['pics', 'pictures', 'photos', 'gifs', 'images', 'deals', 'memes', 'tweets', 'must see']

TITLE_EXCLUSION_WORDS_BUZZFEED = ['amazon', 'twitter', 'instagram', 'tumblr', 'gifts', 'products']

TITLE_EXCLUSION_WORDS_MAPPING = {
    ArticleType.BuzzFeed: TITLE_EXCLUSION_WORDS_BUZZFEED
}


def soup_session(link):
    """BeautifulSoup session."""

    session = requests.Session()
    daily_archive = session.get(link)
    soup = BeautifulSoup(daily_archive.content, 'html.parser')
    return soup


def post_previously_made(subreddit, article_link):
    """
    Checks if the post has already been submitted.
    This is done by checking if the article link to be posted is within the article text of a previous post.
    Returns True if post was already submitted. Returns False otherwise.
    """

    reddit = connect_to_reddit()
    subreddit = reddit.subreddit(subreddit)
    submissions = subreddit.new(limit=25)
    for submission in submissions:
        if article_link in submission.selftext:
            return True

    return False


def get_title_exclusion_words(website):
    """Returns a list of words that should prevent the article from being posted if contained in the title."""

    if website in TITLE_EXCLUSION_WORDS_MAPPING:
        return TITLE_EXCLUSION_WORDS_ALL + TITLE_EXCLUSION_WORDS_MAPPING[website]
    else:
        return TITLE_EXCLUSION_WORDS_ALL


def get_article_list_count(article_title):
    """Returns number of points in the list article."""

    try:
        no_of_elements = [int(s) for s in article_title.split() if s.isdigit()][0]
    except (AttributeError, IndexError):
        return 0

    return no_of_elements


def article_title_meets_posting_requirements(website, article_title):
    """
    Validates that the article title meets all requirements to post the list to Reddit.

    The validations below check if:
        (1) The article contains a number
        (2) The article title doesn't contain certain pre-defined keywords
        (3) The article title is in english (BuzzFeed only)

    Returns True if all validations are met. Returns False otherwise.
    """

    if website == ArticleType.BuzzFeed:
        try:
            if not detect(article_title) == 'en':
                return False
        except lang_detect_exception.LangDetectException:
            return False

    no_of_elements = get_article_list_count(article_title)
    if no_of_elements == 0:
        return False

    article_title_lowercase = article_title.lower()
    if any(words in article_title_lowercase for words in get_title_exclusion_words(website)):
        return False

    return True


def article_text_meets_posting_requirements(website, article_list_text, list_counter, total_elements):
    """
    Validates that the article text meets all requirements to post the list to Reddit.

    The validations below check if:
        (1) The header count is equal to the list article count
        (2) The list is correctly formatted
        (3) The article resembles an ad based on specific regex validations or list element ends with ':' (BuzzFeed only)

    Returns True if all validations are met. Returns False otherwise.
    """

    if list_counter-1 != total_elements:
        return False

    if not is_correctly_formatted_list(article_list_text, list_counter):
        return False

    if website == ArticleType.BuzzFeed:
        percentage_threshold = 0.50  # Max percentage of regex validated ad-like list items where the post will not be made.
        if (len(re.findall('(.amazon.)', article_list_text)) / total_elements) >= percentage_threshold:
            return False
        if (len(re.findall('(\[A(n)? |\[(Up to )?[0-9]{2}% |\[This )', article_list_text)) / total_elements) >= percentage_threshold:
            return False
        if (len(re.findall('(\. This |\. When )', article_list_text)) / total_elements) >= percentage_threshold:
            return False

        # Articles where list items end with a colon will not be posted (most likely referencing an image below).
        if ':\n' in article_list_text:
            return False

    return True


def reverse_list(full_list_text):
    """Returns a numerically ordered list if the list was in reverse order in the article."""

    full_list = full_list_text.split('\n')
    full_list.reverse()
    full_list = list(filter(None, full_list))  # Filters out empty list elements.

    return '\n'.join(full_list) + '\n'


def is_correctly_formatted_list(full_text, list_count):
    """Checks if the final concatenated list is correctly formatted."""

    list_prefix_numbers = []

    for number in range(1, list_count):
        list_prefix_numbers.append(str(number) + '.')

    return all(element_prefix in full_text for element_prefix in list_prefix_numbers)
