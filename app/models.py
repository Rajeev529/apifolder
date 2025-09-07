from django.db import models

# Create your models here.
class user_data(models.Model):
    username=models.TextField()
    email=models.EmailField()
    password=models.CharField(max_length=20)
    date=models.DateTimeField(auto_now_add=True)
    balance=models.FloatField()

class API(models.Model):
    user = models.ForeignKey(user_data, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    
    api_key = models.CharField(max_length=255, unique=True)
    retriever_path = models.CharField(max_length=500)  # FAISS index path
    created_at = models.DateTimeField(auto_now_add=True)
    desc=models.TextField()
    key1=models.TextField()
    val1=models.TextField()
    key2=models.TextField()
    val2=models.TextField()
    key3=models.TextField()
    val3=models.TextField()
    # amount=models.FloatField()
    def __str__(self):
        return f"{self.name} ({self.user.username})"


class Document(models.Model):
    api = models.ForeignKey(API, on_delete=models.CASCADE, related_name="documents")
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} -> {self.api.name}"
class chats(models.Model):
    user=models.ForeignKey(user_data, on_delete=models.CASCADE)
    data=models.JSONField(blank=True, default=dict)
    retriever_path = models.CharField(max_length=500)  # FAISS index path
    lang=models.CharField(max_length=30)
    name=models.CharField(max_length=30)
    api_key = models.CharField(max_length=255, unique=True)
    

class Document2(models.Model):
    api = models.ForeignKey(chats, on_delete=models.CASCADE, related_name="documents")
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)