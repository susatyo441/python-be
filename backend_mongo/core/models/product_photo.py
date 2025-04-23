from mongoengine import *
import datetime

class ProductPhoto(Document):
    key = IntField(required=True)
    photo = StringField(required=True)
    productId = ObjectIdField(required=True)  # ini foreign key manual

    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'product_photos'}