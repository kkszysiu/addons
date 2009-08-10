from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from thumbs import ImageWithThumbsField

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    jid = models.EmailField()

class Category(models.Model):
    cat_image = models.ImageField(upload_to='categories')
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __unicode__(self):
        return self.name

class Addon(models.Model):
    category = models.ForeignKey(Category)
    name = models.CharField(max_length=255)
    description = models.TextField()
    pub_date = models.DateTimeField(default=datetime.now())
    author = models.ForeignKey(User)
    n_downloads = models.IntegerField(default=0)
    modified = models.DateTimeField(default=datetime.now())
    rating = models.IntegerField(default=0)
    #tags_field = models.CharField(max_length=255, default='')

    def __unicode__(self):
        return self.description

#tagging.register(Addon)

class Screenshot(models.Model):
    addon = models.ForeignKey(Addon)
    description = models.CharField(max_length=255)
    screenshot = ImageWithThumbsField(upload_to='screenshots', sizes=((128,128), (256, 256)))
    
    def __unicode__(self):
        return self.description

class Versioning(models.Model):
    addon = models.ForeignKey(Addon)
    version = models.CharField(max_length=100)
    codename = models.CharField(max_length=255)
    description = models.TextField()
    pub_date = models.DateTimeField(default=datetime.now())
    file = models.FileField(upload_to='addons')

    def __unicode__(self):
        return self.name
