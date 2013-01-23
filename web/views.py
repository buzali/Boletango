from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render_to_response
from django.db.models import Q, query
from datetime import datetime
from itertools import groupby
from django.forms.models import model_to_dict
import time
import operator
from Peliculas.models import *   


#restricted_fields = dict([(k, v) for k,v in object.items() if v.name not in keys])

def cerca(request, dire):
    list = filtra_complejo('coord', dire)
    list = ordena_dist_qs(list)
    list = [short(l) for l in list]
    return render_to_response('complejos.html', {'complejos': list, 'coord':dire} )
