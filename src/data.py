from typing import Dict, Tuple, Set
from os import environ
from twitter import Api
from peewee import OperationalError
from models import (User, Document, Annotation, Tweet,
                    AnnotationSimilarity, BaseModel, db)
from nltk import work_tokenize, download
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)


def print_info(tweet):
    print(tweet.user.screen_name)
    print(tweet.full_text or tweet.text)
    print(tweet.hashtags)
    print(tweet.contributors)
    print(tweet.in_reply_to_screen_name)
    print(tweet.user_mentions)
    print("\n")


def update_many(entity: BaseModel, data: Dict[str, float]):
    for (k, v) in data:
        entity.update(rank=data[k]).where(id=k)


def get_user_rank(user_id: str) -> float:
    return float(User.select(User.rank).where(User.id == user_id))


def get_term_user_times(term: str, user: str) -> int:
    docs = Document(Tweet.select(Tweet.id_document).where(
        Tweet.id_annotation == term))
    count = 0
    for doc in docs:
        if doc.user_r == user or doc.user_w == user:
            count += 1
    return count


def wait_for_db():
    flag = True
    while flag:
        try:
            db.connect()
            flag = False
        except OperationalError:
            flag = True
    return db


def close_connection():
    db.close()


def create_db():
    db.create_tables([User, Document, Annotation,
                      Tweet, AnnotationSimilarity])


def normalize_data(text: str, user_r: str=None) -> Set[str]:
    wnl = WordNetLemmatizer()
    seng = stopwords.words("english")
    sita = stopwords.words("italian")
    if sita is None or seng is None:
        download()


def get_aa_subset(query: str) -> Dict[Tuple[str, str], float]:
    normalize_data(query)
    key_subset = []
    for annotation in annotations:
        key_contains()

def key_contains(keys, key, ret=[]):
    for k in keys:
        if k[0] == key:
            ret.add(k[1])
        elif k[1] == key:
            ret.add(k[0])
    return ret


def save_data(tweet, u_r, u_w):
    with db.atomic():
        User.get_or_create(id=u_w.id)
        if Document.select(id).where(Document.id == tweet.id).count() == 0:
            Document.get_or_create(id=tweet.id,
                                   user_w=u_w.id,
                                   user_r=u_r.id)
        hashtags = {hashtag.text for hashtag in tweet.hashtags}
        for hashtag in hashtags:
            Annotation.get_or_create(id=hashtag)
            Tweet.get_or_create(id_document=tweet.id,
                                id_annotation=hashtag)


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
        User.get_or_create(id=friend_id)
        friend_timeline = api.GetUserTimeline(user_id=friend_id, count=200)
        friend = api.GetUser(user_id=friend_id)
        print("GETTING STATUSES OF ", friend.screen_name)
        for tweet in friend_timeline:
            save_data(tweet, friend, tweet.user)
        print("GETTING MENTIONS OF ", friend.screen_name)
        for tweet in api.GetSearch(term=friend.screen_name, count=100):
            if tweet.user.id != friend_id:
                save_data(tweet, friend, tweet.user)
