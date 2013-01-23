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

#restricted_fields = dict([(k, v) for k,v in object.items() if v.name not in keys])

fields_pelicula = ('id', 'titulo', 'clasificacion', 'tags', 'sinopsis', 'actores', 'directores', 'duracion', 'tags', 'pais_origen', 'poster', 'fecha_agregado')
fields_complejo = ('id', 'nombre', 'direccion', 'cadena', 'telefonos_string' )

def cerca(request, dire):
    list = filtra_complejo('coord', dire)
    list = ordena_dist_qs(list)
    list = [short(l) for l in list]
    return render_to_response('complejos.html', {'complejos': list, 'coord':dire} )
     

## General--------------------------------------
def short(obj):
	"""Regresa un diccionario con algunos campos de la pelicula/complejo"""
	fields = None
	if type(obj) is Peli_ver:
		pelicula = obj.pelicula
		fields=('id', 'titulo_org', 'clasificacion', 'tags',)
		the_dict = model_to_dict(pelicula, fields=fields)
		the_dict['titulo'] = unicode(obj)
	elif type(obj) is Pelicula:
		fields = fields_pelicula
		the_dict = model_to_dict(obj, fields=fields)
	elif type(obj) is Complejo:
		fields= fields_complejo
		the_dict = model_to_dict(obj, fields=fields)
		if hasattr(obj, 'km'):
			the_dict['km'] = obj.km
			
	return the_dict

def short_list(list, by):
	"""Acorta todos los objetos Complejo/Pelicula de la lista de funciones """
	assert (by == 'pelicula') | (by == 'complejo') 
	if by == 'pelicula':
		by = 'peli_ver'
		label = 'Pelicula'
	else:
		label = 'complejo'
	by = by.capitalize()
	
	for h in list:
		h[label] = short ( h.pop(by))
	
#def just_keys(dict, keys):
#	"""Regresa el diccionario solo con las keys del argumento"""
#	a = {}
#	for k in keys:
#		if k in dict:
#			a[k] = dict[k]
#	return a

def json(query, **options):
    """Recibe un query y regresa su representacion en JSON"""
    return serializers.serialize("json", query, ensure_ascii =False, **options)






#restricted_fields = dict([(k, v) for k,v in object.items() if v.name not in keys])

## Complejo--------------------------------------

def filtra_complejo(modo, rest):
    """Filtra los complejos por el modo y la restriccion"""
    comps = Complejo.objects.all()
    if modo and rest:
        if modo == 'ciudad':
            ciu = get_object_or_404(Ciudad,pk=rest)
            comps = comps.filter(ciudad_m=ciu)
        elif modo == 'complejos':
            ids = rest.split(';')
            comps = comps.filter(pk__in=ids)
        elif modo == 'coord':
            lat, lon = rest.split(',')
            comps = Complejo.objects.near(float(lat), float(lon), 20)
        else:
            raise Exception('ModoInvalido')
    return comps

##Distancia-----------------------------------
def ordena_dist_qs(qs):
	"""Ordena querySet por distancia y regresa lista con dist (km) de cada complejo"""
	assert isinstance(qs, query.QuerySet) #Ordena querysets
	loc_dict = qs.loc_dict
	logger.debug(loc_dict)
	ordenado = list(qs)
	ordenado.sort( lambda x,y: cmp(loc_dict[x.id], loc_dict[y.id]  ) )
	#logger.debug( ordenado)
	#Agrega distancia
	for c in ordenado:
		km = loc_dict[c.id]
		c.km = km
	return ordenado

def ordena_dist(a_ordenar, loc_dict):
    """Pide distancias de complejos y ordena.
    Recibe un diccionario de donde ordena los complejos, y un loc_dict con las distancias de c/comp
    """
    #Ordena la lista por complejos, usando loc_dict que tiene la distancia de cada complejo
    a_ordenar.sort(lambda x,y: cmp(loc_dict[x['Complejo'].id], loc_dict[y['Complejo'].id]  )  )

    #Agrega la distancia a cada complejo
    for h in a_ordenar:
        c = h['Complejo']
        km= loc_dict[c.id]
        c.km = km

## Funcion------------------------------------
def get_times(query, by):
	""" Regresa una lista con obj pelicula/complejo y horas en base a los funciones de UN complejo.
	by define como ordenar y regresar los resultados.
	Si by es pelicula, regresa un grupo de peliculas y horas.
	Si by es complejo, regresa un grupo de complejos y horas.
	"""
	assert (by == 'pelicula') | (by == 'complejo') 
	if by == 'pelicula': by = 'peli_ver'
	q = query.order_by(by, 'hora').select_related()
	groups = []
	objs= []
	for k, g in groupby(q, operator.attrgetter(by)):
		groups.append([h.hora.time() for h in g]) #Grupo de funciones
		objs.append(k) #Pelicula o Complejo por cada grupo
	return [{	by.capitalize() :objs[i], 'Times': groups[i]} for i in range(len(objs)) ]
