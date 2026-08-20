from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


# Create your views here.
def forms_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session['portal'] = 'forms'
            if user.is_superuser or (hasattr(user, 'userprofile') and user.userprofile.role == 'Admin'):
                return redirect("login:admin_appraisal_dashboard")
            return redirect("login:forms_dashboard")
        else:
            return render(request, "Login/forms_login.html", {"error": "Invalid credentials"})
    return render(request, "Login/forms_login.html")

@login_required
def upload_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('hris_csv')
        if not csv_file:
            return render(request, 'hriscsv/upload.html', {
                'error': 'Please select a CSV file to upload.',
            })
        try:
            csv_text = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return render(request, 'hriscsv/upload.html', {
                'error': 'File could not be read. Please upload a valid UTF-8 CSV file.',
            })

        if not csv_text.strip():
            return render(request, 'hriscsv/upload.html', {
                'error': 'The uploaded file is empty.',
            })

        from hriscsv.analyzer import analyze
        results = analyze(csv_text)
        results['filename'] = csv_file.name
        return render(request, 'hriscsv/results.html', results)

    return render(request, 'hriscsv/upload.html')
