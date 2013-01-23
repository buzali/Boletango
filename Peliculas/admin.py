from django.contrib import admin
from customfilterspec import CustomFilterSpec
from models import *
from django import forms
import re

class TelefonoField(forms.IntegerField):
    """ Quita todo lo que no sea un digito """
    def clean(self, value):
        value = re.sub("\D", "", value)
        return super(TelefonoField, self).clean(value)

class ComplejoForm(forms.ModelForm):
    """Cambia los telefonos a TelefonoField y asi elimina todo lo que no sea digito antes de guardar"""
    telefono1 = TelefonoField(required=False)
    telefono2 = TelefonoField(required=False)
    telefono3 = TelefonoField(required=False)
    
    class Meta:
        model = Complejo

class Version(admin.TabularInline):
	model = Peli_ver
	extra = 0
	verbose_name_plural = 'versiones'
	readonly_fields = ('id',)

class Imagenes(admin.TabularInline):
	model = ImagenPelicula
	extra = 0
	verbose_name_plural = 'imagenes'	
	readonly_fields = ('id',)

class ComplejoAdmin(admin.ModelAdmin):
	search_fields = ('nombre', 'direccion', 'id_org')
	#list_filter = ('dir_lat',)
	list_display = ('id','nombre', 'ciudad_m', 'dir_lat')
	#custom_filter_spec = {'dir_lat': Complejo.objects.filter(dir_lat='')}
	form = ComplejoForm

class PeliculaAdmin(admin.ModelAdmin):
	search_fields = ('titulo', 'sinopsis','peli_ver__id_pol', 'peli_ver__id_cineticket','peli_ver__id_mex','peli_ver__id_mark')
	list_display = ('id','titulo')
	inlines = [Version, Imagenes]                                       
                                                              
class FuncionAdmin(admin.ModelAdmin):                         
    search_fields = ('peli_ver__pelicula__titulo', 'complejo__nombre')
    list_display = ('id','peli_ver', 'complejo', 'hora', 'sala', 'pol_idShowTime')
    list_filter = ('hora',)




admin.site.register(Complejo, ComplejoAdmin)
admin.site.register(Pelicula, PeliculaAdmin)
admin.site.register(Funcion, FuncionAdmin)
admin.site.register(Ciudad)

