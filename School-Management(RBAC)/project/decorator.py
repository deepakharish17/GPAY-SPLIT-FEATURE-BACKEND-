from functools import wraps
from django.utils import timezone
from .models import Decorator


def api_details(api_use):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = timezone.now()
            print("=" * 20)
            print(f"API name   : {func.__name__}")
            print(f"API Method : {request.method}")
            print(f"API Path : {request.path}")
            print(f"API use    : {api_use}")
            print(f"Start time : {start_time}")
            try:
                result = func(request,*args,**kwargs)
                status = "Success"

                if result.status_code >= 400:
                    status = "Failed"
                else:
                    status = "Success"
            except Exception as e:
                status = "Failed"
                print(f"Error: {str(e)}")
                raise
            finally:
                end_time = timezone.now()
                print(f"Status      : {status}")
                print(f"End time    : {end_time}")
                print(f"Duration    : {end_time - start_time}")
                print("=" * 20)
                duration = end_time - start_time

                Decorator.objects.create(
                    API_name=func.__name__,
                    API_Path=request.path,
                    API_Method=request.method,
                    API_use=api_use,
                    Start_time=start_time,
                    Status=status,
                    End_time=end_time,
                    Duration=duration
                )
            return result
        return wrapper
    return decorator


