from django.shortcuts import render, redirect


def home(request):
    context = {'request': request}
    if not request.user.is_authenticated:
        return redirect('access')

    template = 'homepage.html'
    return render(request, template, context)


def index(request):
    context = {'request': request}
    if request.user.is_authenticated:
        return redirect('home')

    template = 'frontpage.html'
    return render(request, template, context)
