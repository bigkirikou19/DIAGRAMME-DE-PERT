from django import forms
from .models import Projet, Tache

class ProjetForm(forms.ModelForm):
    """Formulaire pour créer/modifier un projet"""
    
    class Meta:
        model = Projet
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Ex: Construction d\'un bâtiment'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Décrivez votre projet en détail...',
                'rows': 4
            }),
        }
        labels = {
            'nom': 'Nom du projet',
            'description': 'Description',
        }


class TacheForm(forms.ModelForm):
    """Formulaire pour créer/modifier une tâche"""
    
    class Meta:
        model = Tache
        fields = ['code', 'nom', 'description', 'duree', 'dependances']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition uppercase',
                'placeholder': 'Ex: A',
                'maxlength': '10',
                'style': 'text-transform: uppercase;'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Ex: Fondations'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Décrivez la tâche en détail...',
                'rows': 3
            }),
            'duree': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
                'placeholder': 'Ex: 10',
                'min': '1'
            }),
            'dependances': forms.CheckboxSelectMultiple(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
        }
        labels = {
            'code': 'Code',
            'nom': 'Nom de la tâche',
            'description': 'Description',
            'duree': 'Durée (en jours)',
            'dependances': 'Dépendances (tâches à terminer avant)',
        }
    
    def __init__(self, *args, **kwargs):
        projet = kwargs.pop('projet', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les dépendances aux tâches du même projet
        if projet:
            # Exclure la tâche courante si elle existe
            if self.instance.pk:
                self.fields['dependances'].queryset = Tache.objects.filter(
                    projet=projet
                ).exclude(pk=self.instance.pk)
            else:
                self.fields['dependances'].queryset = Tache.objects.filter(
                    projet=projet
                )
        else:
            self.fields['dependances'].queryset = Tache.objects.none()
    
    def clean_code(self):
        """Valider et formater le code en majuscules"""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
        return code
    
    def clean_duree(self):
        """Valider que la durée est positive"""
        duree = self.cleaned_data.get('duree')
        if duree and duree <= 0:
            raise forms.ValidationError("La durée doit être supérieure à 0")
        return duree
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        # Vérifier l'unicité du code dans le projet
        code = cleaned_data.get('code')
        if code and hasattr(self.instance, 'projet'):
            projet = self.instance.projet
            existing = Tache.objects.filter(projet=projet, code=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    f"Le code '{code}' existe déjà dans ce projet. Choisissez un code unique."
                )
        
        return cleaned_data