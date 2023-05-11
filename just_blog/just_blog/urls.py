"""
URL configuration for just_blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.i18n import JavaScriptCatalog
import debug_toolbar
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from django.contrib.sitemaps.views import sitemap
from app_blog.sitemap import PostSiteMap
from app_main.sitemap import StaticSiteMap

sitemap_static = {
    'static': StaticSiteMap,
}

sitemap_posts = {
    'posts': PostSiteMap,
}


schema_view = get_schema_view(
    openapi.Info(
        title="API for the JustBlog blogging platform",
        default_version="v1",
        description="An API to get the data of the database of the web application "
                    "and pefrom the same actions available in it.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="pevzner.daniil@gmail.com"),
        license=openapi.License(name="")
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('app_auth.urls')),
    path('main/', include('app_main.urls')),
    path('', lambda req: redirect('main/')),
    path('i18n', include('django.conf.urls.i18n')),
    path('blogs/', include('app_blog.urls')),
    path('posts-feed/', include('app_rss.urls')),
    path('api/', include('app_api.urls')),
    path('api/auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('api-auth/', include('rest_framework.urls')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema_swagger_ui'),
    path('sitemap-static.xml/',
         sitemap,
         {'sitemaps': sitemap_static},
         name='django.contrib.sitemaps.views.sitemap'
         ),
    path('sitemap-posts.xml/',
         sitemap,
         {'sitemaps': sitemap_posts},
         name='django.contrib.sitemaps.views.sitemap'
         ),
]


if settings.DEBUG:
    urlpatterns.extend(
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    )

    urlpatterns.extend(
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    )

    # urlpatterns += [
    #     path('__debug__/', include(debug_toolbar.urls))
    # ]
