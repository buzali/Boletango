"""
cinepolis.py

Created by Tofi Buzali on 2009-08-15.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.

Funciones necesarias para hacer el scraping de cinepolis


"""
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, NavigableString
import time, re, urllib2, locale
from urllib2 import urlopen
from datetime import date, datetime, timedelta
from models import *
from scrape_base import *
from lxml.html.clean import clean_html, Cleaner

#****************************************************Agregar aqui las variables globales***************************************************************
url_movil = "http://m.cinemex.com/"

#Complejos
def updateComplejos():
	"""Jala los complejos usando la pagina movil"""
	
	url_base_cd = "http://m.cinemex.com/estrenos.php?cveciudad=%s"
	
	base_url_complejo = "http://www.cinemex.com/cinemex/complejos.php?cvecine=%s"
	
	ciudades = parse_ciudades( urlopen(url_movil) )
	
	for ciudad_id in ciudades.keys():
		url_cd = url_base_cd % ciudad_id
		complejos = parse_complejos( urlopen(url_cd) )
		for comp in complejos:
			url = base_url_complejo % comp['id_org']
			comp_html = urlopen(url)
			complejo, platino = scrape_compInfo(comp_html,comp)
			#logger.debug( complejo['id_org'])
			complejo['id_ciudad']= ciudad_id
			createComplejo(complejo)
			if platino: createComplejoPlatino(complejo)	
	
	#Por alguna razon hay algunos cinemex sin nombre y causan problema
	#Borra vacios
	Complejo.objects.filter(nombre='Cinemex ').delete()	

def parse_ciudades(data):
	"""regresa dict con id: nombre ciudad"""
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	ciudades_html = soup.find('select', id='ByCiudad').findAll('option', value=True)
	ciudades = {}
	for c in ciudades_html:
		ciudades[c['value']] = c.string
	return ciudades
	
def parse_complejos(data):
	"""regresa lista de dict con id_org: nombre complejo"""
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	complejos_html = soup.find('select', id='ByComple').findAll('option', value=True)
	complejos = [{'id_org': complejo['value'],
			'nombre': 'Cinemex ' + complejo.string}
			for complejo in complejos_html]
	return complejos

def scrape_compInfo(data, comp):
	"""Agrega al diccionario recibido direccion y telefonos by scraping la info de data.
	Regresa diccionario y bool q indica si existen salas platino
	
	"""
	c_data = comp # id_org, mex_ciudad y nombre de xml
	platino = False #Determina si es necesario crear complejo platino
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	
	c_data['cadena']='Cinemex'
	
	#direccion soup.find('table', cellspacing='3').findAll('td',colspan='2')[0].p.findNextSiblings(text=True)
	#telefono soup.find('table', cellspacing='3').findAll('td',colspan='2')[1]
	datos = soup.find('table', cellspacing='3').findAll('td',colspan='2')
	
	c_data['nombre'] = str(soup.find('span', 'texto_6').string)
	c_data['direccion'] = ''.join(datos[0].p.findAll(text=True)).strip()
	c_data['telefonos_string'] = ''.join(datos[1].findAll(text=True)).strip()
	
	#Checa si existe salas platino
	precios = soup.find('td', width='179')
	precios_str = ''.join(precios.findAll(text=True))
	if precios_str.find('Platino') > -1:
		platino = True
	
	return c_data, platino


def createComplejoPlatino(c_dict):
	"""Cambia el nombre para agregar platino y crea el complejo. Los platino tienen id_org +10000 ej 10050"""
	nom = c_dict['nombre'].split()
	nom.insert(1, 'Platino')
	nombre = ' '.join(nom)
	c_dict['nombre'] = nombre
	c_dict['id_org'] = int(c_dict['id_org']) + 10000
	createComplejo(c_dict)


#VIEJOS Complejo
#Este no tiene todas las ciudades .:. no aparecen todos los complejos
def VIEJOupdateComplejos():
	"""Jala datos de cada complejo de cinepolis y lo agrega a la BD"""
	xml_ciudades = "http://api2.cinemex.com/rsvr.php?Action=GetFiltrados&IdDev=1"
	xml_complejos = "http://api2.cinemex.com/rsvr.php?Action=GetFiltrados&IdDev=1&ciudad=%s"
	
	
	ciudades = parse_ciudadesxml( urlopen(xml_ciudades) )#Diccionario de ciudades de Mexico
	
	#xml = urlopen(xml_complejos)
	#ids = parse_complejosxml(xml)
	
	base_url = "http://www.cinemex.com/cinemex/complejos.php?cvecine=%s"
	
	for ciudad_id in ciudades:
		xml_url =  xml_complejos % ciudad_id
		complejos_xml = urlopen(xml_url)
		complejos = parse_complejosxml(complejos_xml)
		for comp in complejos:
			url = base_url % comp['id_org']
			comp_html = urlopen(url)
			complejo, platino = scrape_compInfo(comp_html,comp)
			#logger.debug( complejo['id_org'])
			complejo['id_ciudad']= ciudad_id
			#createComplejo(complejo)
			logger.debug( complejo)
			logger.debug( platino)
			#if platino: createComplejoPlatino(complejo)


def parse_complejosxml(data):
	"""regresa un diccionario con 'id': 'nombre complejo'"""
	parser = BeautifulStoneSoup(data)
	ids = [{'id_org': complejo.clave.string,
			'nombre': 'Cinemex ' + complejo.nombre.string}
			for complejo in parser.findAll('cine')]
	return ids


def parse_ciudadesxml(data):
	"""regresa un diccionario con 'id': 'nombre ciudad'"""
	parser = BeautifulStoneSoup(data)
	ciudades = {}
	for ciudad in parser.findAll('ciudad'):
		ciudades[ciudad.clave.string] = ciudad.nombre.string
	
	return ciudades


###



#Peliculas
def updatePeliculas():
	"""Checa q todas las peliculas existan en la BD en caso de no existir la crea"""
	xml_ciudades = "http://api2.cinemex.com/rsvr.php?Action=GetFiltrados&IdDev=1"
	xml_peliculas = "http://api2.cinemex.com/rsvr.php?Action=GetFiltrados&IdDev=1&ciudad=%s&byciudad=1" #id_ciudad
    
	ciudades = parse_ciudades( urlopen(url_movil) )    
	
	
	base_url_pelicula = "http://www.cinemex.com/cartelera/pelicula.php?vcode=%s" #mex_vc
	peliculas = {}
    
	pelis_obj = [] #Contiene toda la info de las peliculas, titulo, sinopsis, etc
    
	#Crea un diccionario con el vc y el objeto de la pelicula
	#De esta forma no hay peliculas repetidas
	for ciudad_id in ciudades:
		xml_url = xml_peliculas % ciudad_id
		try:
			xml = urlopen(xml_url)
		except:
			logger.debug( 'error cargando pagina %s' % xml_url)
			continue
		pelis_actual = parse_peliculas(xml)
		#Agregar las peliculas q no estan todavia
		for peli in pelis_actual:
			key = peli.get('mex_vc', '')
			if key not in peliculas: peliculas[key] = peli
            
	for k, v in peliculas.items():
		url = base_url_pelicula % k
		html = urlopen(url)
		pelis_obj.append(scrape_pelicula(html, v))
        
	for peli in pelis_obj:
		createPelicula(peli)


def parse_peliculas(data):
	"""Parsea el archivo con peliculas y ID"""
	parser = BeautifulStoneSoup(data)
	peliculas = [{ 'id_mex': peli.clave.string.strip(),
				'titulo': peli.nombre.string.strip(),
				'mex_vc': peli.vc.string.strip(),
				'subtitulada': unicode(peli.idiomaflex.string).find(u'Ingl\xe9s') > -1,
				'doblada':  unicode(peli.idiomaflex.string).find(u'Espa\xf1ol') > -1,
				'tres_D': unicode(peli.idiomaflex.string).find(u'3D') > -1}
				for peli in parser.findAll('pelicula')]
	return peliculas

def scrape_pelicula(data, peli_data):
	"""Scrape de la informacion de la pelicula"""
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	p_data = peli_data
    
	descripcion_peli = soup.find('div', 'descripcion_peli')
    
	if descripcion_peli:
		titulo_html = descripcion_peli.find('span', 'texto_4')
		p_data['titulo'] = unicode(titulo_html.string).strip()
		p_data['titulo_org'] = unicode(titulo_html.findNext('span').string).strip()
        
	string_att = {'directores': 'Director:', 'actores': 'Actores:', 'tags': u'G&eacute;nero:', 'clasificacion': u'Clasificaci&oacute;n:', 'duracion': u'Duraci&oacute;n:', 'pais_origen': u'Pa&iacute;s Origen:', 'sinopsis': 'SINOPSIS' }
    
	for k,v in string_att.items():
		try:
			p_data[k] = unicode(soup.find('span', text=v).findNext(['span', 'div'], 'texto_1').string).strip()
		except:
			p_data[k] = ''
            
	img_url = soup.find('img', alt='poster')['src'].strip()
	if img_url:
		p_data['img_urls'] = (img_url,)
	
	return p_data




#Funciones
def updateFunciones():
	"""Actualiza los funciones de la pagina de cinemex"""
	# lt=10000 Asegura que no sea la platino, los horarios de platino estan en normal
	mex_comps = Complejo.objects.filter(cadena='Cinemex', id_org__lt=10000)
	base_url_cartelera = "http://cinemex.com/cartelera/cartelera_cine.php?cvecine=%s"
	
	for comp in mex_comps:
		url = base_url_cartelera % comp.id_org
		try:
			page = urlopen(url)
			funciones = scrape_cartelera(page.read(), comp.nombre)		
			for hora in funciones:
				createFuncion(hora)
		except:
			logger.debug( u'error cargando cartelera de comp %s' %comp.mex_nombre())
                

def scrape_cartelera(data, comp_nom):
	"""scrape de la cartelera por complejo recibe html y nombre del complejo"""	
	funciones = []
	#limpia el html para no tener problemas:
	cleaner = Cleaner(page_structure=False)
	cleaned = cleaner.clean_html(data)
	soup = BeautifulSoup(cleaned, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	show_exp = re.compile(r'sid=(\d+)')
	sala_exp = re.compile(r'Sala (\d{1,2})')
	
	complejo_org = Complejo.objects.get(nombre=comp_nom)
	complejo = complejo_org
	complejo_platino = None
	
	#Quita el nombre cinemex para encontrar comp platino
	nom_corto = comp_nom.replace('Cinemex ', '')
	complejos_l = Complejo.objects.filter(nombre__icontains=nom_corto, cadena='Cinemex')
	#Busca complejo platino:
	if len(complejos_l) > 1:
		nom = 'Cinemex Platino '+ nom_corto
		query = complejos_l.filter(nombre=nom)
		if len(query): complejo_platino = query[0] 
		
	peliculas = []
	contenido = soup.find('div', 'contenido2')
	
	#Si existe tabla de peliculas
	if contenido:
		try:
			peliculas = contenido.find('table', cellspacing='0', cellpadding='0', border='0').contents
		except:
			logger.debug( u'Error cargando complejo %s' %comp_nom)
			return []
			#logger.debug( u'peliculas mide %s' %len(peliculas))
		
		
		for peli in peliculas:
			#logger.debug( peli)
			#Asegura que no sea un navigableString
			imax = False
			if type(peli) != NavigableString:
				if peli.find('div', 'texto_1', align='center'):
					#logger.debug( peli.b.string)
					if peli.b.string.find('Platino') > -1:
						#Ajustar el complejo para platino
						if complejo_platino:
							imax = False
							complejo = complejo_platino
						else:
							logger.debug( u'Me falta platino %s' %comp_nom)
							return funciones
						#logger.debug( 'Estoy en platino')
					elif peli.b.string.find('IMAX')>-1:
						imax = True
					else:
						imax = False
						complejo= complejo_org
						
				#Si el td corresponde a una pelicula
				if peli.find('td', width='210', valign='top'):	
					tres_D = False
					idioma = None
					sala = None
					pelicula = None
					
					#Checar tiene logo de 3d
					if peli.find('div', 'icono_platino').find('img', src=re.compile(r'3d.png$')): tres_D = True
					
					#Encabezado contiene titulo e idioma
					encabezado = peli.find('li', 'texto_3')
					titulo = ''.join(encabezado.findAll(text=True)).replace('\n', '').strip()
					
					
					#Determina Idioma
					idi = encabezado.find('img', alt='idioma')
					if idi:
						if idi.get('src', '').find('ing') > 0:
							idioma = 'ingles'
					else:
						idioma = 'espanol'
						
					#Buscar pelicula por titulo segun idioma y 3d.. subtitulada o no.
					#logger.debug( u'titulo %s' %titulo)
					tit = '|'+ titulo + '|'
					peli_query = filter_peli_ver(pelicula__alt_tit__icontains=tit, tres_D=tres_D, imax=imax)# id_mex__gt=0)
					#Checa si hay imax. 
					las_imax = peli_query.filter(imax=True)
					if las_imax:
						peli_query= las_imax
						logger.debug( 'Encontre imax!')
						
					if len(peli_query) > 1:
						#Si idioma == ingles, selecciona la pelicula subtitulada
						try:
							pelicula = peli_query.get(subtitulada= (idioma == 'ingles'), doblada = (idioma != 'ingles') )
							
						except Exception, e:
							logger.debug( e)
							logger.debug( "Error de idioma con la pelicula %s, idioma: %s" % (titulo, idioma))
							continue
					elif len(peli_query) == 1:
						pelicula = peli_query[0]
					else:
						logger.debug( u'No encontre pelicula %s, tres_D=%s, idioma=%s' %(titulo, tres_D, idioma))
						continue
					#logger.debug( u'pelicula %s' %pelicula)
					horas_html = peli.findAll('div', id='fecha')
					
					#logger.debug( u'tengo %s fechas aqui...' %len(horas_html))
					#logger.debug( horas_html)
					
					for tag in horas_html:
						#Me salto todo lo que no es html
						if type(tag) != NavigableString:
							#Si esta disponible, obtiene num. sala
							if tag.get('style', '').find('text-transform: uppercase;') > -1: sala = sala_exp.search(tag.string).group(1)
							
							#logger.debug( u'hay %s horarios aqui'%len(tag.findNext('div', id='horarios').findAll('a', 'texto_1')))
							fecha = parseDate(tag.string)
							#logger.debug( pelicula)
							#logger.debug( complejo)
							funciones.extend([{
    									'peli_ver': pelicula,
    									'complejo': complejo,
    									'hora': datetime.datetime(fecha.year, fecha.month, fecha.day,  *time.strptime( hora_html.string , '%H:%M')[3:5]),
    									'pol_idShowTime': show_exp.search(hora_html['href']).group(1),
    									'sala': sala,
    									} for hora_html in tag.findNext('div', id='horarios').findAll('a', 'texto_1')])
		#logger.debug( len(funciones))
		return funciones
				
			




	


	
def scrape_carteleraVIEJA(data, comp_nom):
	"""scrape de la cartelera por complejo"""	
	
	funciones = []
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	show_exp = re.compile(r'sid=(\d+)')
	
	complejo_org = Complejo.objects.get(nombre=comp_nom)
	
	#Busca complejo platino... en caso de existir:
	complejo_platino = complejo_org
	
	
	peliculas = soup.find('table', cellspacing='0', cellpadding='0', border='0').contents[3:-1:2]
	
	for peli in peliculas:
		tres_D = False
		idioma = None
		
		#Checar tiene logo de 3d
		if peli.find('div', 'icono_platino').find('img', src=re.compile(r'3d.png$')): tres_D = True
		
		#Encabezado contiene titulo e idioma
		encabezado = peli.find('li', 'texto_3', style='margin: 2px 0px 0px; float: left; width: 155px;')
		titulo = ''.join(encabezado.findAll(text=True)).replace('\n', '').strip()
		
		
		#Determina Idioma
		if encabezado.find('img', alt='idioma').get('src', '').find('ing') > 0:
			idioma = 'ingles'
		else:
			idioma = 'espanol'
		
		tit = '|'+ titulo + '|'
		#Buscar pelicula por titulo segun idioma y 3d.. subtitulada o no.
		peli_query = Pelicula.objects.filter(alt_tit__icontains=tit, tres_D=tres_D)
		if len(peli_query) > 1:
			#Si idioma == ingles, selecciona la pelicula subtitulada
			pelicula = peli_query.filter(subtitulada= (idioma == 'ingles') )
		elif len(peli_query) == 1:
			pelicula = peli_query[0]
		else:
			logger.debug( "No se encontro pelicula %s" % titulo		)
			
		horas_html = peli.find('div', id='horax')
		platino_b= False		
		for tag in horas_html.contents:
			#Me salto todo lo que no es html
			if type(tag) != NavigableString:		
				#En caso de que sea funciones de platino
				if tag.name == 'center':
					platino_b = True
					funcion_name = ''.join(tag.findAll(text=True)).strip()
					if funcion_name.find('Platino') > -1:
						#Ajustar el complejo para platino
						complejo = complejo_platino
						
				elif tag.get('style','').find('border-bottom: 1px solid rgb(238, 207, 0);') > -1:
					#Ajustar de regreso el complejo normal
					complejo = complejo_org
					platino_b = False
					
					
				#Si es renglon de hora y no algo mas como <br/>			
				if tag.name== 'div' and tag.get('id','') == 'general':
					fecha = parseDate(tag.find('div', id=fecha).string)
					funciones.extend(
						[{
							'pelicula': pelicula,
							'complejo': complejo,
							'hora': datetime.datetime(fecha.year, fecha.month, fecha.day,  *time.strptime( hora_html.string , '%H:%M')[3:5]),
							'pol_idShowTime': show_exp.search(hora_html['href']).group(1),
							} for hora_html in tag.find('div', id='funciones').find('a', 'texto_1')]
							
						)
					#logger.debug( funciones)
	return funciones



