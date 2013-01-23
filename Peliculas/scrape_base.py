#!/usr/bin/env python
# encoding: utf-8
"""
scrape_base.py

Created by Tofi Buzali on 2009-08-15.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.

Contiene las funciones comunes para scraping

"""
import time, re, os
import unicodedata
from datetime import date, datetime, timedelta
from models import *
from django.core.files import File
from urllib import urlretrieve
import locale

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def to24Hour(time):
	"""
	Recibe una hora en formato 12h ej. 2:20pm y la convierte a 24h ej 14:20
	"""
	time_list = re.search(r'(\d\d?):(\d\d)\s*(?i)(am|pm)', time)
	if time_list:
		hour = int(time_list.group(1))
		mins = int(time_list.group(2))
		ampm = time_list.group(3)
		ampm = ampm.lower()
		
		assert hour < 13 
		assert hour > 0
		if hour == 12 and ampm == 'am':
			hours = 0
		elif hour == 12 and ampm == 'pm':
			hours = 12 
		elif ampm == 'pm':
			hour += 12	
		return '%d:%.2d' % (hour, mins)
	


def parseDate(date_string):
	"""Recibe una fecha como 'Lunes 27 de agosto' y regresa un obj datetime.date"""

	#Ajusta el lenguage para poder parsear las fechas q estan en espanol
	locale.setlocale(locale.LC_TIME, "es_ES")
	exp = re.compile(r'(\d{1,2} de \D+)$')
	try:
		string = exp.search(date_string.strip()).group(1)
	except:
		logger.debug( 'Hay un error con la fecha')
		return ''

	format = '%d de %B'
	hoy = datetime.date.today()

	fecha = datetime.date(hoy.year, *time.strptime(string, format)[1:3])
	return fecha

def fechasSemana(hoy= date.today()):
	"""Regresa los 7 fechas del viernes pasado al siguiente viernes. empezando en la variable hoy"""
	#hoy = date.today()
	a_viernes = hoy.weekday() - 4
	if hoy.weekday() < 4 :a_viernes += 7
	
	viernes = hoy - timedelta(days=a_viernes) #El viernes pasado
	dias = [
			viernes + timedelta(days=i) for i in range(0,7) 
			]
	return dias


def fechasFines():
	"""Regresa los sabados y domingos de la semana"""
	fines = []
	for fecha in fechasSemana():
		if fecha.weekday() == 6 or fecha.weekday() == 5:
			fines.append(fecha)
	return fines
	
def fechasDias():
	"""Regresa las fechas q no sean sabados o domingos"""
	dias = []
	for fecha in fechasSemana():
		if fecha.weekday() != 6 and fecha.weekday() != 5:
			dias.append(fecha)
	return dias

def objToDict(obj):
	"""Convierte el obj en diccionario, si el obj es dic, lo deja igual"""
	if type(obj) == dict:
		return obj
	else:
		try:
			return vars(obj)
		except Exception, e:
			logger.debug( 'error convirtiendo %s en diccionario' % obj)
			raise e
	

def merge(obj, obj2):
	"""Cambia los atributos del objeto q estan vacios pero si estan en el diccionario,
	El primer parametro es un obj,
	obj2 puede ser objeto o dict
	
	"""
	#Asegura q obj sea pelicula, complejo o funcion
	assert isinstance(obj,(Pelicula,Complejo, Funcion, Peli_ver))
	
	d_dict = objToDict(obj2)
			
	#iterate through dic fields
	for k, v in vars(obj).items():
		#if k field is empty and dict has k info, update peli
		if (v == None or v == '') and d_dict.get(k, None):	setattr(obj, k, d_dict[k])
	obj.save()
	return obj



def strip_accents(s):
   return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def join_peli_num(pk1,pk2):
    """join pelicula por numero"""
    #try:
    join_peliculas(Pelicula.objects.get(pk=pk1),Pelicula.objects.get(pk=pk2))
    #except:
    #    logger.debug( 'No se encontraron las peliculas')

 
def join_peliculas(peli1, peli2):
    """
    Para las peliculas que tienen nombres diferentes, une las dos en un solo obj
    Agrega el nombre de peli2 a alt_tit y elimina peli2
    """	
    #Verificar q las dos sean obj pelicula...
    
    
    #El [1:] es para que no copie el primer |
    for alt in peli2.alt_tit[1:-1].split('|'):
        if  peli1.alt_tit.lower().find('|'+ alt.lower() + '|') < 0: peli1.alt_tit += alt + '|'
        
    #hacer merge de peli1 y peli2
    merge(peli1,peli2)
            
    #Cambia y hace merge de las vers relacionados con peli2 a peli1
    vers = []
    #Checa las ver que hay, si existe una con la misma huella, hace merge, sino namas asigna pelicula a ver
    for ver2 in peli2.peli_ver_set.all():
        nueva_ver = None
        for ver1 in peli1.peli_ver_set.all():
            if ver2.huella == ver1.huella:
                nueva_ver = merge(ver2,ver1)
                ver1.delete()
        if not nueva_ver:
            nueva_ver = ver2
        vers.append(nueva_ver)
    #para no alterar a peli2.peli_ver_set_all, cambio a peli1 al final
    for v in vers:
        v.pelicula=peli1
        v.save()
        
        
    #Verificar q no halla nada relacionado con peli2
    assert len(peli2.peli_ver_set.all()) == 0
    peli2.delete()
    peli1.save()
    return peli1



def existePelicula(peli_dict):
    """Regresa True o False dependiendo si existe la pelicula en la BD	"""
    tit = '|'+ peli_dict['titulo'] + '|'
    qs = Peli_ver.objects.filter(pelicula__alt_tit__icontains=tit, subtitulada=peli_dict.get('subtitulada', False), doblada=peli_dict.get('doblada', False), tres_D=peli_dict.get('tres_D', False))
    if not qs:
        return False
    else:
        return True


def createPelicula(peli_dict):
	"""Verifica que no exista una pelicula con ese titulo y la crea.
	Si ya existe la pelicula, hace un merge.
	Regresa el obj y si fue creado. 
	"""
	creado = False
	
	tit = '|'+ peli_dict['titulo'] + '|'
	#Extrae de peli_dict y crea peli_ver
	atts = Peli_ver._meta.get_all_field_names() #Saca todos los fields de Peli_ver
	atts.remove('pelicula')
	ver_dict = {}
	for k in atts:
		att=peli_dict.pop(k, None)
		#Solo deja los que son True o algun valor, sino pondria False en campos int como id_pol
		if att: ver_dict[k]=att
	ver = Peli_ver(**ver_dict)
    
	#Saca info de imagenes
	img_urls = peli_dict.pop('img_urls', None)
	
	obj, created = Pelicula.objects.get_or_create(alt_tit__icontains=tit, defaults=peli_dict )
	
	if created: 
		obj.alt_tit = tit
		ver.pelicula=obj
		ver.save()
		obj.save()
		creado = True
	else:
		obj = merge(obj,  peli_dict)
		obj.save()
		
		nueva_ver = None
		#Checa las ver que hay, si existe una con la misma huella, hace merge, sino namas asigna pelicula a ver
		for la_ver in obj.peli_ver_set.all():
			if ver.huella == la_ver.huella:
				nueva_ver = merge(ver,la_ver)
				
		if not nueva_ver:
			ver.pelicula=obj
			nueva_ver = ver
		nueva_ver.save()
		
		ver.pelicula=obj
		ver.save()
		creado = False
		
	#Pide imagenes y agrega a esa peli
	for url in img_urls:
		img, created = ImagenPelicula.objects.get_or_create(pelicula=obj, url_org=url)
		if created:
			try:
				img_file = retrieveImagen(url)
			except:
				img.delete()
				img = None
				logger.error("Error cargando imagen %s" %url)
				continue
			img.imagen = img_file
			basename, extension = os.path.splitext(url)
			if not extension:
				img.delete()
				continue
			img.imagen.name = u"%s_%d%s" %(obj.slug(), img.imagen.width, extension)
			img.width = img.imagen.width
			img.height = img.imagen.height
			img.save()
			logger.debug("Creted image %s" %img.imagen.name)
	
	return obj, creado

	
def retrieveImagen(url):
	"""Pide url de internet y regresa obj File"""
	filename, headers = urlretrieve(url)
	f = open(filename)
	file_o = File(f)
	return file_o
		
		

def createPeliculaVIEJO(self):
    tit = '|'+ peli_dict['titulo'] + '|'
    qs = Pelicula.objects.filter(alt_tit__icontains=tit, subtitulada=peli_dict.get('subtitulada', False), doblada=peli_dict.get('doblada', False), tres_D=peli_dict.get('tres_D', False))
    if not qs:
        #Asigna el alt_tit
        peli_dict['alt_tit'] = tit
        #Crea el obj
        p = Pelicula.objects.create(**peli_dict)
    else:
        peli = qs[0]
        peli = merge(peli, peli_dict)
        peli.save()



def createComplejo(complejo_dict):
    """Actualiza o crea nuevo complejo"""
    comp = Complejo.objects.get_or_create(id_org=complejo_dict['id_org'], cadena=complejo_dict['cadena'])[0] #solo el obj sin bool
    for key,value in complejo_dict.items():
        setattr(comp, key, value)
    comp.save()


def createFuncion(funcion_dict):
	"""Verifica que no exista el funcion, busca las relaciones y crea el objeto"""
	kwargs = {'peli_ver': funcion_dict['peli_ver'], 'complejo':funcion_dict['complejo'], 'hora':funcion_dict['hora']}
	funcion = Funcion.objects.get_or_create(**kwargs)[0]
	for key,value in funcion_dict.items():
		setattr(funcion, key, value)
	funcion.save()


def stripTit(titulo):
	"""Quita sufijos de subtitulada, etc (S), (D), (3D)"""
	titulo = titulo.replace(' (S)', '')
	titulo = titulo.replace(' (D)', '')
	titulo = titulo.replace(' (3D)', '')
	titulo = titulo.replace(' (Digital)', '')
	titulo = titulo.replace(' (IMAX)', '')
	titulo = titulo.replace(' (XE)', '')
	
	return titulo
    

def corrigeSub():
    """Busca todas las peliculas y si solo existe subtitulada le quita la S"""
    for peli in Peli_ver.objects.filter(subtitulada=True):
		tit = '|'+ peli.pelicula.titulo + '|'
		qs = Peli_ver.objects.filter(pelicula__alt_tit__icontains=tit, tres_D=peli.tres_D, digital=peli.digital, imax=peli.imax, xe=peli.xe, subtitulada=False)
		#Si no existe pelicula doblada
		if (not qs.filter(doblada=True)) and qs:
			assert len(qs) == 1
			peli.subtitulada = False
			corregida=  merge(peli, qs[0])
			corregida.save()
			qs[0].delete()
			logger.debug( corregida)
		

def copyAddress(uno,dos):
	"""copy addresses and phones from a to b"""
	a= Complejo.objects.get(pk=uno)
	b= Complejo.objects.get(pk=dos)
 	strings = ('dir_lat', 'dir_long', 'calle', 'ciudad', 'estado', 'CP', 'telefono1', 'telefono2', 'telefono3', 'loc_exact', 'loc_aprox')
	for att in strings:
		dato = getattr(a, att)
		setattr(b, att,dato)
		b.save()
#			
#			
#Arregla dir_lat
def arregla_dir_lat():
    a = Complejo.objects.exclude(dir_lat='').filter(latitude=0)
    for comp in a:
        lat, lon = comp.dir_lat.split(',')
        comp.latitude = float(lat)
        comp.longitude = float(lon)
        comp.save() 




def filter_peli_ver(*args, **kwargs):
	"""Hace un get de peli_ver tomando False como default para params como digital, imax, xe"""
	params = ['tres_D', 'digital', 'imax', 'xe']
	for p in params:
		if p not in kwargs:
			kwargs[p]=False
	return Peli_ver.objects.filter(*args, **kwargs)