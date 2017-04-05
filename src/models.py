from peewee import (DoubleField, TextField,
                    ForeignKeyField, CompositeKey,
                    Model)

from playhouse.postgres_ext import PostgresqlDatabase
from os import environ

db = PostgresqlDatabase(environ["POSTGRES_DB"],
                        user=environ["POSTGRES_USER"],
                        password=environ["POSTGRES_PASSWORD"],
                        host=environ["DB_HOST"],
                        port=environ["DB_PORT"])


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = TextField(primary_key=True)
    rank = DoubleField(null=True)


class Document(BaseModel):
    id = TextField(primary_key=True)
    user_w = ForeignKeyField(User, on_delete="CASCADE",
                             related_name="posted")
    user_r = ForeignKeyField(User, on_delete="CASCADE",
                             related_name="received")
    language = TextField()
    rank = DoubleField(null=True)


class Annotation(BaseModel):
    id = TextField(primary_key=True)
    rank = DoubleField(null=True)


class Tweet(BaseModel):
    id_document = ForeignKeyField(Document, on_delete="CASCADE",
                                  related_name="tweets")
    id_annotation = ForeignKeyField(Annotation, on_delete="CASCADE",
                                    related_name="tweets")

    class Meta:
        primary_key = CompositeKey('id_document', 'id_annotation')


class AnnotationSimilarity(BaseModel):
    annotation1 = ForeignKeyField(Annotation, on_delete="CASCADE",
                                  related_name="row")
    annotation2 = ForeignKeyField(Annotation, on_delete="CASCADE",
                                  related_name="column")
    rank = DoubleField(null=True)

    class Meta:
        primary_key = CompositeKey('annotation1', 'annotation2')
