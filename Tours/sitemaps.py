from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Package

# Tours/sitemaps.py

class PackageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Add .order_by('id') to fix the warning
        return Package.objects.all().order_by('id')

    def location(self, item):
        return reverse('package_detail', args=[item.pk])

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['home', 'about', 'contact', 'packages', 'services']

    def location(self, item):
        return reverse(item)