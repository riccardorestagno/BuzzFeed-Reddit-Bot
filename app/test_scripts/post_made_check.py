from bs4 import BeautifulSoup
import requests
import praw
from os import environ
from dotenv import load_dotenv
load_dotenv()


def reddit_bot(headline, main_text, link):
    """Module that takes the title, main text and link to article and posts directly to reddit"""

    reddit = praw.Reddit(client_id=environ["BUZZFEEDBOT_CLIENT_ID"],
                         client_secret=environ["BUZZFEEDBOT_CLIENT_SECRET"],
                         user_agent=environ["BUZZFEEDBOT_USER_AGENT"],
                         username=environ["BUZZFEEDBOT_USERNAME"],
                         password=environ["BUZZFEEDBOT_PASSWORD"])

    reddit.subreddit('buzzfeedbot').submit(title=headline, selftext=main_text+'\n' + '[Link to article](' + link + ')')


def post_made_check(post_title, subpoints):
    """Checks if the post has already been submitted.
Returns True if post was submitted already and returns False otherwise"""

    post_made = False
    reddit = praw.Reddit(client_id=environ["BUZZFEEDBOT_CLIENT_ID"],
                         client_secret=environ["BUZZFEEDBOT_CLIENT_SECRET"],
                         user_agent=environ["BUZZFEEDBOT_USER_AGENT"],
                         username=environ["BUZZFEEDBOT_USERNAME"],
                         password=environ["BUZZFEEDBOT_PASSWORD"])

    subreddit = reddit.subreddit('buzzfeedbot')
    submissions = subreddit.new(limit=40)
    for submission in submissions:
        if submission.title.lower() == post_title:
            post_made = True
            break
        subpoints_to_check = [int(s) for s in submission.title.split() if s.isdigit()]
        if subpoints_to_check == subpoints:
            sameWords = set.intersection(set(post_title.split(" ")), set(submission.title.lower().split(" ")))
            numberOfWords = len(sameWords)
            if numberOfWords >=4:
                post_made = True
                break
    return post_made


def article_info(link, no_of_points):

    article_text_to_use = article_text(link, no_of_points)

    print(article_text_to_use)
    print(link)


def article_text(link_to_check, total_points):
    """Concatenates the main points of the article into a single string and also makes sure the string isn't empty.
Also checks to make sure  the number of subpoints in the article is equal to the number the atricle title starts with"""

    i = 1
    this_when_counter = 0
    top_x_final = ''
    session = requests.Session()
    article = session.get(link_to_check)
    soup = BeautifulSoup(article.content, 'html.parser')

    for title in soup.find_all('h3'):

        subpoint_check = False

        if title.find_all('span', attrs={'class': 'subbuzz__number'}):
            break

        if not subpoint_check:
            continue

        for article in title.find_all('span', attrs={'class': 'js-subbuzz__title-text'}):
            if len(article.text)<4 or article.text.endswith(':'):
                return ''
            else:
                top_x_final_temp = top_x_final
                if this_when_counter == 3:
                    return ''
                if article.text.startswith(('When ', 'This ', 'And this ')):
                    this_when_counter += 1
                else:
                    this_when_counter = 0
                try:
                    for link in article.find_all('a', href=True):
                        link_to_use = link['href']

                        if link_to_use.startswith('http:') and (r'/https:' in link_to_use or r'/http:' in link_to_use): #removes redirect link if there is any
                            link_to_use = 'http' + link_to_use.split(r'/http', 1)[1]
                        if 'amazon' in link['href']:  # Removes buzzfeed tag in all amazon links
                            link_to_use = link_to_use.split('?', 1)[0]
                        if article.text.startswith((str(i)+'.' , str(i)+')')):
                            top_x_final += '[' + article.text + '](' + link_to_use+')' + '\n'
                        else:
                            top_x_final += str(i) + '. [' + article.text + '](' + link_to_use+')' + '\n'
                        break
                except KeyError:
                    pass
                if top_x_final_temp == top_x_final:
                    if article.text.startswith((str(i)+'.' , str(i)+')')):
                        top_x_final += article.text  + '\n'
                    else:
                        top_x_final += str(i) + '. ' + article.text + '\n'
            i += 1

    if total_points != i-1:
        top_x_final = ''
    return top_x_final


if __name__ == "__main__":

    # Enter buzzfeed article link and number of points in article
    article_info(link='', no_of_points=0)