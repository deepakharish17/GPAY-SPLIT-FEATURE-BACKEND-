from django.urls import path, URLPattern
from .views import Add_School
from project import views
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
urlpatterns = [
    # path('index', views.index,name='index'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('Add_School/', Add_School.as_view(),name='Add_School'),
    path('Admin_Add_Teacher/', views.Admin_Add_Teacher.as_view(),name='Admin_Add_Teacher'),
    path('Admin_Add_Student/', views.Admin_Add_Student.as_view(),name='Admin_Add_Student'),
    path('Admin_Add_Marks/', views.Admin_Add_Marks.as_view(),name='Admin_Add_Marks'),
    path('Student_My_Marks/', views.Student_My_Marks.as_view(),name='Student_My_Marks'),
    path('View_All_Marks/', views.View_All_Marks.as_view(),name='View_All_Marks'),
    path('ExportStudentExcel/',views.ExportStudentExcel.as_view(),name='ExportStudentExcel'),
    path('UpdateByExcel/',views.UpdateByExcel.as_view(),name='UpdateByExcel'),
    path('AddByExcel/',views.AddByExcel.as_view(),name='AddByExcel'),

]

