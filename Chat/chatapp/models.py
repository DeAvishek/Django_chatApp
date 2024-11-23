from django.db import models
from django.contrib.auth.models import User

# Create your models here
#room model for represents only the chat room
class Room(models.Model):
    room_id=models.CharField( max_length=50,unique=True)
    user_1=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user_1_rooms')
    user_2=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user_2_rooms')
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.room_id}"
    
class Message(models.Model):
    message=models.TextField()
    user=models.ForeignKey(User,related_name='messages',on_delete=models.CASCADE)
    room=models.ForeignKey(Room,related_name='messages',on_delete=models.CASCADE)
    timestamp=models.DateTimeField(auto_now_add=True)
    
    def __str__(self) :
        return f"{self.user.username} & {self.message[:20]}"

