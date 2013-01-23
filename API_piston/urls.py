from django.conf.urls.defaults import *
from piston.resource import Resource
from API_piston.handlers import *

pelicula_handler = Resource(PeliculaHandler)
peliver_handler = Resource(PeliVerHandler)
complejo_handler = Resource(ComplejoHandler)
funciones_handler = Resource(FuncionesHandler)
ciudad_handler = Resource(CiudadHandler)

urlpatterns = patterns('',
	url(r'^complejo/$', complejo_handler),
	url(r'^complejo/(?P<obj_id>\d+)/funciones$', funciones_handler, {'modo': 'complejo'}),
	url(r'^complejo/(?P<obj_id>\d+)$', complejo_handler),
	#(r'^complejo/(?:(\D*)/(.*))?$', ),
	url(r'^ciudades/$', ciudad_handler),
	url(r'^peliver/(?P<obj_id>\d+)/funciones$', funciones_handler, {'modo': 'peli_ver'}),
	url(r'^peliver/(?P<id>\d+)', peliver_handler),
	url(r'^pelicula/(?P<pelicula_id>\d+)$', pelicula_handler,),
	url(r'^pelicula/$', pelicula_handler),
	#(r'^funciones/complejo/(?P<modo>\D*)/(?P<rest>.*)$', funcion_complejo),	
	#(r'^cerca/(.*)', cerca),		
	#url(r'^funciones/$', funciones_handler)
)