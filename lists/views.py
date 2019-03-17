import bleach

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from lists.forms import ExistingListItemForm, ItemForm, NewListForm
from lists.models import Item, List

User = get_user_model()


def home_page(request):
    return render(request, 'home.html', {'form': ItemForm()})


def view_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    form = ExistingListItemForm(for_list=list_)
    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if form.is_valid():
            if (not(list_.owner) or
                (request.user == list_.owner) or
                (request.user in list_.shared_with.all())):
                Item.objects.create(text=request.POST['text'], list=list_)
            return redirect(list_)
    return render(
        request,
        'list.html',
        {'list': list_,
         'form': form})


def old_new_list(request):
    form = ItemForm(data=request.POST)
    if form.is_valid():
        list_ = List()
        if request.user.is_authenticated:
            list_.owner = request.user
        list_.save()
        form.save(for_list=list_)
        return redirect(list_)
    else:
        return render(request, 'home.html', {'form': form})


def new_list(request):
    form = NewListForm(data=request.POST)
    if form.is_valid():
        list_ = form.save(owner=request.user)
        return redirect(list_)
    return render(request, 'home.html', {'form': form})


def my_lists(request, email):
    owner = User.objects.get(email=email)
    return render(request, 'my_lists.html', {'owner': owner})


def share_list(request, list_id):
    list_ = List.objects.get(id=list_id)
    if request.method == 'POST':
        input_sharee_email = bleach.clean(request.POST['sharee'])
        try:
            sharee = User.objects.get(email=input_sharee_email)
            list_.shared_with.add(sharee.email)
        except:
            return render(
                request,
                'list.html',
                {'list': list_,
                 'share_error': user_not_found_string(input_sharee_email)})
    return redirect(list_)


def user_not_found_string(email):
    return f"User '{email}' not found."
