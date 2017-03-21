from peewee import (DoubleField, TextField,
                    ForeignKeyField, CompositeKey,
                    Model)

from playhouse.db_url import connect
from os import environ


def get_url() -> str:
    url = environ["TQE_DB_URL"]
    return url


class BaseModel(Model):
    class Meta:
        database = connect(get_url())


class User(BaseModel):
    id_user = TextField(primary_key=True)
    rank = DoubleField()


class Document(BaseModel):
    id_document = TextField(primary_key=True)
    rank = DoubleField()


class Annotation(BaseModel):
    id_annotation = TextField(primary_key=True)
    rank = DoubleField()


class Tweet(BaseModel):
    user_w = ForeignKeyField(User, on_delete="CASCADE",
                             related_name="posted")
    user_r = ForeignKeyField(User, on_delete="CASCADE",
                             related_name="received")
    id_document = ForeignKeyField(Document, on_delete="CASCADE",
                                  related_name="tweet")
    annotation = ForeignKeyField(Annotation, on_delete="CASCADE",
                                 related_name="tweets")

    class Meta:
        indexes = (
            (('user_w', 'user_r', 'id_document', 'annotation'), True)
        )


class AnnotationSimilarity(BaseModel):
    annotation1 = ForeignKeyField(Annotation, on_delete="CASCADE")
    annotation2 = ForeignKeyField(Annotation, on_delete="CASCADE")
    rank = DoubleField()

    class Meta:
        primary_key = CompositeKey('annotation1', 'annotation2')
