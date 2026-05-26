from __future__ import annotations

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Páginas estáticas/públicas indexáveis."""

    priority = 1.0
    changefreq = "weekly"
    protocol = "https"

    def items(self) -> list[str]:
        return ["public:landing"]

    def location(self, item: str) -> str:
        return reverse(item)
