import tweepy
import webbrowser

consumer_token = 'h4hVnKqsDbERkxRsKOdRUrzGt'
consumer_secret = 'Jr5uLHs27COM9qojI8MmPkR3GiiEzmdzFafeVYeCXz3ugPmOPj'

auth = tweepy.OAuthHandler(consumer_token, consumer_secret)

try:
    redirect_url = auth.get_authorization_url()
except tweepy.TweepError:
    print('Error! Failed to get request token.')

webbrowser.open(redirect_url)

pin = input('PIN? ').strip()

try:
    token = auth.get_access_token(verifier=pin)
except tweepy.TweepError:
    print('Error! Failed to get access token.')

#key = token.key
#secret = token.secret

print(token)
