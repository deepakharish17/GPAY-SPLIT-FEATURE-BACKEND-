import  time

class RequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("Request-Started")
        print("Method:", request.method)
        print("Path:", request.path)
        Start_time = time.time()
        response = self.get_response(request)
        print("Request Ended")
        end_time=time.time()
        print(f"Request processed in {end_time - Start_time} seconds")
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Request successful")
        else:
            print("Request failed")
        print("="*20)

        return response
