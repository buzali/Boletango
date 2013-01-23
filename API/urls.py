from django.conf.urls.defaults import *
from API.views import *


urlpatterns = patterns('',
	(r'^complejo/(\d+)$', complejo_detail),
	(r'^complejo/(?:(\D*)/(.*))?$', complejo_list),
	(r'^ciudad/$', ciudad_list),
	(r'^pelicula/(\d+)$', pelicula_detail),
	(r'^pelicula/$', pelicula_list),
	#(r'^funciones/complejo/(?P<modo>\D*)/(?P<rest>.*)$', funcion_complejo),	
	(r'^funciones/(?P<by>pelicula|complejo)/(?:(?P<peli_id>\d+)/)?(?P<modo>\D*)/(?P<rest>.*)$', funciones),
	(r'^cerca/(.*)', cerca),		
)