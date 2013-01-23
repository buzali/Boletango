from django.conf.urls.defaults import *
from Peliculas.views import updatePeliculas, updateComplejos, updateFunciones

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^Boletango/', include('Boletango.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
	(r'^updatePeliculas/$', updatePeliculas),
	(r'^updateComplejos/$', updateComplejos),
	(r'^updateFunciones/$', updateFunciones),
	
	
	(r'^API/', include('Boletango.API_piston.urls')),
	(r'^APIv/', include('Boletango.API.urls')),
	
)
