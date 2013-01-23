from django.http import HttpResponse

import cinepolis, cinemex, cinemark, scrape_base, time
# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


	
def updateComplejos(request):
	"""Actualiza la BD con los complejos"""
	pol_start = time.time()
	cinepolis.updateComplejos()
	mex_start = time.time()
	cinemex.updateComplejos()
	mark_start = time.time()
	#cinemark.updateComplejos()
	fin = time.time()
	duration = fin - pol_start
	return HttpResponse('Complejos up to date.</br> %0.1f minutos</br></br>Cinepolis %0.1f</br>Cinemex %0.1f</br>Cinemark %0.1f' %(duration/60.0, (mex_start-pol_start)/60, (mark_start-mex_start)/60, (fin-mark_start)/60 ))
	

def updatePeliculas(request):
	"""Actualiza la BD con las peliculas"""
	pol_start = time.time()
	cinepolis.updatePeliculas()
	
	mex_start = time.time()
	cinemex.updatePeliculas()
	
	mark_start = time.time()
	cinemark.updatePeliculas()
	scrape_base.corrigeSub()
	fin = time.time()
	duration = fin - pol_start
	return HttpResponse('Peliculas up to date.</br> %0.1f minutos</br></br>Cinepolis %0.1f</br>Cinemex %0.1f</br>Cinemark %0.1f' %(duration/60.0, (mex_start-pol_start)/60, (mark_start-mex_start)/60, (fin-mark_start)/60 ))

def updateFunciones(request):
	"""Actualiza la BD con los funciones"""
	pol_start = time.time()
	logger.debug( 'Cinepolis')
	logger.debug( '')
	cinepolis.updateFunciones()
	logger.debug( 'Cinemex')
	logger.debug( '')
	mex_start = time.time()
	cinemex.updateFunciones()
	logger.debug( 'Cinemark')
	logger.debug( '')
	mark_start = time.time()
	cinemark.updateFunciones()
	fin = time.time()
	duration = fin - pol_start
	return HttpResponse('Funciones up to date.</br> %0.1f minutos</br></br>Cinepolis %0.1f</br>Cinemex %0.1f</br>Cinemark %0.1f' %(duration/60.0, (mex_start-pol_start)/60, (mark_start-mex_start)/60, (fin-mark_start)/60 ))
