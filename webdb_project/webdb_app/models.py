from django.db import models


class Server(models.Model):
    name = models.CharField(max_length=255, unique=True)
    host = models.CharField(max_length=255, default='localhost')
    port = models.IntegerField(default=5432)
    username = models.CharField(max_length=255, default='postgres')
    password = models.CharField(max_length=255, default='', blank=True)
    database = models.CharField(max_length=255, default='postgres')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class SavedQuery(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='saved_queries')
    name = models.CharField(max_length=255)
    query_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.server.name} - {self.name}"

    class Meta:
        ordering = ['name']
