from django.db import models
from django.contrib.auth.models import User

class School(models.Model):
    school_name = models.CharField(max_length=100)
    def __str__(self):
        return self.school_name
    class Meta:
        db_table = 'school'


class UserProfile(models.Model):
    ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('teacher', 'Teacher'),
    ('student', 'Student'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    def __str__(self):
        return self.user.username
    class Meta:
        db_table = 'user_profile'

class Student(models.Model):
    user=models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    reg=models.CharField(max_length=100,unique=True)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'student'


class Marks(models.Model):
    student=models.OneToOneField(Student, on_delete=models.CASCADE,related_name='marks')
    school=models.ForeignKey(School, on_delete=models.CASCADE)
    tamil = models.IntegerField()
    english = models.IntegerField()
    maths = models.IntegerField()
    science = models.IntegerField()
    social = models.IntegerField()
    total = models.FloatField()
    avg = models.FloatField()
    def __str__(self):
        return self.student.name
    class Meta:
        db_table = 'marks'


class Teacher(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    school = models.ForeignKey(School,on_delete=models.CASCADE)
    def __str__(self):
        return self.name

    class Meta:
        db_table = "teacher"

class Decorator(models.Model):
    API_name=models.CharField(max_length=500)
    API_Path=models.CharField(max_length=500)
    API_Method=models.CharField(max_length=500)
    API_use=models.CharField(max_length=500)
    Start_time=models.DateTimeField()
    Status=models.CharField(max_length=500)
    End_time=models.DateTimeField()
    Duration=models.CharField(max_length=500)

    def __str__(self):
        return self.API_name
    class Meta:
        db_table = 'decorator'

