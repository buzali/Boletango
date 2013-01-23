#from IRC user jtiai 

import django.utils.simplejson as json
#from django.contrib.gis.geos.geometry import GEOSGeometry
from django.utils import datetime_safe
from django.utils.functional import Promise
from django.utils.encoding import force_unicode
from django.http import HttpResponse
import datetime

from Peliculas.models import Pelicula

class AugmentedJSONEncoder(json.JSONEncoder):
    """
    Augmentation for simplejson encoder.
    Now additionally encodes arbitrary iterables, class instances, decimals,
    GEOSGeometries, dates, times and datetimes.
    """
    
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
       # if isinstance(o, GEOSGeometry):
        #    return o.wkt
        if(hasattr(o, "__iter__")):
            iterable = iter(o)
            return list(iterable)
        elif(hasattr(o, "__add__") and hasattr(o, "__sub__") and hasattr(o, "__mul__")):
            return float(o)
        elif isinstance(o, datetime.datetime):
            d = datetime_safe.new_datetime(o)
            return d.isoformat()
        elif isinstance(o, datetime.date):
            d = datetime_safe.new_date(o)
            return d.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        elif isinstance(o, Promise):
            return force_unicode(o)
        elif isinstance(o, Pelicula):
            the_dict = o.__dict__
            the_dict['titulo'] = unicode(o)
            return the_dict
        elif(hasattr(o, "__class__")):
            return o.__dict__
        else:
            return str(o)
        
def render_to_json(obj):
    return HttpResponse(json.dumps(obj, ensure_ascii=False, cls=AugmentedJSONEncoder),) #mimetype='application/json')