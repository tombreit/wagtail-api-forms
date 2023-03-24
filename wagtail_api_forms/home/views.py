from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, Http404

def sphinx_searchindex_view(request):
    searchindex_json_path = settings.BASE_DIR / "docs/_build/json/searchindex.json"
    if searchindex_json_path.is_file():
        with open(searchindex_json_path, 'r') as fh:
            searchindex_js = f"Search.setIndex({fh.read()});"
            response = HttpResponse(searchindex_js, content_type="text/javascript")
            response['Content-Disposition'] = 'inline; filename="searchindex.js"'
            return response
    raise Http404
