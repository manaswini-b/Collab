from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
import json
from django.utils import timezone


# Create your models here.
class Comments(models.Model):
	user = models.ForeignKey(User)
	text = models.CharField(max_length=255)
	channel = models.CharField(max_length=50)
	timestamp = models.DateTimeField(db_index=True)


class Channel(models.Model):
	admin = models.ForeignKey(User)
	user_list = JSONField()
	channel_name = models.CharField(max_length=50)
	channel_type = models.CharField(max_length=50)
