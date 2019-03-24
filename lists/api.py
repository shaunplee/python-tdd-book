import json
from django.http import HttpResponse
from lists.forms import ExistingListItemForm
from lists.models import List, Item

def list(request, list_id):
    list_ = List.objects.get(id=list_id)
    if request.method == 'POST':
        form = ExistingListItemForm(for_list=list_, data=request.POST)
        if (form.is_valid()) and (not(list_.owner) or
                                  (request.user == list_.owner) or
                                  (request.user in list_.shared_with.all())):
            Item.objects.create(text=request.POST['text'], list=list_)
            return HttpResponse(status=201)
        else:
            errors_dict = {'error': form['text'].errors[0]}
            return HttpResponse(json.dumps(errors_dict),
                                status=400,
                                content_type='application/json')
    item_dicts = [
        {'id': item.id, 'text': item.text}
        for item in list_.item_set.all()
    ]
    return HttpResponse(json.dumps(item_dicts),
                        content_type='application/json')
