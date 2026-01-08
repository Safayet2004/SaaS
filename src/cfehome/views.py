import pathlib
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.conf import settings

from visits.models import PageVisit

from allauth.account.views import LogoutView

LOGIN_URL = settings.LOGIN_URL

class CustomLogoutView(LogoutView):
    template_name = "account/logout.html"

this_dir = pathlib.Path(__file__).resolve().parent

def home_page_view(request, *args, **kwargs):


    print(request.user.is_authenticated, request.user)
    #A little confusion here
    qs = PageVisit.objects.all()
    queryset = PageVisit.objects.filter(path=request.path)
    path = request.path
    PageVisit.objects.create(path=request.path)
    
    my_title = "My Page"
    my_context = {
        "page_title" : my_title,
        "queryset": queryset.count(),
        "qs": qs.count(),
    }
    
    html_template = "home.html"
    return render(request, html_template, my_context)


def another_home_page_view(request, *args, **kwargs):
    html_file_path = this_dir / "home.html"
    html_ = html_file_path.read_text()
    
    return HttpResponse(html_)

VALID_CODE = "abc123"

def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
    
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        if user_pw_sent == VALID_CODE:
            is_allowed = 1
            request.session['protected_page_allowed'] = is_allowed

    if is_allowed:
        return render(request, "protected/view.html", {})
    return render(request, "protected/entry.html", {})

@login_required(login_url = LOGIN_URL)
def user_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {})


@staff_member_required(login_url = LOGIN_URL)
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {})