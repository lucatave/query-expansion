from os import environ
from twitter import Api

def save_data():
    pass

def get_data():
    cons_key = environ["TWITTER_CONSUMER_KEY"]
    cons_secret = environ["TWITTER_CONSUMER_SECRET"]
    user_access = environ["TWITTER_USER_ACCESS"]
    user_secret = environ["TWITTER_USER_SECRET"]

    api = Api(consumer_key=cons_key,
              consumer_secret=cons_secret,
              access_token_key=user_access,
              access_token_secret=user_secret)

    for friend_id in api.GetFriendIDs():
        friend_timeline = api.GetUserTimeline(user_id=friend_id, count=200)
        for tweet in friend_timeline:
            save_data()
