from django.contrib import admin
from .models import Projet, Tache


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    """Interface d'administration pour les projets"""
    list_display = ['nom', 'date_creation', 'date_modification', 'nb_taches']
    list_filter = ['date_creation']
    search_fields = ['nom', 'description']
    date_hierarchy = 'date_creation'
    
    def nb_taches(self, obj):
        """Affiche le nombre de tâches"""
        return obj.taches.count()
    nb_taches.short_description = 'Nombre de tâches'


@admin.register(Tache)
class TacheAdmin(admin.ModelAdmin):
    """Interface d'administration pour les tâches"""
    list_display = ['code', 'nom', 'projet', 'duree', 'marge_totale', 'est_critique']
    list_filter = ['projet', 'marge_totale']
    search_fields = ['code', 'nom', 'description']
    filter_horizontal = ['dependances']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('projet', 'code', 'nom', 'description', 'duree')
        }),
        ('Dépendances', {
            'fields': ('dependances',)
        }),
        ('Calculs PERT (automatique)', {
            'fields': (
                'date_debut_tot', 'date_fin_tot',
                'date_debut_tard', 'date_fin_tard',
                'marge_totale', 'marge_libre'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = [
        'date_debut_tot', 'date_fin_tot',
        'date_debut_tard', 'date_fin_tard',
        'marge_totale', 'marge_libre'
    ]