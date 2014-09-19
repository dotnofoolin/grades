from datetime import date, timedelta, datetime
import os
from peewee import *

from config import *


if not os.path.exists('databases'):
    os.makedirs('databases')

database = SqliteDatabase('databases/' + USERNAME + '.sqlite')


class BaseModel(Model):
    class Meta:
        database = database


class Child(BaseModel):
    child_name = CharField(unique=True)

    class Meta:
        database = database


class Class(BaseModel):
    child_table = ForeignKeyField(Child)
    class_name = CharField()
    color = CharField()

    class Meta:
        database = database
        indexes = (
            (('child_table', 'class_name'), True),
        )


class Grade(BaseModel):
    class_table = ForeignKeyField(Class)
    grade_letter = CharField()
    grade_average = FloatField()
    post_date = DateField()
    post_desc = CharField()
    report_text = TextField()
    created_at = DateTimeField()

    class Meta:
        database = database
        indexes = (
            (('class_table', 'post_date', 'post_desc'), True),
        )


def create_tables():
    database.connect()
    database.create_tables([Child, Class, Grade], safe=True)


def save_report(child_name=None, class_name=None, grade_letter=None, grade_average=None, post_date=None, post_desc=None, report_text=None):
    # Try to create new children, classes, and grades. Silently fail if they already exist.

    try:
        child_object = Child.create(child_name=child_name)

    except:
        child_object = Child.get(Child.child_name == child_name)

    try:
        class_object = Class.create(child_table=child_object.id, class_name=class_name, color="#000000")

        # Get a color, and then put it back in the list. This is how I rotate them.
        color = CLASS_COLORS.pop(0)
        CLASS_COLORS.append(color)
        class_object.color = color
        class_object.save()

    except:
        class_object = Class.get(Class.class_name == class_name, Class.child_table == child_object.id)

    try:
        grade_object = Grade.create(
            class_table=class_object.id,
            grade_letter=grade_letter,
            grade_average=float(grade_average),
            post_date=post_date,
            post_desc=post_desc,
            report_text=report_text,
            created_at=datetime.now(),
        )

    except:
        pass