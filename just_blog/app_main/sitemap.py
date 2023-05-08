from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse


class StaticSiteMap(Sitemap):
    """
    Sitemap object for static pages.
    """

    def items(self):
        return ['about', 'contacts']

    def location(self, item):
        return reverse(f'app_main:{item}')
