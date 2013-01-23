from Peliculas.models import *
from Peliculas.cinemark import *
import sys
#xml_complejos = "http://www.google.com"
xml_complejos = "http://www.cinemark.com.mx/xml/lista.xml"
base_url = "http://www.cinemark.com.mx/cines.php?complejo=%s"
complejos = [{'id_org': u'2', 'nombre': u'Cinemark Bosques'},
 {'id_org': u'7', 'nombre': u'Cinemark Centro Nacional de las Artes'},
 {'id_org': u'50', 'nombre': u'Cinemark Parque Lindavista'},
 {'id_org': u'8', 'nombre': u'Cinemark Pedregal'},
 {'id_org': u'53', 'nombre': u'Cinemark Reforma 222'},
 {'id_org': u'39', 'nombre': u'Cinemark Canc\xfan'},]

cartelera = "http://www.cinemark.com.mx/cartelera.php"
headers = {'Referer': 'http://www.cinemark.com.mx/cartelera.php',
 'X-requested-with': 'XMLHttpRequest',}
ajax_url= "http://www.cinemark.com.mx/ajax-response.php"


def test_parse_complejosxml():
	try:
		complejos = parse_complejosxml(urlopen(xml_complejos))
		if not complejos: return 0
		for c in complejos:
			if not c['id_org']: return 0 
			if not c['nombre']: return 0
		return 1
	except:
		return 0
		
def test_scrape_compInfo():
	count_malos = 0
	for c in complejos:
		try:
			comp_html = urlopen(base_url % c['id_org'])
			complejo, platino = scrape_compInfo(comp_html,c)
			if not complejo: count_malos +=1
		except:
			count_malos +=1
	if count_malos > 3: return 0
	else: return 1

def test_mini_scrapePeli():
	br = mechanize.Browser()
	br.set_handle_robots(False)
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]	
	html = br.open(cartelera).read()
	count_malos = 0
	pelis = []
	try:
		pelis = mini_scrapePeli(html)
	except Exception, e:
		logger.debug( e )
		count_malos +=1
	for p in pelis:
		if not p: count_malos +=1
	if not pelis: count_malos +=5
	if count_malos > 5: return 0
	else: return 1
	
def test_scrape_pelicula():
	""" Asume que mini_scrapePeli sirve """
	br = mechanize.Browser()
	br.set_handle_robots(False)
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]	
	html = br.open(cartelera).read()
	pelis = mini_scrapePeli(html)
	count_malos = 0
	peliculas = []
	for peli in pelis[0:5]:
		req_ajax = mechanize.Request(ajax_url)
		req_ajax.headers = headers
		values = {u'myajaxrequest': '{"typeRequest":"get-movie","myMovieID":"' + peli['id_mark'] + '","myMovieName":"' + peli['titulo_mark'] +'"}'}
		data = urllib.urlencode(dict([k, v.encode('utf-8')] for k, v in values.items())) #Convierte a utf-8 y decode
		req_ajax.data = data
		resp_ajax = br.open(req_ajax).read()
		peli_html = br.open("http://www.cinemark.com.mx/" + resp_ajax).read()
		try:
			peliculas.append(scrape_pelicula(peli_html, peli ))
		except Exception, e:
			count_malos +=1
	for p in peliculas:
		if not p['sinopsis']: count_malos +=1
	if count_malos >3: return 0
	else: return 1
	
def test_nuevo_scrape_cartelera():
	complejos = Complejo.objects.filter(cadena='Cinemark')
	count_malos = 0
	for comp in complejos[0:5]:
		url = base_url % comp.id_org
		page = urlopen(url)
		try:
			funciones = nuevo_scrape_cartelera(page, comp)
			if not funciones: count_malos +=1
		except:
			count_malos +=1
			continue
		for hora in funciones:
			if not hora: count_malos +=1
	if count_malos >3: return 0
	else: return 1	

def test_cinemark_peliculas():
	return (test_mini_scrapePeli() and test_scrape_pelicula())

def test_cinemark_funciones():
	return test_nuevo_scrape_cartelera()

def test_cinemark_complejos():
	return (test_parse_complejosxml() and test_scrape_compInfo())


def test_cinemark_verbose():
	logger.debug( "Prueba Cinemark")
	sys.stdout.write("\nComplejos xml...")
	if test_parse_complejosxml(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape complejos...")
	if test_scrape_compInfo(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nminiScrape pelicula...")
	if test_mini_scrapePeli(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape pelicula...")
	if test_scrape_pelicula(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape funciones...")
	if test_nuevo_scrape_cartelera(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")	