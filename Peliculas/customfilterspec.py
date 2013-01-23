# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.admin.filterspecs import FilterSpec, ChoicesFilterSpec, RelatedFilterSpec
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

class CustomFilterSpec(FilterSpec):
    """
    Na verdade este é um FilterSpec para passar Queryset diferente do default do campo, por exemplo, filtrado 
    """
    def __init__(self, f, request, params, model, model_admin):
        super(CustomFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.lookup_val = request.GET.get(f.name, None)
        if isinstance(f, models.ManyToManyField):
            self.lookup_title = f.rel.to._meta.verbose_name
        else:
            self.lookup_title = f.verbose_name
        
        # Queryset padrão
        qs = f.rel.to._default_manager.all()
        
        # Verifica se as opções do admin possuem um queryset para este campo
        qs_dict = getattr(model_admin, 'custom_filter_spec', None)
        if qs_dict and f.name in qs_dict:
            qs = qs_dict[f.name]
        
        self.lookup_choices = qs.all()

    def title(self):
        return self.lookup_title

    def choices(self, cl):
        yield {'selected': self.lookup_val is None,
               'query_string': cl.get_query_string({}, [self.field.name]),
               'display': All}
        for inst in self.lookup_choices:
            val = smart_unicode(inst.pk)
            yield {'selected': self.lookup_val == val,
                   'query_string': cl.get_query_string({self.field.name: val}),
                   'display': smart_unicode(inst)}

# O ideal seria usar o método register, mas o filtro ficaria por último e não seria utilizável.
# Então é preciso registrá-lo como primeiro.
#FilterSpec.register(lambda f: bool(f.rel and hasattr(f, 'custom_filter_spec')), CustomFilterSpec)
FilterSpec.filter_specs.insert(0, (lambda f: bool(f.rel and hasattr(f, 'custom_filter_spec')), CustomFilterSpec))