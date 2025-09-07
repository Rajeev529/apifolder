from django.shortcuts import render
from app.models import user_data
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

def signup1(request):
    from app.models import user_data
    if request.method == 'POST':
        uname = request.POST['uname']
        email = request.POST['email']
        p1 = request.POST['p1']
        p2 = request.POST['p2']
        
        # Check if username already exists
        try:
            u = user_data.objects.get(username=uname)
            return render(request, "signup.html", {"error": "Username already exists"})
        except user_data.DoesNotExist:
            pass  # Proceed if username doesn't exist
        
        # Check if email already exists
        try:
            e = user_data.objects.get(email=email)
            return render(request, "signup.html", {"error": "Email already exists"})
        except user_data.DoesNotExist:
            pass  # Proceed if email doesn't exist
        
        # Check if passwords match
        if p1 != p2:
            return render(request, "signup.html", {"error": "Passwords do not match"})
        
        # If all checks pass, create the user_data
        try:
            user_data = user_data.objects.create(username=uname, email=email, password=p1, balance=10.0).save()
            return render(request, "login.html", {"error": "Sign up successful"})
        except Exception as e:
            # Log the error or print it for debugging purposes
            return render(request, "signup.html", {"error": "Internal error: " + str(e)})

def login1(request):
    if request.method=='POST':
        un=request.POST['uname']
        p=request.POST['password']
        if(user_data.objects.get(username=un)):
            if(user_data.objects.get(username=un).password==p):
                request.session['username']=un
                request.session['flag']=True
                # return render(request,"admin.html")
                return redirect('/admin')
            else:
                return HttpResponseRedirect("password wrong")
        else:
            return HttpResponseRedirect("username does not exist")
    else:
        return HttpResponseRedirect("internal error")
    
# def create_api(request):

def logout(request):
    request.session.flush()
    return redirect("/")
    