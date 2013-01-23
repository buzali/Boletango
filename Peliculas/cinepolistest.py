from Peliculas.models import *
from Peliculas.cinepolis import *
import sys
xml_peliculas = "http://www.cinepolis.com.mx/pelicula/xml/peliculasxml.aspx"
base_url_pelicula = "http://www.cinepolis.com.mx/cartelera/aspx/pelicula.aspx?ip=%s&peliculacineticket=%s"

xml_complejos = "http://www.cinepolis.com.mx/xml/complejos.xml"
xml_ciudades = "http://www.cinepolis.com.mx/Aspx/xml/CiudadesXml/CiudadesXml.aspx?pais=1"
base_url_complejo = "http://www.cinepolis.com.mx/cartelera/aspx/complejoinfo.aspx?plaza=%s&ciudad=%s"
base_url_cartelera = "http://www.cinepolis.com.mx/cartelera/aspx/carteleras_.aspx?ci=%s&fecha=%s"


ids_complejos =[{'id_ciudad': u'2', 'id_org': u'1', 'nombre': u'Cin\xe9polis Acapulco'},
 {'id_ciudad': u'4',
  'id_org': u'4',
  'nombre': u'Cin\xe9polis Plaza Las Am\xe9ricas'},
 {'id_ciudad': u'4',
  'id_org': u'150',
  'nombre': u'Cin\xe9polis VIP Plaza Las Am\xe9ricas'},
 {'id_ciudad': u'24',
  'id_org': u'273',
  'nombre': u'Cin\xe9polis Galer\xedas Las Torres'},
 {'id_ciudad': u'24',
  'id_org': u'269',
  'nombre': u'Cin\xe9polis La Gran Plaza'},]

ciudades = {u'10': u'Chihuahua',
 u'101': u'Comit\xe1n',
 u'103': u'Taxco',
 u'108': u'Orizaba',
 u'109': u'Hidalgo del Parral',
 u'11': u'Coatzacoalcos',
 u'111': u'Tabasco',
 u'12': u'Culiac\xe1n',
 u'13': u'D.F. y \xc1rea Metropolitana (Centro)',
 u'14': u'D.F. y \xc1rea Metropolitana  (Norte)',
 u'15': u'D.F. y \xc1rea Metropolitana (Oriente)',
 u'16': u'D.F. y \xc1rea Metropolitana (Poniente)',
 u'17': u'D.F. y \xc1rea Metropolitana (Sur)',
 u'18': u'Ensenada',
 u'19': u'Guadalajara',
 u'2': u'Acapulco',
 u'22': u'Hermosillo',
 u'23': u'Irapuato',
 u'24': u'Le\xf3n',
 u'26': u'Matamoros',
 u'27': u'Mazatl\xe1n',
 u'28': u'M\xe9rida',
 u'29': u'Mexicali',
 u'3': u'Aguascalientes',
 u'30': u'Minatitl\xe1n',
 u'31': u'Monterrey',
 u'32': u'Morelia',
 u'33': u'Nogales',
 u'34': u'Nuevo  Laredo',
 u'35': u'Pachuca',
 u'36': u'Puebla',
 u'37': u'Quer\xe9taro',
 u'38': u'Reynosa',
 u'39': u'Saltillo',
 u'4': u'Canc\xfan',
 u'40': u'San Luis Potos\xed',
 u'42': u'Tampico',
 u'43': u'Tapachula',
 u'44': u'Tijuana',
 u'45': u'Toluca',
 u'47': u'Tuxtla Guti\xe9rrez',
 u'48': u'Uruapan',
 u'49': u'Veracruz',
 u'5': u'Cd. Ju\xe1rez',
 u'50': u'Villahermosa',
 u'51': u'Xalapa',
 u'52': u'Durango',
 u'53': u'Cozumel',
 u'54': u'Torre\xf3n',
 u'55': u'Salamanca',
 u'57': u'La Paz',
 u'58': u'Oaxaca',
 u'6': u'Cd. Obreg\xf3n',
 u'60': u'Chetumal',
 u'61': u'San Crist\xf3bal de las Casas',
 u'63': u'Puerto Vallarta',
 u'64': u'Tecate',
 u'65': u'Cuernavaca',
 u'66': u'Cd. Cuauht\xe9moc (Chihuahua)',
 u'67': u'Manzanillo',
 u'70': u'Playa del Carmen',
 u'71': u'Tehuac\xe1n',
 u'74': u'Colima',
 u'76': u'San Jos\xe9 del Cabo',
 u'78': u'Tepeji del R\xedo',
 u'79': u'San Luis R\xedo Colorado',
 u'8': u'Cd. Victoria',
 u'81': u'Tuxpan',
 u'85': u'Uriangato',
 u'88': u'Zamora',
 u'89': u'Rosarito',
 u'9': u'Celaya',
 u'90': u'Cuautla',
 u'91': u'Iguala',
 u'93': u'Chilpancingo',
 u'97': u'Cd. Acu\xf1a',
 u'99': u'Cabo San Lucas'}


def test_parse_peliculasxml():
	xml = urlopen(xml_peliculas)
	try:
		ids = parse_peliculasxml(xml)
		if not ids: return 0
		for i in ids:
			if not i['titulo']: return 0
	except:
		return 0
	return 1

def test_scrape_pelicula():
	""" Depende de parse_peliculasxml """
	xml = urlopen(xml_peliculas)
	ids = parse_peliculasxml(xml)
	count_malas = 0
	for peli_data in ids[0:5]:
		url = base_url_pelicula % (peli_data['id_pol'], peli_data['id_cineticket'])
		peli_html = urlopen(url)
		try:
			pelicula = scrape_pelicula(peli_html, peli_data)
			if not pelicula: count_malas +=1
			if not pelicula['titulo']: count_malas+=1
			if not pelicula['duracion']: count_malas +=1
		except Exception, e:
			count_malas +=1
			logger.debug( e)
	if count_malas > 3: return 0
	else: return 1

def test_cinepolis_peliculas():
	return (test_scrape_pelicula() and  test_parse_peliculasxml())
	
def test_parse_complejosxml():
	xml = urlopen(xml_complejos)
	try:
		ids = parse_complejosxml(xml)
		if not ids: return 0
		for i in ids:
			if not i['nombre']: return 0
	except:
		return 0
	return 1

def test_parse_ciudadesxml():
	try:
		ciudades = parse_ciudadesxml( urlopen(xml_ciudades) )
		if not ciudades: return 0
		for i in ciudades:
			if not i: return 0
	except:
		return 0
	return 1

def test_scrape_compInfo():
	count_malas = 0
	for comp_id in ids_complejos:
		if comp_id['id_ciudad'] in ciudades: #verifica que la ciudad sea de mexico
			url = base_url_complejo % (comp_id['id_org'], comp_id['id_ciudad'])
			comp_html = urlopen(url)
			try:
				complejo =scrape_compInfo(comp_html, comp_id)
				if not complejo: count_malas +=1
				if not complejo['direccion']: count_malas +=1
			except:
				count_malas +=1
	if count_malas > 3: return 0
	else: return 1

def test_cinepolis_complejos():
	return (test_parse_complejosxml() and test_parse_ciudadesxml() and test_scrape_compInfo())

def test_scrape_funcionesAsp():
	count_malas = 0
	for fecha in [date.today(),]:#fechasSemana():
		fecha_str = fecha.strftime('%Y%m%d')
		for id_ciudad, v in ciudades.items()[0:5]:
			url = base_url_cartelera % (id_ciudad, fecha_str)
			html = urlopen(url)
			try:
				funciones = scrape_funcionesAsp0811(html, fecha, id_ciudad)
				if not funciones: count_malas +=1
				for hora in funciones:
					if not hora['hora']: count_malas +=1
			except:
				count_malas +=1
	if count_malas > 3: return 0
	else: return 1

def test_cinepolis_funciones():
	return test_scrape_funcionesAsp()
	
def test_cinepolis_verbose():
	logger.debug( "Prueba Cinepolis")
	sys.stdout.write("\nParse peliculas...")
	if test_parse_peliculasxml(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape pelicula...")
	if test_scrape_pelicula(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nParse complejos...")
	if test_parse_complejosxml(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nParse ciudades...")
	if test_parse_ciudadesxml(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape complejos...")
	if test_scrape_compInfo(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")
	sys.stdout.write("\nScrape funciones...")
	if test_scrape_funcionesAsp(): sys.stdout.write("OK")
	else:  sys.stdout.write("FAIL")