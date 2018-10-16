import tweepy
import pandas as pd
import numpy as np
import time


consumer_token = 'h4hVnKqsDbERkxRsKOdRUrzGt'
consumer_secret = 'Jr5uLHs27COM9qojI8MmPkR3GiiEzmdzFafeVYeCXz3ugPmOPj'
key = '1027268802755448832-gDCwmbpVhvAcmXnBk2pjGoiC0aRBU7'
secret = 'QHCBxfqTxux5RoNrgjFNYfCNA8XDSCkMPzmEeUckcfFqP'

auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(key, secret)
api = tweepy.API(auth)

#gbroh10 Bot? 167778891


'''
creator_id_list = []
my_file = open('network.csv', 'r')

for line in my_file:
    creator_id_list.append(line[:-1])

my_file.close()
'''

creator_id_list = ['38266703']

def from_creator(status, id_list):
    if status.in_reply_to_status_id != None or status.in_reply_to_screen_name != None or status.in_reply_to_user_id != None: # Reply to a tweet
        if status.user.id_str not in id_list:
            return False
        else:
            return True # Reply by one of the creators
    elif hasattr(status, 'retweeted_status'):
        if status.user.id_str not in id_list:
            return False
        else:
            return True # Retweet by one of the creators
    else:
        return True # Tweet by one of the creators

class MyStreamListener(tweepy.StreamListener):

    def __init__(self):
        self.attempts_nb = 0 # Should be put back to 0 after some time
        self.api = api
        open('tweets.csv', 'w').close()
        self.file = open('tweets.csv', 'w')

    def on_status(self, status):

        if from_creator(status, creator_id_list):

            print('New tweet/retweet added')
            is_retweet = hasattr(status, 'retweeted_status') # Check if this is a retweet

            if is_retweet: # Get the full tweet

                try:
                    string = status.retweeted_status.extended_tweet['full_text']
                except AttributeError:
                    string = status.retweeted_status.text

            else:

                try:
                    string = status.extended_tweet['full_text']
                except AttributeError:
                    string = status.text

            indices = [pos for pos, char in enumerate(string) if char == '\n'] # Remove '\n' from tweets
            if len(indices) == 0:
                tweet = string
            elif len(indices) == 1:
                tweet = string[0:indices[0]] + string[indices[0] + 1:-1]
            else:
                tweet = string[0:indices[0]]
                for i in range(len(indices) - 1):
                    tweet += string[indices[i] + 1:indices[i + 1]]
                tweet += string[indices[-1] + 1:-1]

            self.file.write(str(is_retweet) + ',' + str(status.id) + ',' + status.user.id_str + ',' + str(status.created_at) + ',' + tweet + '\n')

    def on_error(self, status_code):

        print('Error: ' + str(status_code))

        if status_code == 420:

            time.sleep(60*np.power(2,self.attempts_nb))

        else:

            time.sleep(5*np.power(2,self.attempts_nb))

        self.attempts_nb += 1
        print('Number of reconnection attempts: ' + str(self.attempts_nb))
        return True

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener, tweet_mode = 'extended')

myStream.filter(follow = creator_id_list)
