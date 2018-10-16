# Creates a retweet network starting from a given first user
import twint
import numpy as np
import random
import time
import re
import requests
import sys


#sys.path.insert(0, '/ubc/cs/home/r/rlacombe/Twitter/tweepy/') # Add another folder from which to import modules/files
#import tweepy

import importlib.util
#spec = importlib.util.spec_from_file_location('module.name', '/ubc/cs/home/r/rlacombe/Twitter/tweepy/helper.py')
spec = importlib.util.spec_from_file_location('module.name', '/home/remi/Master_thesis/Research/Twitter/tweepy/helper.py')
foo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foo)

#1204982528 818096502 with Twitter handle: DonnaTa81840733 3178558838 with Twitter handle: CynsTreat 1037471229568065538 with Twitter handle: SavageKracker
first_user_id = '1204982528'

follower_threshold = 50000 # Maximum number of followers for targeted users
activity_threshold = 40 # Minimum accepted number of tweets/retweets
fc_threshold = 2 # Minimum accepted number of fn/fc
#topic_count_threshold = 2 # Number of times keyword was used in the last month
date = '2018-09-16'
date_int = 2000*int(date[:4]) + 100*int(date[5:7]) + int(date[8:10])
nb_consecutive = 10 # Number of consecutive older tweets to switch to next user when scrapping a profile

# List of keywords to spot potential users (case sensitive)
keywords = ['senate', 'Senate', 'midterm', 'Midterm', 'politics', 'Politics', 'Democrats', 'democrats', 'Republicans', 'republicans']

fc_file = open('fact_check.txt', 'r')
fn_file = open('fake_news.txt', 'r')

fc_websites = []
fn_websites = []
# Include popular news websites to avoid loosing time when unshortnening URLs
popular_websites = ['cnn', 'nyp', 'reut.rs', 'bloom.bg', 'nyti', 'apple', 'vote.gov', 'huffp', 'apne', 'abcn', 'nbcnews', 'youtu.be']

for line in fc_file:

    fc_websites.append(line[:-1])

for line in fn_file:

    fn_websites.append(line[:-1])


open('network.csv', 'w').close()
file = open('network.csv', 'w')
users_seen = set()
users_seen.add(first_user_id)

user_counter = 0
error_counter = 0 # Some tweets might be split in two when being scraped
global_fn_count = 0
global_fc_count = 0
users_list = {first_user_id: first_user_id}

#users_list = [first_user_id]
#new_users_list = [first_user_id]

c = twint.Config
c.Lang = 'en'
c.Date = date_int
c.Limit = 500
c.Store_csv = True
c.Output = 'tweets.csv'
c.Custom = ['user_id', 'date', 'time', 'tweet']
c.Profile_full = False
c.Show_hashtags = True
c.Verbose = False
c.Nb_consecutive = nb_consecutive

session = requests.Session()

start_time = time.time()

while len(users_list) != 0:

    sys.stdout.flush() # To be able to access to the output before the program exits

    user = random.choice(list(users_list))

    c.User_id = user
    open('tweets.csv', 'w').close()

    twint.run.Profile(c)

    activity_score = sum(1 for line in open('tweets.csv')) # Nb of tweets/retweets during the last month
    my_file = open('tweets.csv', 'r')
    fn_score = 0 # Nb of links to FC websites
    fc_score = 0 # Nb of links to F websites

    if activity_score > activity_threshold:

        potential_users = [] # Temporarily stores interesting followees

        print('The current investigated user is: ' + user)

        for line in my_file:

            indices = [pos for pos, char in enumerate(line) if char == ","]

            if len(indices) < 3:
                error_counter += 1
                print('A tweet was split in two here')

            else:
                user_id = line[:indices[0]]

                # Get the original URLs from shortened URLs
                tweet = line[indices[2]:-1]

                #if fn_score + fc_score >= fc_threshold: # Avoid unecessary queries for original URLs

                flag_indices = [m.start() for m in re.finditer("http", tweet)]

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

                if any(substring in line for substring in fc_websites):
                    fc_score += 1

                elif any(substring in line for substring in fn_websites):
                    fn_score += 1

                # Identify if the retweeted user is 'interesting'
                if user_id != user and any(substring in line for substring in keywords) and user_id not in potential_users and user_id not in users_seen and foo.followers_count([user_id]) < follower_threshold:
                    potential_users.append(user_id)


        if fn_score + fc_score >= fc_threshold:

            global_fc_count += fc_score
            global_fn_count += fn_score
            print('Number of FC items for user: ' + user + ' is: ' + str(fc_score) + '. Global count is: ' + str(global_fc_count))
            print('Number of FN items for user: ' + user + ' is: ' + str(fn_score) + '. Global count is: ' + str(global_fn_count))

            print('A new user is added to the network, please welcome: ' + user)
            file.write(user + ',' + users_list[user] + ',' + str(activity_score) + ',' + str(fc_score) + ',' + str(fn_score) + '\n')
            user_counter += 1
            print('Current user count: ' + str(user_counter))

            if user_counter == 5000:
                print('Network size cap has been reached !')
                break

            for user_id in potential_users:
                relationship = foo.follower_check(user, user_id)
                if relationship[0] == True: # Our user has to follow the user she retweets
                    users_list[user_id] = user
                    users_seen.add(user_id)
                    print('retweeted user is followed')
                else:
                    print('retweeted user is NOT followed')

    users_list.pop(user)
    my_file.close()

print('The total number of errors was: ' + str(error_counter))
print('The total FC count is: ' + str(global_fc_count))
print('The total FN count is: ' + str(global_fn_count))

elapsed_time = time.time() - start_time
print('Running time: ' + str(elapsed_time) + ' seconds')

file.close()
fn_file.close()
fc_file.close()
