from django.db import models
import datetime
import re

import geopy.distance
from geopy import geocoders

class LocationManager(models.Manager):
    def __init__(self):
        super(LocationManager, self).__init__()
        
    #def near_dict(self, latitude=None, longitude=None, distance=None):
    #    """ Regresa un diccionario con [id]= km """
    #    if not (latitude and longitude and distance):
    #        return []
    #
    #    o_queryset = super(LocationManager, self).get_query_set()
    #    queryset = o_queryset
    #    # prune down the set of all locations to something we can quickly check precisely
    #    #rough_distance = geopy.distance.arc_degrees(arcminutes=geopy.distance.nm(km=distance)) * 2
    #    #queryset = queryset.filter(
    #    #      latitude__range=(latitude - rough_distance, latitude + rough_distance), 
    #    #      longitude__range=(longitude - rough_distance, longitude + rough_distance)
    #    #      )
    #    #
    #    locations = {}
    #    queryset = queryset.exclude(dir_lat='')
    #    for location in queryset:
    #        if location.latitude and location.longitude:
    #            exact_distance = geopy.distance.distance(
    #            (latitude, longitude),
    #            (location.latitude, location.longitude)
    #            )
    #            if exact_distance.km <= distance:
    #                locations[location.id]= exact_distance.km
    #    return locations
    #    #close_locations = sorted(locations, lambda x,y: cmp(x['km'], y['km']))[:10] 
    #    #return close_locations
    
    def near(self, latitude=None, longitude=None, distance=None):
        """ Regresa queryset con los complejos dentro de la distancia distance.
        No hay forma de ordenar el queryset.
        """
        if not (latitude and longitude and distance):
            return []
        queryset = super(LocationManager, self).get_query_set()
        # prune down the set of all locations to something we can quickly check precisely
        #rough_distance = geopy.distance.arc_degrees(arcminutes=geopy.distance.nm(km=distance)) * 2
        #queryset = queryset.filter(
        #      latitude__range=(latitude - rough_distance, latitude + rough_distance), 
        #      longitude__range=(longitude - rough_distance, longitude + rough_distance)
        #      )
        #
        locations = []
        loc_dict = {}
        queryset = queryset.exclude(dir_lat='')
        for location in queryset:
            if location.latitude and location.longitude:
                exact_distance = geopy.distance.distance(
                (latitude, longitude),
                (location.latitude, location.longitude)
                )
                if exact_distance.km <= distance:
                    loc_dict[location.id]= round(exact_distance.km, 2)
                    locations.append(location)
        queryset = queryset.filter(id__in=[l.id for l in locations])
        queryset.loc_dict= loc_dict
        return queryset

class Pelicula(models.Model):
    titulo = models.CharField(max_length=150)
    titulo_org = models.CharField(max_length=50, blank=True, default="")
    alt_tit = models.CharField(blank=True, max_length=500)
    clasificacion = models.CharField(max_length=5, blank=True, default="")
    sinopsis = models.TextField(blank=True, default="")
    actores = models.TextField(blank=True, default="")
    directores = models.TextField(blank=True, default="")
    duracion = models.CharField(max_length=50, blank=True, default="")
    tags = models.CharField(max_length=50, blank=True, default="")
    pais_origen = models.CharField(blank=True, max_length=50)
    poster = models.CharField(max_length=100, blank=True, default="")
    fecha_agregado = models.DateTimeField(blank=True, null=True, auto_now_add=True) #checar auto_nows
    
    def slug(self):
        """regresa el titulo sin acentos o espacios."""
        import unicodedata
        sin_acento = unicodedata.normalize('NFKD', unicode(self.titulo)).encode('ASCII', 'ignore')
        titulo = sin_acento.replace(' ', '-').strip().lower()
        return titulo
		
    def __unicode__(self):
        return self.titulo

    class Meta:
        ordering = ('titulo',)

class ImagenPelicula(models.Model):
	"""Guarda Imagen de pelicula"""
	pelicula = models.ForeignKey(Pelicula, related_name='imagenes')
	imagen = models.ImageField(upload_to="imagenes")
	url_org = models.CharField(blank=True, max_length=100) #url original de archivo
	width = models.IntegerField(blank=True, null=True)
	height = models.IntegerField(blank=True, null=True)

	def __unicode__(self):
		return u"ImagenPelicula %s" %self.id



class Peli_ver(models.Model):
	"""Se crea uno de estos por cada version de la pelicula ej. Doblada, Sub, 3D, etc"""
	pelicula = models.ForeignKey(Pelicula, )
	id_pol = models.IntegerField(blank=True, null=True) #id cineticket
	id_cineticket = models.IntegerField(blank=True, null=True)
	id_mex = models.IntegerField(blank=True, null=True) #id cinemex
	id_mark = models.IntegerField(blank=True, null=True) #id cinemark
	mex_vc = models.IntegerField(blank=True, null=True)
	subtitulada = models.BooleanField(default=False)
	doblada = models.BooleanField(default=False)
	tres_D = models.BooleanField(default=False)
	digital = models.BooleanField(default=False)
	imax = models.BooleanField(default=False)
	xe = models.BooleanField(default=False)
	#Si agregas otra propiedad, no se te olvide actualizar la huella y el filter_peli_ver en scrape_base
	@property
	def huella(self):
		"""regresa un string con las caracteristicas q tiene esa version, en este orden. sub,dob,tres_D,digital,imax, xe"""
		return "%d%d%d%d%d%d" %(self.subtitulada,self.doblada,self.tres_D,self.digital,self.imax, self.xe)
	def __unicode__(self):    
		suf = u''
		if self.subtitulada:
			suf += u' (S)'
		if self.doblada:
			suf += u' (D)'
		if self.tres_D:
			suf += u' (3D)'
		if self.digital:
			suf += u' (Digital)'
		if self.imax:
			suf += u' (IMAX)'
		if self.xe:
			suf += u' (XE)'
		return self.pelicula.titulo + suf
		
	#class Meta:
	#	ordering = ('pelicula__titulo',)

		


class Ciudad(models.Model):
	"""Une las ciudades de los diferentes cines"""
	nombre = models.CharField(max_length=100)
	id_mex = models.IntegerField(blank=True, null=True)
	id_pol = models.IntegerField(blank=True, null=True)
	id_mark = models.IntegerField(blank=True, null=True)
	def __unicode__(self):
		return self.nombre
	def natural_key(self):
		return self.nombre
	class Meta:
		ordering = ['nombre']
		verbose_name_plural = "Ciudades"

class Complejo(models.Model):
	objects = LocationManager()
	ciudad_m = models.ForeignKey(Ciudad, blank=True, null=True)
	id_org = models.IntegerField() #id que utiliza el cine
	id_ciudad = models.IntegerField(null=True, blank= True) #id de la ciudad cinepolis
	nombre = models.CharField(max_length=50)
	direccion = models.TextField( blank= True)
	dir_lat = models.CharField('latitud', max_length=50, blank=True)
	dir_lat.custom_filter_spec = True
	dir_long = models.CharField('longitud', max_length=50, blank=True)
	latitude = models.FloatField(blank=True, null=True)
	longitude = models.FloatField(blank=True, null=True)
	loc_aprox = models.BooleanField(default=False)
	loc_exact = models.BooleanField(default=False)
	cadena = models.CharField(max_length=50, blank=True)
	telefonos_string = models.TextField( blank= True)
	calle = models.CharField(max_length=50, blank= True)
	ciudad =  models.CharField(max_length=50, blank= True)
	estado =  models.CharField(max_length=50, blank= True)
	CP = models.IntegerField(null=True, blank= True)
	# telefono1 = models.IntegerField(null=True, blank= True)
	# telefono2 = models.IntegerField(null=True, blank= True)
	# telefono3 = models.IntegerField(null=True, blank= True)
	telefono1_str = models.CharField(blank=True, max_length=100)
	telefono2_str = models.CharField(blank=True, max_length=100)
	telefono3_str = models.CharField(blank=True, max_length=100)
    #precios
	def __unicode__(self):
		return self.nombre	
	def mex_nombre(self):
		"""regresa el nombre sin acentos o espacios. Usado para los URL de cinemex"""
		import unicodedata
		sin_acento = unicodedata.normalize('NFKD', unicode(self.nombre)).encode('ASCII', 'ignore')
		nombre = sin_acento.replace('Cinemex', '')
		return nombre.replace(' ', '').strip().lower()
		
	class Meta:
		ordering = ('nombre',)


class Funcion(models.Model):
	peli_ver = models.ForeignKey(Peli_ver, default=None)
	complejo = models.ForeignKey(Complejo)
	hora = models.DateTimeField()
	sala = models.IntegerField(null=True, blank=True)
	pol_idShowTime = models.IntegerField(null=True, blank=True)
	class Meta:
	    verbose_name_plural='Funciones'
	
	def __unicode__(self):
		return u'%s --  %s -- %s -- Sala: %s' % (self.peli_ver, self.complejo.nombre, self.hora, self.sala)