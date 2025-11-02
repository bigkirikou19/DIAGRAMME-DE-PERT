from django.db import models
from django.core.exceptions import ValidationError

class Projet(models.Model):
    """Modèle représentant un projet PERT"""
    nom = models.CharField(max_length=200, verbose_name="Nom du projet")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-date_creation']
    
    def __str__(self):
        return self.nom
    
    @property
    def taches_critiques(self):
        """Retourne les tâches critiques (marge totale = 0)"""
        return self.taches.filter(marge_totale=0)
    
    @property
    def duree_totale(self):
        """Calcule la durée totale du projet"""
        taches = self.taches.all()
        if not taches.exists():
            return 0
        dates_fin = [t.date_fin_tot for t in taches if t.date_fin_tot is not None]
        return max(dates_fin) if dates_fin else 0
    
    @property
    def marge_max(self):
        """Retourne la marge maximale du projet"""
        taches = self.taches.all()
        if not taches.exists():
            return 0
        marges = [t.marge_totale for t in taches if t.marge_totale is not None]
        return max(marges) if marges else 0
    
    @property
    def chemin_critique(self):
        """Retourne le chemin critique du projet ordonné"""
        return self.taches_critiques.order_by('date_debut_tot')


class Tache(models.Model):
    """Modèle représentant une tâche dans un projet PERT"""
    projet = models.ForeignKey(
        Projet, 
        on_delete=models.CASCADE, 
        related_name='taches',
        verbose_name="Projet"
    )
    code = models.CharField(max_length=10, verbose_name="Code de la tâche")
    nom = models.CharField(max_length=200, verbose_name="Nom de la tâche")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    duree = models.IntegerField(verbose_name="Durée (en jours)")
    
    # Dépendances entre tâches
    dependances = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        blank=True, 
        related_name='successeurs',
        verbose_name="Dépendances (tâches à terminer avant)"
    )
    
    # Calculs PERT - dates au plus tôt
    date_debut_tot = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Date de début au plus tôt"
    )
    date_fin_tot = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Date de fin au plus tôt"
    )
    
    # Calculs PERT - dates au plus tard
    date_debut_tard = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Date de début au plus tard"
    )
    date_fin_tard = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Date de fin au plus tard"
    )
    
    # Marges
    marge_totale = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Marge totale"
    )
    marge_libre = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Marge libre"
    )
    
    class Meta:
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
        ordering = ['code']
        unique_together = ['projet', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def clean(self):
        """Validation pour éviter les dépendances circulaires"""
        super().clean()
        
        # Vérifier que le code est en majuscules
        if self.code:
            self.code = self.code.upper()
        
        # Vérifier la durée positive
        if self.duree and self.duree <= 0:
            raise ValidationError("La durée doit être supérieure à 0")
    
    def save(self, *args, **kwargs):
        """Surcharge pour forcer le code en majuscules"""
        self.code = self.code.upper()
        super().save(*args, **kwargs)
    
    @property
    def est_critique(self):
        """Détermine si la tâche est critique"""
        return self.marge_totale == 0 if self.marge_totale is not None else False
    
    def get_dependances_codes(self):
        """Retourne la liste des codes des dépendances"""
        return [dep.code for dep in self.dependances.all()]