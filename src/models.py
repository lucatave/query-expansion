from peewee import (DoubleField, TextField,
                    ForeignKeyField, CompositeKey,
                    Model)

from playhouse.postgres_ext import PostgresqlDatabase
from os import environ


class BaseModel(Model):
    class Meta:
        database = PostgresqlDatabase(environ["POSTGRES_DB"],
                                      user=environ["POSTGRES_USER"],
                                      password=environ["POSTGRES_PASSWORD"],
                                      host=environ["DB_HOST"],
                                      port=environ["DB_PORT"])


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
