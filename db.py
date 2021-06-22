import peewee
from datetime import datetime
import pytz

db = peewee.SqliteDatabase('database.db')


class User(peewee.Model):
    id = peewee.AutoField()
    chat_id = peewee.IntegerField(unique=True)
    status = peewee.TextField(default="student")
    full_name = peewee.TextField(null=True)
    photo = peewee.TextField(null=True)
    subject = peewee.TextField(null=True)
    info = peewee.TextField(null=True)
    speciality = peewee.TextField(null=True)
    likes = peewee.IntegerField(default=0)
    dislikes = peewee.IntegerField(default=0)
    reg_date = peewee.DateTimeField(default=datetime.now(pytz.timezone('Europe/Kiev')))

    class Meta:
        database = db
        db_table = 'users'

class Like(peewee.Model):
    id = peewee.AutoField()
    student_chat_id = peewee.IntegerField()
    teacher_chat_id = peewee.IntegerField()
    value = peewee.TextField()

    class Meta:
        database = db
        db_table = 'likes'
class Rating(peewee.Model):
    id = peewee.AutoField()
    student_chat_id = peewee.IntegerField()
    teacher_chat_id = peewee.IntegerField()
    key = peewee.TextField()
    value = peewee.FloatField()

    class Meta:
        database = db
        db_table = 'ratings'



User.create_table()
Rating.create_table()
Like.create_table()