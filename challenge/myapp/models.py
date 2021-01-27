from django.db import models


class Person(models.Model):
    fistname = models.TextField(default='')
    lastname = models.TextField(default='')

