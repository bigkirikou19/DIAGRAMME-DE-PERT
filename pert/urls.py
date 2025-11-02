from django.urls import path
from . import views

urlpatterns = [
    # Page d'accueil
    path('', views.home, name='home'),
    
    # Gestion des projets
    path('projets/', views.projet_list, name='projet_list'),
    path('projets/nouveau/', views.projet_create, name='projet_create'),
    path('projets/<int:pk>/', views.projet_detail, name='projet_detail'),
    path('projets/<int:pk>/modifier/', views.projet_update, name='projet_update'),
    path('projets/<int:pk>/supprimer/', views.projet_delete, name='projet_delete'),
    
    # Gestion des tâches
    path('projets/<int:projet_id>/taches/nouvelle/', views.tache_create, name='tache_create'),
    path('taches/<int:pk>/modifier/', views.tache_update, name='tache_update'),
    path('taches/<int:pk>/supprimer/', views.tache_delete, name='tache_delete'),
    
    # Diagramme PERT
    path('projets/<int:projet_id>/diagramme/', views.diagramme, name='diagramme'),
]