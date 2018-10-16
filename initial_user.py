# Finds an interesting initial user to create the network
import twint

import numpy as np
import time
import re
import requests


import importlib.util
spec = importlib.util.spec_from_file_location('module.name', '/home/remi/Master_thesis/Research/Twitter/tweepy/helper.py')
foo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foo)

fc_file = open('fact_check.txt', 'r')
fn_file = open('fake_news.txt', 'r')

fc_websites = []
fn_websites = []
# Include popular news websites to avoid loosing time when unshortnening URLs
popular_websites = ['cnn', 'nyp', 'reut.rs', 'bloom.bg', 'nyti', 'apple', 'vote.gov', 'huffp', 'apne', 'abcn', 'nbcnews', 'youtu.be']
black_list = ['snopes', 'WuWeiToday', 'FactandMythCom', 'politifact']

topic = 'republicans'
topic_count_threshold = 2 # Number of times keyword was used in the last month
activity_threshold = 40 # Minimum accepted number of tweets/retweets
fc_threshold = 3 # Minimum accepted number of FN/FC
date = '2018-09-16'
date_int = 2000*int(date[:4]) + 100*int(date[5:7]) + int(date[8:10])
nb_consecutive = 10 # Number of consecutive older tweets to switch to next user when scrapping a profile
follower_threshold = 10000

# List of keywords to spot potential users (case sensitive)
keywords = ['senate', 'Senate', 'midterm', 'Midterm', 'politics', 'Politics', 'Democrats', 'democrats', 'Republicans', 'republicans']

# Run a quick first search for potential initial users
c = twint.Config
c.Lang = 'en'
c.Limit = 40 # Number of candidates (batches of 20 and one 'Limit' for each website)
c.Since = date
c.Show_hashtags = True
c.Verbose = False
c.Count = True
c.Nb_consecutive = nb_consecutive

open('first.csv', 'w').close()
c.Store_csv = True
c.Custom = ['user_id', 'username']
c.Output = 'first.csv'

for line in fc_file:

    website = line[:-1]
    #c.Search = topic + ' ' + website
    if website != 'snopes.com':
        c.Search = website
        twint.run.Search(c)

    fc_websites.append(website)

for line in fn_file:

    fn_websites.append(line[:-1])

users_seen = set() # To avoid looking twice for the same user
my_file = open('first.csv', 'r')
first_user_id = 0

c.Custom = ['tweet']
c.Output = 'tweets_ini.csv'
c.Limit = 200
c.Date = date_int
c.Profile_full = False

# Find active initial users
for line in my_file:

    index = [pos for pos, char in enumerate(line) if char == ","][0]
    user_id = line[:index]
    username = line[index + 1:-1]

    if user_id not in users_seen and foo.followers_count([user_id]) < follower_threshold and username not in black_list:

        open('tweets_ini.csv', 'w').close()
        c.User_id = user_id

        twint.run.Profile(c)

        activity_score = sum(1 for line in open('tweets_ini.csv')) # Nb of tweets/retweets during the last month
        your_file = open('tweets_ini.csv', 'r')
        topic_count = 0
        fc_score = 0 # Nb of links to FC websites
        fn_score = 0 # Nb of links to F websites

        if activity_score > activity_threshold:

            for line in your_file:

                # Get the original URLs from shortened URLs
                tweet = line[:-1]

                #if fc_score < 3 or fn_score < 2: # Avoid unecessary queries for original URLs

                flag_indices = [m.start() for m in re.finditer("http", tweet)]

                session = requests.Session()

                if len(flag_indices) != 0:
                    for i in flag_indices:
                        index = tweet.find(chr(160) or chr(32), i)
                        link = tweet[i:index]

                        if len(link) < 25 and not any(substring in tweet for substring in popular_websites): # The link is a shortened link
                            try:
                                resp = session.head(link, allow_redirects = True) # Veryyy slow
                                tweet += resp.url # Add the full link to the tweet
                            except:
                                pass

                if any(substring in tweet for substring in fc_websites):
                    fc_score += 1

                elif any(substring in tweet for substring in fn_websites):
                    fn_score += 1

                if any(substring in tweet for substring in keywords):
                    topic_count += 1

        if topic_count >= topic_count_threshold and fc_score + fn_score >= fc_threshold:
            print('An initial user has been found with: ' + str(topic_count) + ' topic count.')
            print('Her FC score is: ' + str(fc_score) + ' and her FN score is: ' + str(fn_score))
            first_user_id = user_id
            print('This user is: ' + first_user_id + ' with Twitter handle: ' + username)
            #your_file.close()
            #break

        users_seen.add(user_id)
        your_file.close()

my_file.close()

if first_user_id == 0:
    raise ValueError('Warning ! No initial user has been found !')
