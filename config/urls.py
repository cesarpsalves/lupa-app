"""URL config raiz."""

from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.documents.urls import public_urlpatterns as documents_public_urls
from apps.public.sitemaps import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    # SEO
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("", include("apps.public.urls", namespace="public")),
    path("contas/", include("apps.accounts.urls", namespace="accounts")),
    path("app/", include("apps.dashboard.urls", namespace="app")),
    path("app/clientes/", include("apps.clients.urls", namespace="clients")),
    path("app/servicos/", include("apps.catalog.urls", namespace="catalog")),
    path("app/empresa/", include("apps.companies.urls", namespace="companies")),
    path("app/agenda/", include("apps.scheduling.urls", namespace="scheduling")),
    path("app/atendimentos/", include("apps.tickets.urls", namespace="tickets")),
    path("app/caixa/", include("apps.cashflow.urls", namespace="cashflow")),
    path("app/documentos/", include(("apps.documents.urls", "documents"), namespace="documents")),
    # Links públicos de cupom (sem auth, acesso por token)
    path("", include((documents_public_urls, "documents_public"), namespace="documents_public")),
    path(
        "healthz",
        TemplateView.as_view(template_name="healthz.txt", content_type="text/plain"),
        name="healthz",
    ),
]

# Estáticos: servidos por WhiteNoise (middleware) em qualquer ambiente.
# Mídia: WhiteNoise não cobre uploads dinâmicos, então adicionamos a view
# do Django pra MEDIA_URL. Trade-off conhecido (Django serve direto sem
# nginx); aceitável pro MVP até migrar pra Cloudflare R2.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
