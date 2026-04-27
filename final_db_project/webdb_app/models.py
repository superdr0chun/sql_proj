from django.db import models

class Server(models.Model):
    name = models.CharField(max_length=255, unique=True)
    connection_string = models.TextField()
    server_type = models.CharField(max_length=50, default='postgresql')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Database(models.Model):
    server = models.ForeignKey(Server, on_delete=models.CASCADE, related_name='databases')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['server', 'name']

    def __str__(self):
        return f"{self.server.name}.{self.name}"
