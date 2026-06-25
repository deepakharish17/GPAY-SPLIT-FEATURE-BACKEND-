from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin, IsAdminOrTeacher, IsStudent, IsTeacher
from django.http import JsonResponse
from .models import School, UserProfile, Marks, Teacher, Student
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from .decorator import api_details
from django.http import HttpResponse
import pandas as pd


def check_teacher_school(request,school_id):
    if request.user.userprofile.role=="ADMIN":
        return True
    teacher=Teacher.objects.get(
        user=request.user
    )
    return teacher.school.id==school_id

@method_decorator(api_details("This api is for School operations"),name="dispatch")
class Add_School(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):
        school_id = request.query_params.get("school_id")
        try:
            school = School.objects.get(id=school_id)
            return JsonResponse({
                "message":"School Found",
                "school":school.school_name,
                "school_id":school.id
            })
        except School.DoesNotExist:
            return JsonResponse({
                "message":"School Not Found"
            }, status=404)


    def post(self, request):
        school_name = request.data.get(
            "school_name"
        )

        try:
            school, created = School.objects.get_or_create(
                school_name=school_name
            )
            return JsonResponse({
                "message":
                "School Found",
                "school": school.school_name,
                "school_id":
                school.id
            })
        except School.DoesNotExist:
            return JsonResponse({
                "error":
                "School Not Found"
            }, status=404)


    def put(self, request):
        school_id = request.data.get("school_id")
        try:
            school = School.objects.get(id=school_id)
            school.school_name = request.data.get("school_name")
            school.save()
            return JsonResponse({
                "message":"School Updated",
                "school":school.school_name,
                "school_id":school.id
            })
        except School.DoesNotExist:
            return JsonResponse({
                "error":
                 "School Not Found"
            },status=404)

    def delete(self, request):
        school_id = request.data.get("school_id")
        try:
            school = School.objects.get(id=school_id)
            school.delete()
            return JsonResponse({
                "message":"School Deleted"
            })
        except School.DoesNotExist:
            return JsonResponse({
                "message":"School Not Found"
            }, status=404)

@method_decorator(api_details("For api is for teacher operations"),name="dispatch")
class Admin_Add_Teacher(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):
        teacher_id = request.query_params.get("teacher_id")
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            # name=
            return JsonResponse({
                "teacher":teacher.name,
                "teacher_id":teacher.id,
                "School":{
                    "id":teacher.school_id,
                    "name":teacher.school.school_name
                }
            })
        except Teacher.DoesNotExist:
            return JsonResponse({
                "message":"Teacher Not Found"
            },status=404)


    def post(self, request):
        school = School.objects.get(
            id=request.data.get("school_id")
        )
        user = User.objects.create_user(
            username=request.data.get("username"),
            password=request.data.get("password")
        )
        try:
            UserProfile.objects.create(
                user=user,
                role="TEACHER"
            )
            teacher = Teacher.objects.create(
                user=user,
                name=request.data.get("name"),
                subject=request.data.get("subject"),
                school=school
            )

            return Response({
                "message": "Teacher Added",
                "school": school.school_name,
                "school_id": school.id,
                "teacher_id": teacher.id,
                "teacher_name": teacher.name,
                "teacher_subject": teacher.subject,
                "teacher_username": user.username
            },status=201)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=400)

    def put(self, request):
        teacher_id = request.data.get("teacher_id")
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            teacher.name = request.data.get("name")
            teacher.subject = request.data.get("subject")
            teacher.school_id = request.data.get("school_id")
            teacher.save()
            return Response({
                "message":"Teacher Updated",
                "teacher":teacher.name,
                "teacher_id":teacher.id,
                "teacher_subject":teacher.subject,
                "school_id":teacher.school_id
            },status=200)
        except Teacher.DoesNotExist:
            return Response({
                "message":"Teacher Not Found"
            },status=404)

    def delete(self, request):
        teacher_id = request.data.get("teacher_id")
        try:
            teacher = Teacher.objects.get(id=teacher_id).delete()
            return Response({
                "message":"Teacher Deleted"
            },status=200)
        except Teacher.DoesNotExist:
            return Response({
                "message":"Teacher Not Found"
            },status=404)


@method_decorator(api_details("For api is for Student operations"),name="dispatch")
class Admin_Add_Student(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdmin
    ]

    def get(self, request):
        student_id = request.query_params.get("student_id")
        try:
            student = Student.objects.get(id=student_id)
            return JsonResponse({
                "student_id":student.id,
                "student_name":student.name,
                "student_age":student.age,
                "student_reg":student.reg,
                "student_school":{
                    "school_id":student.school.id,
                    "school_name":student.school.school_name}
            })
        except Student.DoesNotExist:
            return JsonResponse({
                "message":"Student Not Found"
            },status=404)

    def post(self, request):

        try:
            username = request.data.get("username")
            password = request.data.get("password")
            name = request.data.get("name")
            age = request.data.get("age")
            reg = request.data.get("reg")
            school_id = request.data.get("school_id")

            school = School.objects.get(id=school_id)
            if User.objects.filter(username=username).exists():
                return Response({ "error":"Username Already Exists"}, status=400)
            if Student.objects.filter(reg=reg).exists():
                return Response({"error":"Registration Number Already Exists"}, status=400)
            user = User.objects.create_user(
                username=username,
                password=password
            )
            UserProfile.objects.create(
                user=user,
                role="STUDENT"
            )
            student = Student.objects.create(
                user=user,
                name=name,
                age=age,
                reg=reg,
                school=school
            )

            return Response({
                "message":"Student Added",
                "student_id":student.id,
                "student_name":student.name,
                "student_age":student.age,
                "student_reg":student.reg,
                "username":user.username,
                "school_id":school.id,
                "school_name":school.school_name
            }, status=201)

        except School.DoesNotExist:
            return Response({"error":"School Not Found"}, status=404)
        except Exception as e:
            return Response({"error":str(e)}, status=500)

    def put(self, request):
        student_id = request.data.get("student_id")
        try:
            student = Student.objects.get(id=student_id)
            student.name = request.data.get("name")
            student.age = request.data.get("age")
            student.reg = request.data.get("reg")
            student.school_id = request.data.get("school_id")
            student.save()
            return Response({
                "message":"Student Updated",
                "student_id":student.id,
                "student_name":student.name,
                "student_age":student.age,
                "student_reg":student.reg,
                "school_id":student.school_id
            },status=200)
        except Student.DoesNotExist:
            return Response({
                "message":"Student Not Found"
            },status=404)

    def delete(self, request):
        student_id = request.data.get("student_id")
        try:
            student = Student.objects.get(id=student_id).delete()
            return Response({
                "message":"Student Deleted"
            },status=200)
        except Student.DoesNotExist:
            return Response({
                "message":"Student Not Found"
            },status=404)



@method_decorator(api_details("For api is for Teachers/Admin for marks operations"),name="dispatch")
class Admin_Add_Marks(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdminOrTeacher
    ]

    def get(self, request):
        student_id = request.query_params.get("student_id")
        try:
            marks = Marks.objects.get(student_id=student_id)
            if not check_teacher_school(
                    request,
                    marks.school.id
            ):
                return Response({
                    "error": "Access Denied"
                }, status=403)
            return Response({
                "student":marks.student.name,
                "tamil":marks.tamil,
                "english":marks.english,
                "maths":marks.maths,
                "science":marks.science,
                "social":marks.social,
                "total":marks.total,
                "avg":marks.avg
            })
        except Marks.DoesNotExist:
            return Response({"message":"Marks Not Found"},status=404)

    def post(self, request):
        try:
            student = Student.objects.get(
                id=request.data.get("student_id"))
            if not check_teacher_school(request,student.school.id):
                return Response({"error": "Access Denied"}, status=403)
            if Marks.objects.filter(student=student).exists():
                return Response({
                    "error": "Marks Already Added"
                }, status=400)
            tamil = int(request.data.get("tamil"))
            english = int(request.data.get("english"))
            maths = int(request.data.get("maths"))
            science = int(request.data.get("science"))
            social = int(request.data.get("social"))
            total = (tamil + english +maths +science +social)
            avg = total / 5
            marks = Marks.objects.create(
                student=student,
                school=student.school,
                tamil=tamil,
                english=english,
                maths=maths,
                science=science,
                social=social,
                total=total,
                avg=avg
            )
            return Response({
                "message": "Marks Added",
                "student": student.name,
                "total": total,
                "avg": avg }, status=201)

        except Student.DoesNotExist:
            return Response({ "error": "Student Not Found"}, status=404)

    def put(self, request):

        student_id = request.data.get( "student_id")
        try:
            marks = Marks.objects.get(student_id=student_id)
            if not check_teacher_school( request, marks.school.id):
                return Response({"error": "Access Denied"}, status=403)
            marks.tamil = request.data.get( "tamil")
            marks.english = request.data.get( "english")
            marks.maths = request.data.get("maths")
            marks.science = request.data.get("science")
            marks.social = request.data.get("social")
            marks.total = (int(marks.tamil) +int(marks.english) +int(marks.maths) +int(marks.science) +int(marks.social))
            marks.avg = marks.total / 5
            marks.save()
            return Response({ "message": "Marks Updated"})
        except Marks.DoesNotExist:
            return Response({"messge": "Marks Not Found"}, status=404)

    def delete(self, request):
        student_id = request.data.get(
            "student_id"
        )
        try:
            marks = (Marks.objects.get(student_id=student_id))
            if not check_teacher_school( request, marks.school.id):
                return Response({"error": "Access Denied"}, status=403)
            marks.delete()
            return Response({"message": "Marks Deleted"}, status=200)
        except Marks.DoesNotExist:
            return Response({"message": "Marks Not Found" }, status=404)


@method_decorator(api_details("For api is for teacher/students to view their marks "),name="dispatch")
class Student_My_Marks(APIView):

    permission_classes=[
        IsAuthenticated,
        IsStudent
    ]
    def get(self,request):
        student_id=request.query_params.get("student_id")
        try:
            student=Student.objects.get( id=student_id)
            if student.user != request.user:
                return Response({
                    "error":"Access Denied"
                },status=403)
            marks=Marks.objects.get( student=student)
            return Response({
                "student":student.name,
                "reg":student.reg,
                "total":marks.total,
                "avg":marks.avg
            })
        except Student.DoesNotExist:
            return Response({
                "message":"Student Not Found"
            },status=404)
        except Marks.DoesNotExist:
            return Response({
                "message":"Marks Not Found"
            },status=404)


@method_decorator(api_details("For api is for teacher/admin to view all marks,students "),name="dispatch")
class View_All_Marks(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdminOrTeacher
    ]
    def get(self, request):

        marks = Marks.objects.all()
        data = []
        for mark in marks:
            data.append({
                "student_id": mark.student.id,
                "student_name": mark.student.name,
                "reg": mark.student.reg,
                "school": {
                    "id": mark.school.id,
                    "name": mark.school.school_name},
                "marks": {
                    "tamil": mark.tamil,
                    "english": mark.english,
                    "maths": mark.maths,
                    "science": mark.science,
                    "social": mark.social},
                "total": mark.total,
                "avg": mark.avg
            })
        return Response(data)


@method_decorator(api_details("for export as a excel"),name="dispatch")
class ExportStudentExcel(APIView):
    permission_classes = [
        IsAuthenticated,
        IsAdminOrTeacher
    ]
    def get(self, request):
        members = Marks.objects.select_related(
            "student",
            "school"
        ).order_by("student__reg").values(
            "student__id",
            "student__name",
            "student__reg",
            "school__school_name",
            "tamil",
            "english",
            "maths",
            "science",
            "social",
            "total",
            "avg"
        )
        df = pd.DataFrame(members)
        response = HttpResponse( content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = ("attachment;"," filename=students.xlsx")
        df.to_excel( response,index=False )
        return response


@method_decorator(api_details("for export as a excel"),name="dispatch")
class UpdateByExcel(APIView):
    def post(self,request):
        permission_classes=[
            IsAuthenticated,
            IsAdminOrTeacher
        ]
        file=request.FILES.get("file")
        if not file:
            return Response({"error":"No file uploaded"},status=400)
        try:
            df=pd.read_excel(file)
            success_count=0
            failed_rows=[]
            for index,row in df.iterrows():
                try:
                    reg=row["reg"]
                    student=Student.objects.get(reg=reg)
                    marks=Marks.objects.get(student=student)
                    school=School.objects.get(id=row["school_id"])
                    error=[]
                    name=row["name"]
                    age=row["age"]
                    tamil=row["tamil"]
                    english=row["english"]
                    maths=row["maths"]
                    science=row["science"]
                    social=row["social"]
                    if pd.isna(name):
                        error.append("Name is invalid")
                    try:
                        age=int(age)
                        if age<1 or age>100:
                            error.append("Age is invalid")
                    except:
                        error.append("Age is invalid")
                    for subject,mark in {
                        "Tamil":tamil,
                        "English":english,
                        "Maths":maths,
                        "Science":science,
                        "Social":social
                    }.items():
                        try:
                            mark=float(mark)
                            if mark<0 or mark>100:
                                error.append(f"{subject} mark invalid")
                        except:
                            error.append(f"{subject} mark invalid")
                    if len(error)>0:
                        failed_rows.append({
                            "row":index+2,
                            "reg":reg,
                            "error":error
                        })
                        continue
                    total=tamil+english+maths+science+social
                    avg=total/5
                    student.name=name
                    student.reg=reg
                    student.age=age
                    student.school=school
                    student.save()
                    marks.school=school
                    marks.tamil=tamil
                    marks.english=english
                    marks.maths=maths
                    marks.science=science
                    marks.social=social
                    marks.total=total
                    marks.avg=avg
                    marks.save()
                    success_count+=1
                except Student.DoesNotExist:
                    failed_rows.append({
                        "row":index+2,
                        "reg":reg,
                        "error":"Student not found"
                    })
                except School.DoesNotExist:
                    failed_rows.append({
                        "row":index+2,
                        "reg":reg,
                        "error":"School not found"
                    })
                except Marks.DoesNotExist:
                    failed_rows.append({
                        "row":index+2,
                        "reg":reg,
                        "error":"Marks not found"
                    })
                except Exception as e:
                    failed_rows.append({
                        "row":index+2,
                        "reg":reg,
                        "error":str(e)
                    })
            return Response({
                "message":"Excel Updated Successfully",
                "success_count":success_count,
                "failed_count":len(failed_rows),
                "failed_rows":failed_rows
            })
        except Exception as e:
            return Response({"error":str(e) },status=400)


@method_decorator(api_details("for add student by excel"),name='dispatch')
class AddByExcel(APIView):

        def post(self, request):
            file = request.FILES.get("file")
            if not file:
                return Response({
                    "error": "No file uploaded"
                }, status=400)

            try:
                df = pd.read_excel(file)
                success_count = 0
                failed_rows = []
                for index, row in df.iterrows():
                    reg = ""
                    try:
                        reg = str(row["reg"]).strip()
                        name = row["name"]
                        age = row["age"]
                        school_id = row["school_id"]
                        tamil = row["tamil"]
                        english = row["english"]
                        maths = row["maths"]
                        science = row["science"]
                        social = row["social"]
                        username = reg.lower()
                        password = "12345"
                        if Student.objects.filter(reg=reg).exists():
                            failed_rows.append({
                                "row": index + 2,
                                "reg": reg,
                                "error": "Student already exists"
                            })
                            continue
                        if User.objects.filter(username=username).exists():
                            failed_rows.append({
                                "row": index + 2,
                                "username": username,
                                "error": "Username already exists"
                            })
                            continue
                        school = School.objects.get(
                            id=school_id
                        )
                        total = (
                                tamil +
                                english +
                                maths +
                                science +
                                social
                        )
                        avg = total / 5
                        user = User.objects.create_user(
                            username=username,
                            password=password
                        )
                        UserProfile.objects.create(
                            user=user,
                            role="student"
                        )
                        student = Student.objects.create(
                            user=user,
                            name=name,
                            age=age,
                            reg=reg,
                            school=school
                        )
                        Marks.objects.create(
                            student=student,
                            school=school,
                            tamil=tamil,
                            english=english,
                            maths=maths,
                            science=science,
                            social=social,
                            total=total,
                            avg=avg
                        )
                        success_count += 1
                    except School.DoesNotExist:
                        failed_rows.append({
                            "row": index + 2,
                            "reg": reg,
                            "error": "School not found"
                        })
                    except Exception as e:
                        failed_rows.append({
                            "row": index + 2,
                            "reg": reg,
                            "error": str(e)
                        })
                return Response({
                    "message": "Excel Processed Successfully",
                    "success_count": success_count,
                    "failed_count": len(failed_rows),
                    "failed_rows": failed_rows
                })
            except Exception as e:
                return Response({
                    "error": str(e)
                }, status=400)
