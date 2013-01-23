from django.core import serializers
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson
from django.shortcuts import get_object_or_404, render_to_response
from django.db.models import Q, query
from datetime import datetime
from API.json import render_to_json
from itertools import groupby
from django.forms.models import model_to_dict
import time
import operator
from Peliculas.models import *   
from API.utils import *





## Complejo------------------------------------
def complejo_detail(request, id):
	"""Regresa JSON con info del complejo con id"""
	comp = get_object_or_404(Complejo,pk=id)
	return HttpResponse(jsonComplejo(comp))#, relations=('funcion',)))

def jsonComplejo(query, **opciones):
    """convierte el query a JSON solo con los fields especificados"""
    fields = fields_complejo
    return json(query, fields=fields, **opciones)


def complejo_list(request, modo=None, rest=None):
	"""Regresa JSON con lista de los complejos"""
	try:
		list = filtra_complejo(modo, rest)
	except Exception('ModoInvalido'):
		return HttpResponseBadRequest('ModoInvalido')
	qr = list
	if request.method == "GET":
		get = request.GET
		if "s" in get:
			qr = qr.filter(nombre__icontains=get['s'])
	if modo == 'coord':
		qr = ordena_dist_qs(qr)
	return render_to_json(qr)


## Ciudad----------------------------------------
def ciudad_list(request):
    qr = Ciudad.objects.all()
    if request.method == "GET":
        get = request.GET
        if "s" in get:
            qr = qr.filter(nombre__icontains=get['s'])
    return render_to_json(qr)





## Pelicula------------------------------------
def pelicula_detail(request, id):
    """Pelicula individual"""
    peli = get_object_or_404(Pelicula, pk=id)
    return HttpResponse(jsonPelicula(peli))

def pelicula_list(request, ciudad_string=None):
    """Regresa JSON con lista de los complejos"""
    list = Pelicula.objects.all()
    qr = list
    if request.method == "GET":
        get = request.GET
        if "s" in get:
            Qalt = Q(alt_tit__icontains=get['s'])
            Qorg = Q(titulo_org__icontains=get['s'])
            qr = qr.filter(Qalt | Qorg)
        if "tags" in get:
            qr = qr.filter(tag__icontains=get['tags'])
		
    return render_to_json(qr)			

def jsonPelicula(query, **opciones):
    """convierte el query a JSON solo con los fields especificados"""
    fields = fields_pelicula
    return json(query, fields=fields, **opciones)

## Funcion------------------------------------

def funciones(request,by=None, peli_id=None, modo=None, rest=None):
    """Regresa cada complejo con las funciones"""
    try:
        comps = filtra_complejo(modo, rest)
        logger.debug( modo)
        logger.debug( rest)
        logger.debug( len(comps))
    except:
        return HttpResponseBadRequest('ModoInvalido')
    #Filtra dia
    hoy = datetime.date.today()
    fecha = hoy
    if request.method == "GET":
        get = request.GET
        if "f" in get:
            f_str= get['f']
            if len(f_str) != 6: return HttpResponseBadRequest('FechaInvalida') #Fecha debe de ser de 6 digitos
            format = '%d%m%y'
            try:
                fecha = datetime.date(*time.strptime(f_str, format)[0:3])
            except:
                return HttpResponseBadRequest('FechaInvalida') 
	if by == 'complejo': #Cartelera de los complejos
		#logger.debug( comps[0].funcion_set.filter(hora__contains=fecha))
		horas =[{'Complejo': short(c),
        'Funciones':get_times(c.funcion_set.filter(hora__contains=fecha), 'pelicula'),
        } for c in comps]
		#Ordena por distancia y agrega distancia a c/complejo
		if modo == 'coord':
			ordena_dist(horas, comps.loc_dict)
		logger.debug( horas)
		#Acorta los complejos
		for h in horas:
			short_list(h['Funciones'], 'pelicula')
		logger.debug( horas)
                
	elif by == 'pelicula': #Funciones de esa peli en diferentes complejos
		logger.debug( 'by_peli')
		p = get_object_or_404(Peli_ver, pk=peli_id)
		horas ={'Pelicula': p,
        'Funciones':get_times(p.funcion_set.filter(hora__contains=fecha, complejo__in=comps), 'complejo'),
        }
		if modo == 'coord':
			ordena_dist(horas['Funciones'], comps.loc_dict)
			
        #Acorta los complejos
		short_list(horas['Funciones'], 'complejo')
		
		
		
	return render_to_json(horas)
