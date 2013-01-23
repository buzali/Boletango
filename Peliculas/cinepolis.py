"""
cinepolis.py

Created by Tofi Buzali on 2009-08-15.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.

Funciones necesarias para hacer el scraping de cinepolis


"""
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, NavigableString
import  time, re
from urllib2 import urlopen
from datetime import date, datetime, timedelta
from models import *
from scrape_base import *



#Pelicula

def updatePeliculas():
	"""Jala datos de cada pelicula en cinepolis y lo agrega a la BD"""
	#xml_peliculas = "http://www.cinepolis.com.mx/pelicula/xml/peliculasxml.aspx"
	
	#xml = urlopen(xml_peliculas)
	url_index = 'http://cinepolis.com/index.aspx'
	index_html = urlopen(url_index)
	
	#ids = parse_peliculasxml(xml)
	ids = scrape_peliculasindex(index_html)
	
	base_url_pelicula = "http://www.cinepolis.com.mx/cartelera/aspx/pelicula.aspx?ip=%s"
	
	for peli_data in ids:
		url = base_url_pelicula % (peli_data['id_pol'])
		try:
			peli_html = urlopen(url)
		except:
			logger.debug( 'error al intentar cargar la pag %s' %url)
			continue
		pelicula = scrape_pelicula(peli_html, peli_data)
		createPelicula(pelicula)


def scrape_peliculasindex(index_html):
	"""Saca lista de pelis de index"""
	soup = BeautifulSoup(index_html)
	peli_list = soup.find('div', 'divComboPelicula2').findAll('option', selected=None)
	ids = [{'titulo': peli.text,
			'id_pol': peli['value']}
			for peli in peli_list]
	return ids
	
	
def parse_peliculasxml(data):
	parser = BeautifulStoneSoup(data)
	ids = [{'titulo': peli.nombre.string,
			'id_pol': peli.id.string,
			'id_cineticket': peli.idcineticket.string}
			for peli in parser.findAll('pelicula')]
	return ids

		
def scrape_pelicula(data, peli_data):
	"""docstring for scrape_pelicula"""
	p_data = peli_data
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	
	string_ids = {'titulo': 'lbltitulo','titulo_org': 'lbltitulooriginal', 'clasificacion': 'lblclasificacion', 'directores': 'lbldirector', 'duracion': 'lblduracion', 'tags': 'lblgenero' } 
	for k, v in string_ids.items():
		p_data[k] = unicode(soup.find(id=v).string).strip()
		
	p_data['actores'] = u''.join(soup.find(id='lblactores').findAll(text=True)).replace('\n','')
	p_data['sinopsis'] = u''.join(soup.find('table', width=530).span.findAll(text=True)).replace('\n',' ')
	img_url = soup.find('td', width=117, height=170)['background'].strip()
	if img_url:
		p_data['img_urls'] = (img_url.replace('../../..', 'http://www.cinepolis.com.mx'),)
 	
	
	
	#Corregir subtitulada, etc
	cambios, titulo = corrigeTitulo(p_data['titulo'])
	if cambios:
		p_data['titulo'] = titulo
		for c in cambios:
			p_data[c] = True #Pone como true el campo especial eg. Subtitulada 
	
    #string_array_ids = {'actores': 'lblactores', 'sinopsis':  } #etc...
    #for k, v in string_array_ids:
    #    parts = soup.find(peli_list=v).findAllNext(text=True)
    #    data[k] = ''.join(parts).replace('\n', '')
	
	return p_data


def corrigeTitulo(titulo):
	"""Checa el titulo por subtitulada o doblada y regresa el titulo corregido y una clave en caso de q cambia"""
	find_for = {' Sub': 'subtitulada' ,  ' 3D' : 'tres_D', '[Digital 3D]' :'tres_D',' Dob': 'doblada' , ' Dig':'digital', ' XE':'xe', ' Imax':'imax' }
	cambios = []
	
	for k, v in find_for.items():
		found = titulo.find(k)
		if found > 0:
			titulo = titulo.replace(k,'').strip()
			cambios.append(v)
	
	return cambios, titulo
			



#Complejos

def updateComplejos():
    """Jala datos de cada complejo de cinepolis y lo agrega a la BD"""
    xml_complejos = "http://www.cinepolis.com.mx/xml/complejos.xml"
    xml_ciudades = "http://www.cinepolis.com.mx/Aspx/xml/CiudadesXml/CiudadesXml.aspx?pais=1"
    
    xml = urlopen(xml_complejos)
    ids = parse_complejosxml(xml)
    
    ciudades = parse_ciudadesxml( urlopen(xml_ciudades) )#Diccionario de ciudades de Mexico
    
    
    base_url_complejo = "http://www.cinepolis.com.mx/cartelera/aspx/complejoinfo.aspx?plaza=%s&ciudad=%s"
    
    for comp_id in ids:
        #logger.debug( comp_id['id_org'])
        if comp_id['id_ciudad'] in ciudades: #verifica que la ciudad sea de mexico
            url = base_url_complejo % (comp_id['id_org'], comp_id['id_ciudad'])
            comp_html = urlopen(url)
            complejo =scrape_compInfo(comp_html, comp_id)
            createComplejo(complejo)
			


def parse_complejosxml(data):
	"""regresa un diccionario con 'id': 'nombre complejo'"""
	parser = BeautifulStoneSoup(data)
	ids = [{'id_org': complejo.id.string,
			'id_ciudad': complejo.idc.string,
			'nombre': complejo.nombre.string}
			for complejo in parser.findAll('complejo')]
	return ids


def parse_ciudadesxml(data):
	"""regresa un diccionario con 'id': 'nombre ciudad'"""
	parser = BeautifulStoneSoup(data)
	ciudades = {}
	for ciudad in parser.findAll('ciudad'):
		ciudades[ciudad.id.string] = ciudad.nombre.string
	
	return ciudades


def scrape_compInfo(data, comp_id):
	"""Agrega al diccionario recibido direccion y telefonos by scraping la info de data"""
	c_data = comp_id # id_org, id_ciudad y nombre de xml
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	
	string_ids = {'direccion': 'lbldireccion', 'telefonos_string': 'lbltelefonos'} 
	for k, v in string_ids.items():
		c_data[k] = ''.join(soup.find(id=v).findAll(text=True)).replace('\n','')
	
	c_data['cadena']='Cinepolis'
	
	return c_data

		



#Funciones

def updateFunciones(*args, **kwargs):
	return updateFuncionesAsp(*args, **kwargs)


def updateFuncionesAsp():
	"""Actualiza los funciones de la pag normal"""
	base_url_cartelera = "http://www.cinepolis.com.mx/cartelera/aspx/carteleras_.aspx?ci=%s&fecha=%s" #id_ciudad, fecha aaaammdd
	ciudades = Complejo.objects.filter(cadena='Cinepolis').order_by('id_ciudad').values_list('id_ciudad', flat=True).annotate()
	
	
	for fecha in fechasSemana():#[date.today(),]:#
		fecha_str = fecha.strftime('%Y%m%d')
		for id_ciudad in ciudades:
			url = base_url_cartelera % (id_ciudad, fecha_str)
			try:
				html = urlopen(url)
			except:
				logger.debug( 'error al cargar la pag %s' %url)
				continue
			try:
				funciones = scrape_funcionesAsp0811(html, fecha, id_ciudad)
				
				for hora in funciones:
					createFuncion(hora)
			except Exception, e:
				logger.debug( 'Error al scrapear cartelera cinepolis ciudad %s, url: %s' %(id_ciudad, url))
				logger.debug( e)




def scrape_funcionesAsp0811(data, fecha, id_ciudad):
	"""scrape de la cartelera normal
	regresa lista de diccionarios:
	{
	'peli_ver': pelicula,
	'complejo': complejo,
	'hora': datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora_str , '%H:%M')[3:5]),
	'pol_idShowTime': id_show,
	}
	"""
	funciones = []
	
	complejo_actual = None
	peli_exp = re.compile(r'ip=(\d+)')
	comp_exp = re.compile(r'Cine(\d*)')
	complejo = None
	
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	
	peliculas = soup.findAll('a', href=peli_exp)
	for peli in peliculas:
		comp_a= peli.findPrevious('a', id=comp_exp)
		comp_id = comp_exp.search(comp_a['id']).group(1)
		if complejo_actual != comp_id:
			complejo_actual = comp_id
			complejo = None
			try:
				complejo = Complejo.objects.get(id_org=comp_id, cadena='Cinepolis')
			except:
				logger.debug( 'No se encontro complejo:%s de ciudad: %s' % (comp_id, id_ciudad))
				continue
		#Si no encontro el complejo se salta esa pelicula
		if not complejo: continue
		peli_html = peli.findPrevious('table', width='695', align='center')
		search = peli_exp.search(peli['href'])
		if search:
			id_peli = search.group(1)
			try:
				peli_ver = Peli_ver.objects.get(id_pol=id_peli)
			except:
				logger.debug( 'No se encontro pelicula:%s'  % id_peli)
				continue
		for hora in peli_html.findAll('span', style='color: #FFFFFF; font-weight:normal; font-size: 11px'): #Cada hora
			id_show = None
			hora_str = ''.join(hora.findAll(text=True)).replace('\n', '')
			hora_str = to24Hour(hora_str)
			funciones.append(
			{'peli_ver': peli_ver,
			'complejo': complejo,
			'hora': datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora_str , '%H:%M')[3:5]),
			'pol_idShowTime': id_show,
			}
			)
	return funciones



def updateFuncionAspMovil():
	"""Actualiza los funciones de la pag movil"""
	base_url = "http://www.cinepolis.com.mx/CinepolisMovil/Ciudad.aspx?IdCiudad=%s" #id_ciudad
	ciudades = [2,]#Complejo.objects.values_list('id_ciudad', flat=True).annotate()
	fecha = datetime.date(2009, 8, 12)
	fecha_str = fecha.strftime('%d/%m/%Y')
	
	funciones = []
	
	for id_ciudad in ciudades:
		url = base_url % id_ciudad
		pag_html = urlopen(url)
		soup = BeautifulSoup(pag_html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
		complejos = soup.find(id='pnlFunciones').div.findAll('div', align='center') #cada elemento de la lista tiene las peliculas y funciones por comp.
		for comp_html in complejos:
			comp_id = re.search(r'IdComplejo=(\d{0,3})', str(comp_html.findPrevious('a'))).group(1)
			complejo = Complejo.objects.get(id_org=comp_id)
			for hora_html in comp_html.findAll('span', 'Fechas'):
				peli_id = re.search(r'Pelicula=(\d{1,4})', str(hora_html.findPrevious('span', 'Pelicula'))).group(1)
				pelicula = Pelicula.objects.get(id_pol=peli_id)
				for tag in hora_html.contents: #Puede que tag sea un span con el link para cineticket o un string con las horas
					if isinstance(tag, NavigableString):
						#Hay que parsear el string ie. 12:30, 1:15
						times = tag.split(', ')
						#logger.debug( complejo)
						funciones.extend([{
							'complejo': complejo,
							'pelicula': pelicula,
							'hora': (lambda hora: datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora , '%H:%M')[3:5]))(to24Hour(hora))	
							}for hora in times if to24Hour(hora)])
					else:
						exp = r'programacion=(\d{1,5})&funcion=(\d{1,2}:\d\d)'
						if tag.a: 
							a = re.search(exp, tag.a['href'])
							id_show, hora = a.groups()
							
							funciones.append({
							'complejo': complejo,
							'pelicula': pelicula,
							'pol_idShowTime': id_show,
							'hora': (lambda hora: datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora , '%H:%M')[3:5]))(hora)	
								})


def updateFuncionesXML():
	"""Obtiene los funciones del XML ObtenerFunciones"""
	base_url = "http://www.cinepolis.com.mx/Cartelera/ASPX/ObtenerFunciones.aspx?IdCiudad=%s&IdPelicula=%s&fecha=%s" #fecha dd/mm/aaaa
	
	#id_ciudad = 2
	fechas = [date(2009, 8, 15),]
	#fecha_str = fecha.strftime('%d/%m/%Y')
	funciones = []
	
	ids_peliculas = Pelicula.objects.values_list('id_cineticket', flat=True)
	
	ciudades = [2,]#Complejo.objects.values_list('id_ciudad', flat=True).annotate()
	
	
	for fecha in fechas: #fechasSemana():
		fecha_str = fecha.strftime('%d/%m/%Y')
		for id_ciudad in ciudades:
			for id_peli in ids_peliculas:
				url = base_url % (id_ciudad, id_peli, fecha_str)
				try:
					xml = urlopen(url)
					funciones.extend(parse_funcionxml(xml, fecha))
					
				except Exception, e:
					logger.debug( 'error loading %s' % url)
					
	#logger.debug( len(funciones))
	for hora in funciones:
		createFuncion(hora)		


def parse_funcionxml(data, fecha):
	"""Regresa una lista de diccionarios con ids y nombre del complejo"""
	parser = BeautifulStoneSoup(data)
	funciones = [{	
			'sala': complejo['salanumero'],
			'complejo': Complejo.objects.get(id_org=complejo['id']),
			'pelicula': Pelicula.objects.get(id_cineticket=complejo['peliculaid']),
			'pol_idShowTime': complejo['idshowtime'],
			'hora': (lambda hora: datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora , '%H:%M')[3:5]))(complejo['funcion'])	#Crea datetime con fecha y funcion de xml		
			} 
			for complejo in parser.findAll('complejo')]
	return funciones	


def scrape_funcionesAsp(data, fecha, id_ciudad):
	"""scrape de la cartelera normal
	regresa lista de diccionarios:
	{
	'peli_ver': pelicula,
	'complejo': complejo,
	'hora': datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora_str , '%H:%M')[3:5]),
	'pol_idShowTime': id_show,
	}
	"""	
	funciones = []
	comp_exp = re.compile(r'Cine(\d*)')
	peli_exp = re.compile(r'ip=(\d+)')
	show_exp = re.compile(r'programacion=(\d+)&amp;funcion=(\d{1,2}:\d\d)&') #regresa idshow y funcion
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	complejos = soup.find('table', align='center', width='600').tbody.tr.td.div.findNextSiblings('table', width='695')#[:-1] #El ultimo es un baner por eso [:-1]
	#if not complejos:
	#	complejos = soup.find('table', align='center', width='600').tbody.tr.td.div.findNextSiblings('table', width='695')
	for comp_html in complejos: #Cada complejo
		complejo = None
		#Para evitar los banners
		try:
			comp_mch = comp_exp.search(comp_html.findPrevious('a')['id'])
		except:
			continue
		if comp_mch:
			comp_id = comp_mch.group(1)
			try:
				complejo = Complejo.objects.get(id_org=comp_id, cadena='Cinepolis')
			except:
				logger.debug( 'No se encontro complejo:%s de ciudad: %s' % (comp_id, id_ciudad))
				continue
		for peli_html in comp_html.findAll('table', width='695', align='center'): #Cada pelicula
			peli_ver = None
			search = peli_exp.search(peli_html.find('a', href=re.compile(r'/pelicula.aspx'))['href'])
			if search:
				id_peli = search.group(1)
				try:
					peli_ver = Peli_ver.objects.get(id_pol=id_peli)
				except:
					logger.debug( 'No se encontro pelicula:%s'  % id_peli)
					continue
			horas = [a.span for a in peli_html.find('td', align='left', width='100%').findAll('table', align='left')]
			for hora in horas: #Cada hora
				id_show = None
				hora_str = None
				show_mch = show_exp.search(str(hora))
				if show_mch:
					id_show, hora_str = show_mch.groups()
				else:
					hora_str = ''.join(hora.findAll(text=True)).replace('\n', '')
					try:
						hora_str = to24Hour(hora_str)
					except:
						logger.debug( 'Error con la hora %s de la pelicula %s complejo %s' %(hora_str, id_peli, comp_id))
						continue
				if not hora:
					logger.debug( 'AGUAS no tengo hora')
					continue
				funciones.append(
				{'peli_ver': peli_ver,
				'complejo': complejo,
				'hora': datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora_str , '%H:%M')[3:5]),
				'pol_idShowTime': id_show,
				}
				)
	return funciones


