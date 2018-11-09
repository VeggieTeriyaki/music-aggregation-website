"""myproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path
from aggserv import views

urlpatterns = [
    path('test/', views.index, name='index'),
    path('redirect/', views.finish_spot_auth, name='redirect'),
    path('admin/', admin.site.urls),
    path('spotify-login/', views.spotlogin),
    path('search-query/',views.searchQuery),
    path('insert-query/',views.insertQuery),
    path('update-query/',views.updateQuery),
    path('delete-query/',views.deleteQuery)
]