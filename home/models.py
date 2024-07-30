from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    telegram_id = models.IntegerField("Telegram ID", null=True, blank=True)
    login_code = models.IntegerField("Login Code", null=True, blank=True)
    passed_login_code = models.BooleanField('Passed Login Code?', null=True, blank=True)


class Room(models.Model):
    name = models.TextField(max_length=200)
    invite_link = models.TextField(max_length=36)
    date_created = models.DateTimeField("date created")
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    join_date = models.DateTimeField("join date")
    is_admin = models.BooleanField()
    left = models.BooleanField(default=False)

    def __str__(self):
        return ("(!) " if self.is_admin else "") + self.user.username + " in " + self.room.name


class Message(models.Model):
    text = models.TextField(max_length=4000)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    sender = models.ForeignKey(Member, on_delete=models.PROTECT)
    date = models.DateTimeField("date")
    replied_message = models.ForeignKey('self', on_delete=models.DO_NOTHING, null=True, blank=True)

    def __str__(self):
        return str(self.sender) + '(Message)'

