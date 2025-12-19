import pathlib
from django.http import HttpResponse
from django.shortcuts import render

from visits.models import PageVisit

this_dir = pathlib.Path(__file__).resolve().parent

def home_page_view(request, *args, **kwargs):
    
    
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