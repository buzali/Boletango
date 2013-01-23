"""
cinepolis.py

Created by Tofi Buzali on 2009-08-15.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.

Funciones necesarias para hacer el scraping de cinepolis


"""
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, NavigableString
import time, re, urllib, locale, string, mechanize
from urllib2 import urlopen
from django.utils.http import urlquote
from datetime import date, datetime, timedelta
from models import *
from scrape_base import *
import cookielib

#****************************************************Agregar aqui las variables globales***************************************************************





def updateComplejos():
	"""Jala datos de cada complejo de cinepolis y lo agrega a la BD"""
	complejos_url = "http://www.cinemark.com.mx/complejos.aspx"
	html = urlopen(complejos_url)
	complejos = scrape_complejos(html)
	for comp in complejos:
		premier = comp.pop('premier')
		createComplejo(comp)
		if premier: createComplejoPremier(comp)
		logger.debug( comp['nombre'])




def scrape_complejos(data):
	""" Regresa lista de dict con datos de los complejos """
	id_exp = re.compile(r'id_theater=(\d*)')
	complejos_lt = [] #complejos list
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	complejos = soup.findAll('table', 'theater_container')
	for c in complejos:
		c_data = {}
		c_data['cadena'] = 'Cinemark'
		c_data['nombre'] = 'Cinemark ' + c.find('td', 'theater_name').text
		info_tp = c.find('td','theater_info').contents
		c_data['direccion'] = info_tp[0]
		c_data['telefonos_string'] = info_tp[2].replace('Telefono: ', '')
		c_data['premier'] = bool(c.find('td','theater_services').find('img', src=re.compile('premier')))
		c_data['id_org'] = id_exp.search(c.find('td', 'theater_billboard_and_map').a['href']).group(1)
 		complejos_lt.append(c_data)
	return complejos_lt
		
		


def updateFunciones():
	"""Actualiza los funciones de la pagina de cinemark"""
	#gt 330 para ignorar complejos de la pag vieja
	#lt 10000 para ignorar premier
	complejos = Complejo.objects.filter(cadena='Cinemark', id__gt=330, id_org__lt=10000) 
	
	base_url = "http://www.cinemark.com.mx/vercartelera.aspx?id_theater=%s"
	
	for comp in complejos:
		url = base_url % comp.id_org
		logger.debug( url)
		page = urlopen(url)
		try:
			funciones = scrape_cartelera(page, comp)
		except Exception, e:
			logger.debug( "Error con complejo %s: %s" %(comp.nombre, e)	)
		for hora in funciones:
			createFuncion(hora)

def scrape_cartelera(data, complejo):
	"""
	{
	'peli_ver': pelicula,
	'complejo': complejo,
	'hora': datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora_str , '%H:%M')[3:5]),
	}
	
	"""
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	funciones = []
	pelicula_tables = []
	pelicula_tables = soup.findAll('table', 'uneven')
	pelicula_tables.extend(soup.findAll('table', 'pair'))
	complejo_org = complejo
	for peli_table in pelicula_tables:
		complejo = complejo_org
		info_dict = {}
		find_for = {'title': 'titulo' , 'date': 'fecha' , 'schedules' : 'horas' }
		for k, v in find_for.items():
			info_dict[v] = peli_table.find('td', k).text
		
		horas = info_dict['horas'].split(' | ')
		fecha_tp = info_dict['fecha'].split('/')
		fecha = datetime.date(int(fecha_tp[2]), int(fecha_tp[1]), int(fecha_tp[0]))
		extras = {}
		cambios, titulo = corrigeTitulo(info_dict['titulo'])
		if cambios:
			for c in cambios:
				extras[c] = True		
			if extras.pop('premier', False):
				try:
					complejo = Complejo.objects.get(id_org=complejo.id_org+10000, cadena='Cinemark')
				except Exception, e:
					logger.error('Falta complejo premier %s, %s: %s' %(complejo.nombre,complejo.id_org, e))
					complejo = None
					break
		#Si no existe el complejo premier, salta a siguiente peli_table
		if not complejo: continue
		try:
			peli_ver_qs = Peli_ver.objects.filter(pelicula__alt_tit__icontains=titulo)
			if len(peli_ver_qs) > 1:
				#Usa la huella para checar cual de las vers coincide.
				#De otra forma tambien regresa las q tienen cosas especiales como Digital xs, etc
				ver_busco = Peli_ver(**extras)
				peli_ver_qs = peli_ver_qs.filter(**extras)
				for ver in peli_ver_qs:
					if ver_busco.huella == ver.huella: peli_ver=ver
				if not peli_ver:
					logger.debug( u'Encontre mas de una pelicula %s, extras=%s' %(titulo, extras))
					continue
			elif len(peli_ver_qs)==1:
				peli_ver = peli_ver_qs[0]
			else:
				logger.debug( u'No encontre pelicula %s, extras=%s' %(titulo , extras))
				continue
		except:
	  		logger.debug( u'EXCEPTION--- No encontre pelicula %s, extras=%s' %(titulo, extras))
			continue
		fun = [{'peli_ver': peli_ver,
		'complejo':complejo,
		'hora': datetime.datetime(fecha.year, fecha.month, fecha.day, *time.strptime( hora, '%H:%M')[3:5]),
		}for hora in horas]
		funciones.extend(fun)
	return funciones
	



def updatePeliculas():
	
	url = 'http://www.cinemark.com.mx/cartelera.aspx'
	peli_url_base = 'http://www.cinemark.com.mx/vercomplejos.aspx?movie_name_original=%s'
	
	html = urlopen(url)
	soup = BeautifulSoup(html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	main_table = soup.find('table', id='date_table')
	movies_tds = main_table.findAll('td', 'movie_cell')
	titulos = [m_td.find('p', 'movie_title').a.text.strip() for m_td in movies_tds]
	for tit in titulos:
		#Convierte IRI a URL para evitar error de unicode
		iri = urlquote(tit)
		peli_url = peli_url_base %iri
		peli_html = urlopen(peli_url)
		try:
			peli = scrape_pelicula(peli_html, tit)
		except Exception, e:
			logger.debug( u'No se pudo scrapear peli %s: %s' %(tit,e))
			continue
		createPelicula(peli)


def scrape_pelicula(html, tit):
	p_data = {}
	cambios, titulo = corrigeTitulo(tit)
	#Agrega extras a p_data
	if cambios:
		p_data['titulo'] = titulo
		for c in cambios:
			p_data[c] = True
	#premier no me interesa, lo saco
	if 'premier' in p_data: p_data.pop('premier')
	soup = BeautifulSoup(html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	p_data['titulo'] = titulo
	t_org_p = soup.find('p', 'movie_title_original')
	if t_org_p:
		p_data['titulo_org'] = t_org_p.text.replace('(','').replace(')', '').strip()
	p_data['sinopsis'] = soup.find('td', 'movie_synopsis').findAll('b', text=True)[1]
	find_for = {'tags': 'Genero: ' , 'clasificacion': u'Clasificaci\xf3n: ' ,'duracion' : u'Duraci\xf3n: ', 'directores': 'Director: ', 'actores':'Actores: ' }
	for k, v in find_for.items():
		item = soup.find('span', 'movie_red', text=v)
		if item:
			p_data[k] = item.findNext('span', 'movie_info', text=True).strip()
			
	img_td = soup.find('td', 'movie_image_container')
	img_url = img_td.findNext('img')['src'].strip()
	if img_url:
		p_data['img_urls']= ("http://www.cinemark.com.mx/%s" %img_url ,)
	return p_data




def createComplejoPremier(c_dict):
	"""Cambia el nombre para agregar premier y crea el complejo. Los platino tienen id_org +10000 ej 10050"""
	nom = c_dict['nombre'].split()
	nom.insert(1, 'Premier')
	nombre = ' '.join(nom)
	c_dict['nombre'] = nombre
	c_dict['id_org'] = int(c_dict['id_org']) + 10000
	createComplejo(c_dict)





def updateFunciones_viejoo():
	"""Actualiza los funciones de la pagina de cinemark"""
	complejos = Complejo.objects.filter(cadena='Cinemark')
	
	base_url = "http://www.cinemark.com.mx/cines.php?complejo=%s"
	
	for comp in complejos:
		url = base_url % comp.id_org
		page = urlopen(url)
		try:
			funciones = nuevo_scrape_cartelera(page, comp)
		except:
			logger.debug( "Error con complejo %s" %comp.nombre	)
		for hora in funciones:
			createFuncion(hora)


def nuevo_scrape_cartelera(data, comp):
	"""docstring for nuevo_scrape_cartelera
	{
	'peli_ver': pelicula,
	'complejo': complejo,
	'hora': datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora_str , '%H:%M')[3:5]),
	}
	"""	
	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
	complejo = comp
	funciones = []
	peliculas = soup.find('table', width=765).table.findAll('table', width=765)
	for peli in peliculas:
		titulo = peli.find('div', 'titulo-pelioula').text
		cambios, titulo = corrigeTitulo(titulo)
		extras = {}
		if cambios:
			for c in cambios:
				extras[c]= True
		if extras.pop('premier', False):
			complejo = Complejo.objects.get(id_org=comp.id_org+10000, cadena='Cinemark')
		else:
			complejo = comp
		logo = peli.find('img', src=re.compile('imagenes/cartelera/ws-'))['src']
		preventa = logo.find('preventa') >-1
		if preventa: continue #No toma en cuenta las preventas
		premier = logo.find('premier') >-1
		tres_D = logo.find('3D') > -1
		try:
			peli_ver_qs = Peli_ver.objects.filter(pelicula__alt_tit__icontains=titulo, tres_D=tres_D)
			if len(peli_ver_qs) > 1:
				#Usa la huella para checar cual de las vers coincide.
				#De otra forma tambien regresa las q tienen cosas especiales como Digital xs, etc
				ver_busco = Peli_ver(**extras)
				peli_ver_qs = peli_ver_qs.filter(**extras)
				for ver in peli_ver_qs:
					if ver_busco.huella == ver.huella: peli_ver=ver
				if not peli_ver:
					logger.debug( u'Encontre mas de una pelicula %s, tres_D=%s, extras=%s' %(titulo, tres_D, extras))
					continue
			elif len(peli_ver_qs)==1:
				peli_ver = peli_ver_qs[0]
			else:
				logger.debug( u'No encontre pelicula %s, tres_D=%s, extras=%s' %(titulo, tres_D, extras))
				continue
   		except:
   			logger.debug( u'EXCEPTION--- No encontre pelicula %s, tres_D=%s, extras=%s' %(titulo, tres_D, extras))
   			continue
		for fecha_html in peli.findAll('div', 'campo-fecha'):
			fecha_txt = fecha_html.text
			fecha = parseDate(fecha_txt)
			#junta todo el texto en un solo string pq pueden estar separados por <br> y se perdia una hora
			horas_string = u' \xa0 '.join(fecha_html.findNext('div','campo-hora').findAll(text=True))
			fun = [{'peli_ver': peli_ver,
			'complejo':complejo,
			'hora': datetime.datetime(fecha.year, fecha.month, fecha.day, *time.strptime( to24Hour(hora), '%H:%M')[3:5]),
			}for hora in horas_string.split(u' \xa0 ')] #\xa0 == nbsp;
			funciones.extend(fun)
	return funciones





def corrigeTitulo(titulo):
	"""Checa el titulo por subtitulada o doblada y regresa el titulo corregido y una clave en caso de q cambia"""
	find_for = {' (SUBTITULADA)':'subtitulada', ' (DOBLADA)': 'doblada', ' 3D':'tres_D', ' SALA XD': 'xe', ' SALA PREMIER': 'premier',  u'(ESPA\xd1OL)': ''}
	cambios = []
	for k, v in find_for.items():
		found = titulo.find(k)
		if found > -1:
			titulo = titulo.replace(k,'').strip()
			if v:cambios.append(v)
	titulo = string.capwords(titulo)
	return cambios, titulo

#
#def mini_scrapePeli(data):
#	"""  """
#	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
#	peliculas_html = soup.findAll('td', width=244)
#	peli_exp = re.compile(r'pelicula=(\d+)')
#	id_exp = re.compile(r"fxjs_get_movie\('(\d+)'")
#	complejos = []
#	string_att = ['tags', 'clasificacion', 'duracion']
#	
#	for peli_html in peliculas_html:
#		p_data = {}
#		p_data['id_mark'] = id_exp.search(peli_html.findPrevious('a',onclick=True)['onclick']).group(1)
#		p_data ['tags'], p_data ['clasificacion'], p_data['duracion']  =[a.nextSibling.strip()  for a in peli_html.findAll('span' ,'texto_d')][:-1]
#		p_data['titulo_mark']= peli_html.find('td', 'titulo_b').find(text=True).strip()
#		idioma = ''.join(peli_html.findAll('tr')[5].findAll(text=True)).strip()
#		
#		find_for = {'(Subtitulada)': 'subtitulada' , '(Doblada)': 'doblada'}
#		for k, v in find_for.items():
#			p_data[v] = idioma.find(k) > -1
#		
#		cambios, titulo = corrigeTitulo(p_data['titulo_mark'])
#		p_data['titulo'] = string.capwords(titulo)
#		if cambios:
#			for c in cambios:
#				p_data[c] = True #Pone como true el campo especial eg. Subtitulada		
#		complejos.append(p_data)
#	return complejos
#	
#	
	


#def scrape_pelicula(data, peli_data):
#	"""Scrape de la informacion de la pelicula"""
#	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
#	p_data = peli_data
#	p_data['sinopsis'] = soup.find('td', 'texto_bco', align='left', width=264).findAll(text=True)[0]
#	if p_data['sinopsis']==None:
#		p_data['sinopsis'] = ''
#	return p_data
#	
#	#string_att = {'directores': u'Dirigida por: ', 'actores': u'Con: ', 'pais_origen':  u'Pa\xeds: '}
#	#
#	#for k,v in string_att.items():
#	#	try:
#	#		p_data[k] = soup.find('td', background = re.compile('f_dorado')).find('td', 'texto').find(text=re.compile(v)).strip().replace(v,'')
#	#	except:
#	#		p_data[k] = ''
#	#
#	#cambios, titulo = corrigeTitulo(p_data['titulo'])
#	#if cambios:
#	#	p_data['titulo'] = titulo
#	#	for c in cambios:
#	#		p_data[c] = True #Pone como true el campo especial eg. ggulada
	

#def updateComplejos_viejo():
#	"""Jala datos de cada complejo de cinepolis y lo agrega a la BD"""
#	
#	xml_complejos = "http://www.cinemark.com.mx/xml/lista.xml"
#	
#	#cines_url = "http://www.cinemark.com.mx/cines.php?ban=1"
#	base_url = "http://www.cinemark.com.mx/cines.php?complejo=%s"
#	
#	complejos = parse_complejosxml(urlopen(xml_complejos))
#	for comp in complejos:
#		url = base_url % comp['id_org']
#		comp_html = urlopen(url)
#		try:
#			complejo, platino = scrape_compInfo(comp_html,comp)
#		except:
#			logger.debug( 'Error al cargar complejo %s' %comp['id_org'])
#			continue
#		if complejo:
#			createComplejo(complejo)
#			if platino: createComplejoPremier(complejo)	


#def parse_complejosxml(data):
#	"""regresa un diccionario con 'id': 'nombre complejo'"""
#	parser = BeautifulStoneSoup(data)
#	ids = [{'id_org': complejo['variable_xml'],
#			'nombre': u'Cinemark ' + complejo['nombre_xml']}
#			for complejo in parser.findAll('foto')]
#	return ids
#


#def scrape_compInfo(data, comp):
#	"""Agrega al diccionario recibido direccion y telefonos by scraping la info de data.
#	Regresa diccionario.
#	"""
#	c_data = comp # id_org, y nombre 
#	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
#	c_data['cadena']='Cinemark'
#	string_ids = {'direccion': r'Direcci\D+n:', 'telefonos_string': r'Tel\D+fono'}
#	for k, v in string_ids.items():
#		c_data[k]= soup.find(text=re.compile(v)).findNext('td').text	
#	platino = bool(soup.find(text=re.compile('Premier:')))
#	return c_data, platino


#VIEJO	
##def scrape_complejos_viejo(data):
#	"""regresa un diccionario con 'id': 'nombre complejo'"""
#	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
#	exp = re.compile('complejo=(\d+)')
#	
#	html = ''.join(unicode(a) for a in soup.findAll('td', 't_amarilla'))
#	soup = BeautifulSoup(html, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
#	
#	
#	ids = [ {'id_org': exp.search(complejo['href']).group(1), 
#			'nombre': 'Cinemark ' + string.capwords(complejo.find(text=True))}
#			for complejo in soup.findAll('a')]
#	return ids
#


#Funciones


#def scrape_cartelera(data, comp):
#	"""scrape de la cartelera por complejo. recibe el html de la cartelera y nombre del complejo
#	
#	class Funcion(models.Model):
#		pelicula = models.ForeignKey(Pelicula)
#		complejo = models.ForeignKey(Complejo)
#		hora = models.DateTimeField()
#		sala = models.IntegerField(null=True, blank=True)
#		pol_idShowTime = models.IntegerField(null=True, blank=True)
#	
#	"""	
#	funciones = []
#	
#	soup = BeautifulSoup(data, convertEntities=BeautifulStoneSoup.HTML_ENTITIES)
#	peliculas_h = soup.findAll('td', background=re.compile('dorado.jpg'))
#	complejo = comp
#	
#	
#	peli_exp = re.compile(r'pelicula=(\d+)')
#		
#	for peli in peliculas_h:
#		peli_id = peli_exp.search(peli.findPrevious('a', href=peli_exp)['href']).group(1)
#		peli_tit = peli.find('td', 'titulo').string
#		
#		try:
#			pelicula = Pelicula.objects.get(id_mark=peli_id)
#		except:
#			logger.debug( 'No se encontro pelicula:%s'  % peli_id)
#			continue
#		
#		#info_h Contiene funciones, nombre en ingles, clasificacion, etc
#		info_h = peli.find('td', width=600).findAll('tr')
#		try:
#			semana_str = info_h[3].next.string.strip().split('.')
#			fines_str = ''.join(info_h[4].findAll(text=True)).replace(u'Funciones de s\xe1bado y domingo:', '').strip().split('.')
#		except:
#			logger.debug( "Error cargando fecha de peli %s, str: %s, %s" % (peli_tit, semana_str, fines_str))
#		
#		#Junta las horas con los dias de la semana correspondientes
#		horas = loop_fechas(semana_str, fechasDias())
#		horas += loop_fechas(fines_str, fechasFines())
#		
#		funciones.extend(
#					{'pelicula': pelicula,
#					'complejo': complejo,
#					'hora': hora ,
#					} for hora in horas)
#	return funciones
	
		
#		
#def loop_fechas(horas_str, fechas):
#	"""Hace un loop con las fechas y horas.
#	horas_str es una lista con horas ej. ['12:40am','1:24 PM' ]
#	fechas son obj datetime
#	"""
#	horas = []
#	for fecha in fechas:
#		for hora in horas_str:
#			try:
#				hora_str = to24Hour(hora)
#			except:
#				logger.debug( 'Error con la hora %s de la pelicula complejo' %(hora))
#				continue
#			if hora_str !=None and hora_str !='':	
#				horas.append(datetime.datetime(fecha.year,fecha.month,fecha.day, *time.strptime( hora_str , '%H:%M')[3:5]))
#	return horas		
#			



#def updatePeliculas():
#	"""Checa q todas las peliculas existan en la BD en caso de no existir la crea"""
#	
#	br = mechanize.Browser()
#	br.set_handle_robots(False)
#	#cj = cookielib.LWPCookieJar()
#	#br.set_cookiejar(cj)
#	
#	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
#	
#	headers = {'Referer': 'http://www.cinemark.com.mx/cartelera.php',
#	 'X-requested-with': 'XMLHttpRequest',}	
#	ajax_url= "http://www.cinemark.com.mx/ajax-response.php"
#	
#	cartelera = "http://www.cinemark.com.mx/cartelera.php"
#	
#	para_scrape = []
#	pelis_obj = [] #Contiene toda la info de las peliculas, titulo, sinopsis, etc
#	
#	html = br.open("http://www.cinemark.com.mx/cartelera.php").read()
#	pelis = mini_scrapePeli(html)
#	#Busca si existe la pelicula, sino hace el scrape grande
#	for peli in pelis:
#		if existePelicula(peli):
#			createPelicula(peli)
#		else:
#			#Si no existe hay que hacer el scrape de toda la info y luego agregarla
#			para_scrape.append(peli)
#	peliculas = []
#	base_url = "http://www.cinemark.com.mx/pelicula.php?pelicula=%s"
#	if para_scrape:
#		for peli in para_scrape:
#			req_ajax = mechanize.Request(ajax_url)
#			req_ajax.headers = headers
#			#Agrego id_mark y titulo despues para que no codifique algunas cosas como parentesis etc
#			values = {u'myajaxrequest': '{"typeRequest":"get-movie","myMovieID":"' + peli['id_mark'] + '","myMovieName":"' + peli['titulo_mark'] +'"}'}
#			del peli['titulo_mark']
#			data = urllib.urlencode(dict([k, v.encode('utf-8')] for k, v in values.items())) #Convierte a utf-8 y decode
#			req_ajax.data = data
#			resp_ajax = br.open(req_ajax).read()
#			peli_html = br.open("http://www.cinemark.com.mx/" + resp_ajax).read()
#			try:
#				peliculas.append(scrape_pelicula(peli_html, peli ))
#			except:
#				logger.debug( u"Error cargando pelicula %s %s" %(p_data['id_mark'], p_data['titulo']))
#				continue
#	
#	for peli in peliculas:
#		createPelicula(peli)
#
#

