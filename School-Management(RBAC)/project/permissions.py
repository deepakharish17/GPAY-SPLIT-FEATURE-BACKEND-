from rest_framework.permissions import BasePermission
from .models import UserProfile

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        try:
            profile = UserProfile.objects.get(user=request.user)
            return profile.role == "ADMIN"
        except UserProfile.DoesNotExist:
            return False
# class IsAdmin(BasePermission):
#
#     def has_permission(self, request, view):
#
#         print("USER =", request.user)
#
#         profile = UserProfile.objects.get(
#             user=request.user
#         )
#
#         print("ROLE =", profile.role)
#
#         return profile.role == "ADMIN"

class IsAdminOrTeacher(BasePermission):

    def has_permission(self, request, view):
        try:
            profile = UserProfile.objects.get(user=request.user)
            return profile.role in ["ADMIN","TEACHER"]
        except UserProfile.DoesNotExist:
            return False

class IsStudent(BasePermission):

    def has_permission(self, request, view):

        print("USER =", request.user)
        try:
            profile = UserProfile.objects.get(
                user=request.user
            )
            print("ROLE =", profile.role)
            return profile.role == "STUDENT"
        except UserProfile.DoesNotExist:
            print("NO PROFILE FOUND")
            return False

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        try:
            profile = UserProfile.objects.get(user=request.user)
            return profile.role == "teacher"
        except UserProfile.DoesNotExist:
            return False