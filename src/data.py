from typing import Dict, Tuple, Set
import urlmarker
import re
from os import environ
from twitter import Api
from peewee import OperationalError
from models import (User, Document, Annotation, Tweet,
                    AnnotationSimilarity as AAS, BaseModel, db)
from nltk import word_tokenize, pos_tag
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
    print(tweet.lang)
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
    while True:
        try:
            db.connect()
            break
        except OperationalError:
            pass
    return db


def close_connection():
    db.close()


def create_db(db):
    db.create_tables([User, Document, Annotation,
                      Tweet, AAS])


def normalize_data(text: str,
                   user_r: str=None) -> Set[str]:
    text = remove_urls(text)
    wnl = WordNetLemmatizer()
    stop: Set[str] = stopwords.words("english")
    tags: Set[str] = set()
    token = pos_tag(word_tokenize(text))
    name = ""
    for word, pos in token:
        word = wnl.lemmatize(word)
        if word not in stop:
            if word[0] is not "#":
                if pos == "NNP":
                    if name is "":
                        name = word
                    else:
                        name = name + " " + word
                else:
                    tags.add(name)
                    name = ""
                    if pos == "NN":
                        tags.add(word)

    return tags


def get_aa_subset(query: str) -> Dict[Tuple[str, str], float]:
    annotations = normalize_data(query)
    key_subset = []
    annotations: List[Tuple[str, str]] = AAS.select(
        AAS.annotation1, AAS.annotation2)
    for annotation in annotations:
        key_contains()


def key_contains(keys, key, ret=[]):
    for k in keys:
        if k[0] == key:
            ret.add(k[1])
        elif k[1] == key:
            ret.add(k[0])
    return ret


def save_tweet(tag: str, doc_id: str):
    Annotation.get_or_create(id=tag)
    Tweet.get_or_create(id_document=doc_id, id_annotation=tag)


def remove_urls(text: str) -> str:
    return re.sub(urlmarker.URL_REGEX, "", text)



def save_data(tweet, u_r, u_w):
    if tweet.lang is not "en":
        return
    with db.atomic():
        User.get_or_create(id=u_w.id)
        if Document.select(id).where(Document.id == tweet.id).count() == 0:
            Document.get_or_create(id=tweet.id,
                                   user_w=u_w.id,
                                   user_r=u_r.id,
                                   language=tweet.lang)
        hashtags = {hashtag.text for hashtag in tweet.hashtags}
        for hashtag in hashtags:
            save_tweet(hashtag, tweet.id)
        for tag in normalize_data(tweet.text):
            save_tweet(tag, tweet.id)


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
        friend_timeline = api.GetUserTimeline(user_id=friend_id,
                                              count=200)
        friend = api.GetUser(user_id=friend_id)
        print("GETTING STATUSES OF ", friend.screen_name)
        for tweet in friend_timeline:
            save_data(tweet, friend, tweet.user)
        print("GETTING MENTIONS OF ", friend.screen_name)
        for tweet in api.GetSearch(term=friend.screen_name,
                                   lang="en",
                                   count=100):
            if tweet.user.id != friend_id:
                save_data(tweet, friend, tweet.user)
