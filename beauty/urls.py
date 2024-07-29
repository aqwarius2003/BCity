from django.urls import include, re_path
from django.contrib import admin


urlpatterns = [
    # url(r'^$', views.show_flats),
    # url(r'^search/$', views.show_flats),
    re_path(r'^admin/', admin.site.urls),
]