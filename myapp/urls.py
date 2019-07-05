
from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('',views.upload,name='upload'),
    path('ncbi/',views.ncbi, name = 'ncbi'),
    path('uniprot/',views.uniprot, name = 'uniprot')
]
