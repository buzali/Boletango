from Peliculas.cinemex import *
import sys
url_movil = "http://m.cinemex.com/"
url_base_cd = "http://m.cinemex.com/estrenos.php?cveciudad=%s"
base_url_complejo = "http://www.cinemex.com/cinemex/complejos.php?cvecine=%s"
xml_peliculas = "http://api2.cinemex.com/rsvr.php?Action=GetFiltrados&IdDev=1&ciudad=%s&byciudad=1"
base_url_pelicula = "http://www.cinemex.com/cartelera/pelicula.php?vcode=%s"
base_url_cartelera = "http://cinemex.com/cartelera/cartelera_cine.php?cvecine=%s"

ciudades ={ u'63': u'D.F. y \xc1rea Metropolitana',
 u'65': u'Guadalajara',
 u'66': u'Toluca',
 u'71': u'Acapulco',
 u'73': u'Morelia',}

complejos =[{'id_org': u'2', 'nombre': u'Cinemex Altavista'},
 {'id_org': u'50', 'nombre': u'Cinemex Antara'},
 {'id_org': u'12', 'nombre': u'Cinemex Galer\xedas'},
 {'id_org': u'48', 'nombre': u'Cinemex Interlomas'},
 {'id_org': u'35', 'nombre': u'Cinemex Universidad'},
 {'id_org': u'24', 'nombre': u'Cinemex WTC'},
]



def test_parse_ciudades():
	count_malas = 0
	try:
		ciudades = parse_ciudades( urlopen(url_movil) )
		if not ciudades: return 0
	except:
		return 0
	for k,v in ciudades.items():
		if not k or not v: count_malas +=1
	if count_malas > 3: return 0
	else: return 1

def test_parse_complejos():
	count_malas = 0
	for ciudad_id in ciudades.keys():
		url_cd = url_base_cd % ciudad_id	
		try:
			complejos = parse_complejos( urlopen(url_cd) )
			if not complejos: count_malas +=1
			for c in complejos:
				if not (c['id_org'] and c['nombre']): count_malas +=1
		except:
			count_malas +=1
	if count_malas > 3: return 0
	else: return 1

def test_scrape_compInfo():
	count_malas = 0
	for comp in complejos:
		url = base_url_complejo % comp['id_org']
		comp_html = urlopen(url)
		try:
			complejo, platino = scrape_compInfo(comp_html,comp)
			if not complejo: count_malas +=1
			if not complejo['nombre']: count_malas +=1
		except:
			count_malas +=1
	if count_malas > 3: return 0
	else: return 1

def test_cinemex_complejos():
	return (test_scrape_compInfo() and test_parse_complejos() and test_parse_ciudades())

def test_parse_peliculas():
	count_malas = 0
	for ciudad_id in ciudades:
		xml_url = xml_peliculas % ciudad_id
		xml = urlopen(xml_url)
		try:
			pelis_actual = parse_peliculas(xml)
			if not pelis_actual: count_malas +=1
			for peli in pelis_actual:
				if not peli: count_malas +=1
		except:
			count_malas +=1
	if count_malas > 3: return 0
	else: return 1
			
def test_scrape_pelicula():
	""" Depende de parse_peliculas """
	count_malas = 0
	peliculas = {}
	for ciudad_id in ciudades:
		xml_url = xml_peliculas % ciudad_id
		xml = urlopen(xml_url)
		pelis_actual = parse_peliculas(xml)[0:5]
		for peli in pelis_actual:
			key = peli.get('mex_vc', '')
			if key not in peliculas: peliculas[key] = peli
	for k, v in peliculas.items()[0:5]:
		url = base_url_pelicula % k
		html = urlopen(url)
		try:
			peli = scrape_pelicula(html, v)
			if not peli: count_malas +=1
			if not peli['titulo']: count_malas +=1
		except:
			count_malas +=1
	if count_malas > 3: return 0
	else: return 1	

def test_cinemex_peliculas():
	return (test_scrape_pelicula() and test_parse_peliculas() and test_parse_ciudades())
	
def test_scrape_cartelera():
	mex_comps = Complejo.objects.filter(cadena='Cinemex', id_org__lt=10000)[0:5]
	count_malas = 0
	for comp in mex_comps:
		if comp.nombre.find('Platino') == -1:
			#logger.debug( u'Cargando complejo %s' %comp.mex_nombre())
			url = base_url_cartelera % comp.id_org
			page = urlopen(url)
			try:
				funciones = scrape_cartelera(page.read(), comp.nombre)		
				if not funciones: count_malas +=1
				for f in funciones:
					if not f: count_malas +=1
					if not f['hora']: count_malas +=1
			except TypeError:
				count_malas +=1
	if count_malas > 3: return 0
	else: return 1

def test_cinemex_funciones():
	return ( test_scrape_cartelera())

def test_cinemex_verbose():
	logger.debug( "Prueba Cinemex")
	sys.stdout.write("\nParse ciudades...")
	if test_parse_ciudades(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nParse complejos...")
	if test_parse_complejos(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nParse pelicula...")
	if test_parse_peliculas(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape pelicula...")
	if test_scrape_pelicula(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape funciones...")
	if test_scrape_cartelera(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")