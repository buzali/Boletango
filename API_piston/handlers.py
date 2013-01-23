from piston.handler import BaseHandler
from piston.utils import rc
from Peliculas.models import *
from Peliculas.scrape_base import fechasSemana
from django.core.exceptions import ObjectDoesNotExist
from exceptions import ValueError
#from API.utils import filtra_complejo
from django.db import models



class ImagenHandler(BaseHandler):
	allowed_methods = ('GET',)	
	model = ImagenPelicula
	fields = ('imagen', 'width', 'height')

class PeliculaHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Pelicula
	fields = ('id', 'titulo', 'clasificacion', 'tags', 'sinopsis', 'actores', 'directores', 'duracion', 'tags', 'pais_origen', 'poster', 'fecha_agregado',
	 ('peli_ver_set', ('id', 'huella')), ('imagenes',(),) ,)
	search_fields = ['titulo', 'actores']
	
	def read(self, request, pelicula_id=None):
		base = Pelicula.objects
		if pelicula_id:
			try:
				p = base.get(pk=pelicula_id)
				return {'pelicula': p }
			except:
				return rc.NOT_FOUND
		else:
			#utiliza los params de GET para filtrar sino regresa todas
			s_dict = {}
			pelicula_qs = base
			complejos = Complejo.objects.all()
			#Filtra por locacion
			try:
				filtrados = filtra_complejos_request(request, complejos)[1] # El [1] es pq no me interesa saber si filtro o no
				#Filtra solo las peliculas que tienen funciones en los complejos filtrados.
				pelicula_qs = pelicula_qs.filter(peli_ver__funcion__complejo__in=filtrados).distinct()
			except:
				return rc.BAD_REQUEST				
			for s in self.search_fields:
				if s in request.GET:
					pelicula_qs = pelicula_qs.filter(**{s+'__icontains':request.GET[s]})
			return_d = [{'pelicula': p } for p in pelicula_qs.all()]
			return return_d

class ComplejoHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Complejo
	fields = ('id', 'nombre', 'direccion', 'cadena', 'telefonos_string', 'ciudad_m_id' )
	search_fields = ['nombre', 'cadena']

	def read(self, request, obj_id=None):
		base = Complejo.objects
		if obj_id:
			try:
				return base.get(pk=obj_id)
			except:
				return rc.NOT_FOUND
		else:
			complejos = Complejo.objects.all()
			#Filtra por locacion
			try:
				filtrados = filtra_complejos_request(request, complejos)[1] # El [1] es pq no me interesa saber si filtro o no
			except:
				return rc.BAD_REQUEST
				
			#filtra por otros params
			#utiliza los params de GET para filtrar sino regresa todas
			s_dict = {}
			for s in self.search_fields:
				if s in request.GET:
					filtrados = filtrados.filter(**{s+'__icontains':request.GET[s]})
			return_d = {}
			return_d['complejos'] =  filtrados.all()
			distancias = None
			#Si tiene distancias las agrega al dict
			if hasattr(filtrados, 'loc_dict'):
				return_d['distancias'] = filtrados.loc_dict
			#return_d.append({'distancias': distancias})
			return return_d;

class PeliVerHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Peli_ver
	fields = ('id','huella', 'pelicula_id')
	#@classmethod 
	#def pelicula_id(self, obj): 
	#	return obj.pelicula.id


class CiudadHandler(BaseHandler):
	allowed_methods = ('GET',)		
	model = Ciudad
	fields = ('nombre','id')
	def read(self, request):
		return [{'ciudad': c} for c in Ciudad.objects.all()]


class FuncionesHandler(BaseHandler):
	allowed_methods = ('GET',)
	model = Funcion
	fields = ('id', 'hora', 'complejo_id', 'peli_ver_id')
	@classmethod
	def read(self, request, modo=None, obj_id=None):		
		if modo == 'complejo':
			try:
				complejo = Complejo.objects.get(pk=obj_id)
			except ObjectDoesNotExist:
				return rc.NOT_FOUND
			
			peliculas = Pelicula.objects.filter(peli_ver__funcion__complejo=complejo).distinct()
			peli_vers = Peli_ver.objects.filter(funcion__complejo=complejo).distinct()
			
			funciones = {}
			#Crea diccionario con 'dia': {'peli_ver_id': funciones, 'peli_id_funciones': funciones} para toda la semana
			# for dia in fechasSemana(datetime.date.today()):
			# 	func_ver = {}
			# 	#Crea un diccionario con 'peli_ver_id': Funciones QS
			# 	for ver in peli_vers:
			# 		func_dia = Funcion.objects.filter(complejo=complejo, hora__contains=dia, peli_ver=ver)
			# 		if func_dia:
			# 			func_ver[ver.id] = func_dia
			# 	funciones[str(dia)] = func_ver
			#return {'funciones':funciones, 'peliculas':peliculas} #ORIGINAL
				
			#####################
			#Solo regresa las funciones de la semana... quick fix. seguro se puede hacer mejor
			funciones = []
			
			for dia in fechasSemana(datetime.date.today()):
				func_dia = Funcion.objects.filter(complejo=complejo, hora__year=dia.year, hora__month=dia.month, hora__day=dia.day)
				if func_dia:
					funciones.extend(func_dia)
			return {'peliculas': peliculas, 'funciones': funciones }
			#####################		
		elif modo == 'peli_ver':
			
			complejos = Complejo.objects.all()
			try:
				filtered, complejos_near = filtra_complejos_request(request, complejos)
			except:
				########### QUICK TEST ######### 
				pass #Deja que se pudan ver todas las funciones de esa peliver, esta mal debes cambiarlo
				################################
				
				########### BUENO ##############
				#return rc.BAD_REQUEST
				################################
				
			#Si no filtro nada regresa bad request
			
			########### QUICK TEST ######### 
			#if not filtered: return rc.BAD_REQUEST
			################################
			
			########### BUENO ##############
			#if not filtered: return rc.BAD_REQUEST
			################################
			
			try:
				peli_ver = Peli_ver.objects.get(pk=obj_id)
			except ObjectDoesNotExist:
				return rc.NOT_FOUND
			#ids de complejos q tienen esa peli Y estan cerca
			#complejo_ids = peli_ver.funcion_set.filter(complejo__in=complejos_near).values_list('complejo', flat=True).annotate()
			#complejos = Complejo.objects.filter().filter(pk__in=complejo_ids)
			complejos = Complejo.objects.filter(pk__in=complejos_near).filter(funcion__peli_ver=peli_ver).distinct()
			
			
			# funciones = {}
			# for dia in fechasSemana(datetime.date.today()):
			# 	func_comp = {}
			# 	for c in complejos:
			# 		func_dia = Funcion.objects.filter(complejo=c, hora__contains=dia, peli_ver=peli_ver)
			# 		if func_dia:
			# 			func_comp[c.id] = func_dia
			# 	if func_comp:
			# 		funciones[str(dia)] = func_comp
				
			#####################	
			#Solo regresa las funciones de la semana... quick fix. seguro se puede hacer mejor
			funciones = []
			for dia in fechasSemana(datetime.date.today()):
				func_dia = Funcion.objects.filter(complejo__in=complejos, hora__year=dia.year, hora__month=dia.month, hora__day=dia.day, peli_ver=peli_ver)
				if func_dia:
					funciones.extend(func_dia)
					
			return {'complejos': complejos, 'funciones': funciones }
			
			#return funciones
			###################
			
			
			#return {'funciones':funciones, 'complejos':complejos}#ORIGINAL
		else:
			return {'complejo': Complejo.objects.get(pk=1), 'pelicula': Pelicula.objects.get(pk=1)}


def filtra_complejos_request(request, qs):
	"""Busca en el request algun filtro y regresa un bool dependiendo si filtro y el qs de los complejos filtrados"""
	modos = ['ciudad', 'complejos', 'coord']
	comps_near = qs
	filtered = False
	for m in modos:
		if m in request.GET:
	#		try:
			comps_near = filtra_complejos(qs, m, request.GET[m])
			filtered = True
	return filtered, comps_near
	#		except e:
				
	#Si no encontro ningun parametro de filtro regresa todo
	#le agrego un esta variable para saber q no 
	#return filtered, qs
	
   
def filtra_complejos(qs, modo, rest):
	"""Filtra los complejos por el modo y la restriccion
	esta hardcodeado los 20 mas cercas en coordenada... alomejor vale la pena comabiarlo
	cuando coordenadas no estan ordenados!!
	"""
	comps = qs
	if modo and rest:
		if modo == 'ciudad':
			ciudad = Ciudad.objects.get(pk=rest)
			comps = comps.filter(ciudad_m=ciudad)
		elif modo == 'complejos':
			ids = rest.split(',')
			comps = comps.filter(pk__in=ids)
		elif modo == 'coord':
			lat, lon = rest.split(',')
			comps = Complejo.objects.near(float(lat), float(lon), 8)
		else:
			raise Exception('ModoInvalido')
	return comps
		