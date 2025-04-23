from mongoengine import *
import datetime

class ProductVariantsAttr(EmbeddedDocument):
    name = StringField(required=True)
    price = IntField(required=True)
    capitalPrice = IntField(null=True)
    stock = IntField(required=True)

class AttributeEmbedded(EmbeddedDocument):
    _id = ObjectIdField()
    name = StringField()
    key = IntField()

class Product(Document):
    name = StringField(required=True)
    category = EmbeddedDocumentField(AttributeEmbedded)
    coverPhoto = StringField()
    stock = IntField()
    price = IntField()
    storeId = ObjectIdField(required=True)
    capitalPrice = IntField()
    variants = EmbeddedDocumentListField(ProductVariantsAttr)

    createdAt = DateTimeField(default=datetime.datetime)
    updatedAt = DateTimeField(default=datetime.datetime)

    meta = {'collection': 'products'}