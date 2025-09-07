from django.shortcuts import render
from django.shortcuts import redirect
from app.models import user_data, API, Document, chats
import requests
from app.var import LANGUAGES
from django.http import HttpResponseRedirect, JsonResponse
# request.session['username']=un
# request.session['flag']=True
# Create your views here.

def index(request):
    return render(request, "index.html")
def advo(request, apikey):
    try:
        if request.session['flag']==True:
            user=user_data.objects.get(username=request.session['username'])
            allchats=chats.objects.filter(user=user)
            # allmsg=allchats[1].data
            # print(allchats[1].data)
            return render(request, "advocate.html", {"chats": allchats, 'apikey': apikey})
    except:
        pass
    return redirect('/login')
def alltables(request):
    try:
        if request.session['flag']==True:
            user=user_data.objects.get(username=request.session['username'])
            allchats=chats.objects.filter(user=user)
            return render(request, "allchats.html", {"chats": allchats})
    except:
        pass
    return redirect('/login')

def upload_page(request):
    try:
        if request.session['flag']==True:
            return render(request, "upload.html", {"lang": LANGUAGES.items()})
    except:
        pass
    return redirect('/login')

def admin(request):
    if(request.session.get('flag')==True):
        un=request.session.get('username')
        data=user_data.objects.get(username=un)
        ratio=(data.balance/10)*100

        return render(request, "admin.html",{"data":data,"ratio":ratio})
    else:
        return redirect("/login")

def login(request):
    try:
        if request.session.get('flag')==True:
            return redirect("/admin")
    except:
        pass
    return render(request, "login.html")

def signup(request):
    return render(request, "signup.html")

def apiform(request):
    if request.session.get('flag')==True:
        return render(request, "apiform.html")
    else:
        return redirect("/login")

def table(request):
    if request.session.get('flag') == True:
        un = request.session.get('username')
        user = user_data.objects.get(username=un)

        # Get all APIs for that user
        all_apis = API.objects.filter(user=user)
        print(all_apis)
        # Get all documents linked to those APIs
        all_docs = Document.objects.filter(api__in=all_apis)

        return render(request, "tables.html", {"all_docs": all_docs, "all_apis": all_apis, "user":user})
    else:
        return redirect("/login")


def api2(request, apiKey):
        return render(request, "test.html",{"apikey":apiKey})



# import requests
# from django.http import JsonResponse




def findval(request):
    if request.method == 'GET':
        try:
            # Get API key and input from GET params
            apikey = request.GET.get('apikey')
            input_text = request.GET.get('inputText')

            if not apikey or not input_text:
                return JsonResponse({"error": "Missing parameters"}, status=400)

            print("Input text:", input_text)

            # Construct the internal API call
            url = f"http://127.0.0.1:8000/answer/{apikey}/"
            payload = {"query": input_text}
            res = requests.post(url, json=payload)

            print("Response:", res)

            if res.status_code == 200:
                return JsonResponse(res.json(), safe=False)
            else:
                return JsonResponse({"error": "Failed to get data from external API"}, status=res.status_code)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)