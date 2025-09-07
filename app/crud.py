import os
import shutil
from django.http import Http404
from django.shortcuts import render
from django.shortcuts import redirect
from app.models import user_data, API, Document, chats, Document2
import requests
from django.http import HttpResponseRedirect, JsonResponse
def editprompt(request):
    print(request.POST)
    if request.method== 'POST':
        name = request.POST['name']
        id = request.POST['id']
        desc = request.POST['desc']
        key1 = request.POST['key1']
        val1 = request.POST['val1']
        key2 = request.POST['key2']
        val2 = request.POST['val2']
        key3 = request.POST['key3']
        val3 = request.POST['val3']
        API.objects.filter(id=id).update(name=name, desc=desc, key1=key1, val1=val1, key2=key2, val2=val2, key3=key3, val3=val3)
        return JsonResponse({"result":"success"})


def edit(request, apikey):
    if request.session.get('flag')==True:
        data=API.objects.get(api_key=apikey)
        return render(request, 'editapi.html', {'data':data})
    return redirect('/login')


def deleteapi(request, apikey):
    try:
        # Get API entry
        api = API.objects.get(api_key=apikey)
        
        # Delete associated documents + their files
        data = Document.objects.filter(api_id=api.id)
        for doc in data:
            filepath = doc.file_path
            if os.path.exists(filepath):
                os.remove(filepath)
        data.delete()

        # Delete retriever folder if it exists
        retrpath = api.retriever_path  # e.g., "a8bf2e98-89fa-4b69-9d0b-bb0e36ffd64d"
        if retrpath and os.path.exists(retrpath):
            shutil.rmtree(retrpath)  # deletes folder + all files inside

        # Delete API entry
        api.delete()

        return JsonResponse({"result": "success"})
    except API.DoesNotExist:
        raise Http404("API not found")
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"result": "error", "message": str(e)}, status=500)

def delchat(request,apikey):
    chat=chats.objects.get(api_key=apikey)
    data=Document2.objects.filter(api=chat)
    for doc in data:
        filepath = doc.file_path
        if os.path.exists(filepath):
            os.remove(filepath)
    data.delete()

    retrpath=chat.retriever_path
    if retrpath and os.path.exists(retrpath):
        shutil.rmtree(retrpath)  # deletes folder + all files inside

    chat.delete()
    return HttpResponseRedirect('/alltables')
