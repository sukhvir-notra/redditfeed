import sys
import praw
import time
import requests
import json
from discord_webhook import DiscordWebhook, DiscordEmbed
import sqlite3

CONFIG_FILE='config.json'

def check_new_posts(sub):
    for post in r.subreddit(sub).new(limit=10):
        if config['keywords']['enabled'] and not any(x.lower() in post.title.lower() for x in config['keywords']['list']):
            seen_posts.append(post.id)
        cur.execute('SELECT id FROM posts WHERE id=?',(post.id,))
        data = cur.fetchall()
        if not data:
            notify(sub, post.title, post.url)
            cur.execute('INSERT INTO posts VALUES(?)',(post.id,))
            con.commit()
            time.sleep(5)

def notify(subreddit, title, url):
    if config['discord']['enabled']:
        notify_discord(subreddit, title, url)
    if config['slack']['enabled']:
        notify_slack(subreddit, title, url)
    if config['reddit_pm']['enabled']:
        notify_reddit(subreddit, title, url)
    if config['debug']:
        print(subreddit + ' | ' + title + ' | ' +  url)

def notify_discord(subreddit, title, url):
    webhook = DiscordWebhook(url=config['discord']['webhook'])
    embed = DiscordEmbed(title=title, url=url, color=242424)
    embed.set_author(name='/r/'+subreddit)
    #embed.set_image(url='your image url')
    webhook.add_embed(embed)
    webhook.execute()

def notify_slack(subreddit, title, url):
    message = title + " | " + url
    payload = { 'text': message }
    headers = { 'Content-Type': 'application/json', }
    requests.post(config['slack']['webhook'], data=json.dumps(payload), headers=headers)

def notify_reddit(subreddit, title, url):
    if title is 'Modqueue':
        subject = 'New item in modqueue on /r/' + subreddit + '!'
    else:
        subject = 'New post on /r/' + subreddit + '!'

    message = '[' + title + '](' + url + ')'

    for user in config['reddit_pm']['users']:
        r.redditor(user).message(subject, message)


with open(CONFIG_FILE) as config_file:
    config = json.load(config_file)

r = praw.Reddit(
    user_agent = config['reddit']['user_agent'],
    client_id = config['reddit']['client_id'],
    client_secret = config['reddit']['client_secret'],
    username = config['reddit']['username'],
    password = config['reddit']['password']
)

con=sqlite3.connect('posts.db')
cur=con.cursor()
cur.execute('CREATE TABLE posts(ID TEXT)')
con.commit()


#seen_posts = []
#first = True

while True:
    try:
        for sub in config['subreddits']:
            if config['new_posts']:
                check_new_posts(sub)
            time.sleep(10)
            #first = False
    except KeyboardInterrupt:
        print('\n')
        sys.exit(0)
    except Exception as e:
        print('Error:', e)
        time.sleep(5)


