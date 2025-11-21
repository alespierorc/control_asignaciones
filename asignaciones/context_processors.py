from .models import Anuncio

def anuncios_context(request):
    if request.user.is_authenticated:
        no_leidos = Anuncio.objects.filter(destinatario=request.user, leido=False).count()
        return {"anuncios_no_leidos": no_leidos}
    return {}
