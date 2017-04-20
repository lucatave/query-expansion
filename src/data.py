from typing import Dict, Tuple, Set
from math import log10 as log
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
from sys import maxsize
from random import randint
from sys import stderr
from logging import (debug, info)
dotenv_path = join(dirname(__file__), '../.env')
load_dotenv(dotenv_path)


def dict_k_add_item(d: Dict[str, float], k: int,
                    key: str, val: float) -> Dict[str, float]:
    if len(d.keys()) > k:
        del d[get_min_key_by_val(d)]
    d[key] = val
    return d


def dict_mat_x_dict(d1: Dict[str, Dict[str, int]],
                   d2: Dict[str, float],
                   result: Dict[str, float] = {}) -> Dict[str, float]:
    for r in d1.keys():
        sum = 0.0
        for c in d2.keys():
            if c in d1[r].keys():
                sum = sum + d1[r][c] * d2[c]
        result[r] = sum

    return result


def joined_dict_transpose(d: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
    ret: Dict[str, Dict[str, int]] = {}
    for k in d.keys():
        for kk in d[k].keys():
            # ret[kk] = {k: d[k][kk]}
            ret = update_dict(ret, (kk, k, d[k][kk]))
    return ret


def update_dict(d: Dict[str, Dict[str, int]], t: Tuple[str, str, int]) \
    -> Dict[str, Dict[str, int]]:
    dt = d.get(t[0], {})
    dt[t[1]] = t[2]
    d[t[0]] = dt
    return d


def query_from_dict_to_str(d: Dict[str, Set[str]]) -> str:
    sep_or = " OR "
    sep_and = " AND "
    query = ""
    fk = list(d.keys())[0]
    query += fk
    del d[fk]
    for k in d:
        l = list(d[k])
        query += sep_and + k
        n = len(l)
        if n > 1:
            query += sep_or + l[0]
        for i in range(1, n):
            query += sep_or + l[i]
    return query


def update_model(rows, d: Dict[str, float]):
    for t in rows:
        if t.id in d.keys():
            t.rank = d[t.id]
            t.save()


def from_socialpagerank_to_db(spr: Tuple[Dict[str, float],
                                         Dict[str, float],
                                         Dict[str, float]]):
    update_model(Document.select(), spr[0])
    update_model(User.select(), spr[1])
    update_model(Annotation.select(), spr[2])


def from_db_to_socialpagerank_matPU() -> Dict[str, Dict[str, int]]:
    matPU: Dict[str, Dict[str, int]] = {}
    query = BaseModel.raw("\
    select tweet.id_document_id, document.user_w_id, count(*) \
    from tweet,document \
    where tweet.id_document_id = document.id \
    group by(tweet.id_document_id, document.user_w_id)").tuples()
    for (page, user, n) in query:
        matPU = update_dict(matPU, (page, user, n))

    return matPU


def from_db_to_socialpagerank_matAP() -> Dict[str, Dict[str, int]]:
    matAP: Dict[str, Dict[str, int]] = {}
    query = BaseModel.raw("\
    select tweet.id_annotation_id, tweet.id_document_id, count(*) \
    from tweet \
    group by (tweet.id_annotation_id, tweet.id_document_id)").tuples()
    for (ann, page, n) in query:
        matUA = update_dict(matAP, (ann, page, n))

    return matAP


def from_db_to_socialpagerank_matUA() ->Dict[str, Dict[str, int]]:
    matUA: Dict[str, Dict[str, int]] = {}
    query = BaseModel.raw("\
    select document.user_w_id, tweet.id_annotation_id, count(*) \
    from tweet,document \
    where tweet.id_document_id = document.id \
    group by(document.user_w_id, id_annotation_id)").tuples()
    for (user, ann, n) in query:
        matUA = update_dict(matUA, (user, ann, n))
    return matUA


def get_min_key_by_val(d: Dict[str, float]) -> str:
    _min = list(d.keys())[0]
    for k in d:
        if d[k] < d[_min]:
            _min = k
    return _min


def get_min_max_mat_dict(m: Dict[str, Dict[str, int]],
                         _min: int = maxsize,
                         _max: int = 0,) -> Tuple[int, int]:
    for k in m.keys():
        for kk in m[k].keys():
            if m[k][kk] < _min:
                _min = m[k][kk]
            elif m[k][kk] > _max:
                _max = m[k][kk]
    return (_min, _max)


def randomize_matP(matPU: Dict[str, Dict[str, int]],
                   matAP: Dict[str, Dict[str, int]],
                   matUA: Dict[str, Dict[str, int]]) -> Dict[str, float]:
    minmax = get_min_max_mat_dict(matPU)
    minmax = get_min_max_mat_dict(matAP, minmax[0], minmax[1])
    minmax = get_min_max_mat_dict(matUA, minmax[0], minmax[1])
    matP: Dict[str, float] = {}
    for doc in Document.select():
        matP[doc.id] = randint(minmax[0], minmax[1])
    return matP



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


def tf_iuf(term: str) -> float:
    n = int(Annotation.select().count())
    n_term = int(Tweet.select(Tweet.id_annotation_id).where(
        Tweet.id_annotation_id == term).count())

    tf = float(n_term/n)
    n = int(User.select().count())

    iuf = log(n/n_term)

    return float(tf * iuf)


def get_annotation_neighbours(a1: str) -> Set[str]:
    neighbour: Set[str] = set()
    docs = Tweet.select(Tweet.id_document).where(Tweet.id_annotation_id == a1)
    for doc in docs:
        candidates = Tweet.select(Tweet.id_annotation).where(
            Tweet.id_document == doc)
        for candidate in candidates:
            if candidate is not a1:
                neighbour.add(candidate)

    return neighbour


def get_users_from_term(term: str):
    return Document.select(Document.user_r_id).join(Tweet).where(
        Tweet.id_annotation_id == term)


def get_user_count_from_term(term: str) -> int:
    return get_users_from_term(term).count()


def get_term_count() -> int:
    return int(Annotation.select().count())


def get_terms():
    return Annotation.select(Annotation.id)


def get_user_rank(user_id: str) -> float:
    return float(User.select(User.rank).where(User.id == user_id))


def get_annotation_rank(annotation_id: str) -> float:
    return float(Annotation.select(Annotation.rank).where(
        Annotation.id == annotation_id))


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


def normalize_data(text: str) -> Set[str]:
    text = remove_urls(text)
    wnl = WordNetLemmatizer()
    stop: Set[str] = stopwords.words("english")
    stop.append(stopwords.words("spanish"))
    stop.append(stopwords.words("italian"))
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
        else:
            name = ""

    return tags


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
    with db.atomic():
        User.get_or_create(id=u_w.id)
        if Document.select().where(Document.id == tweet.id).count() == 0:
            Document.get_or_create(id=tweet.id,
                                   user_w=u_w.id,
                                   user_r=u_r.id,
                                   language=tweet.lang)
        hashtags = {hashtag.text for hashtag in tweet.hashtags}
        for hashtag in hashtags:
            save_tweet(hashtag, tweet.id)
        for tag in normalize_data(tweet.text):
            save_tweet(tag, tweet.id)


def save_replies(replies, u_r):
    for tweet in replies:
        save_data(tweet, u_r, tweet.user)


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
        info("GETTING STATUSES OF " + friend.screen_name)
        for tweet in friend_timeline:
            save_data(tweet, friend, tweet.user)
            # save_replies(api.GetRetweets(tweet.id, count=100), friend_id)
        info("GETTING MENTIONS OF " + friend.screen_name)
        for tweet in api.GetSearch(term=friend.screen_name,
                                   lang="en",
                                   count=100):
            if tweet.user.id is not friend_id:
                save_data(tweet, friend, tweet.user)
                # save_replies(api.GetRetweets(tweet.id, count=100), friend_id)
