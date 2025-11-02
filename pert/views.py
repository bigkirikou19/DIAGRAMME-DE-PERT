from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
import json

from .models import Projet, Tache
from .forms import ProjetForm, TacheForm
from .pert_calculator import PertCalculator


def home(request):
    """Page d'accueil"""
    return render(request, 'pert/home.html')


def projet_list(request):
    """Liste de tous les projets"""
    projets = Projet.objects.all()
    return render(request, 'pert/projet_list.html', {
        'projets': projets
    })


def projet_create(request):
    """Créer un nouveau projet"""
    if request.method == 'POST':
        form = ProjetForm(request.POST)
        if form.is_valid():
            projet = form.save()
            messages.success(request, f'Projet "{projet.nom}" créé avec succès !')
            return redirect('projet_detail', pk=projet.pk)
    else:
        form = ProjetForm()
    
    return render(request, 'pert/projet_form.html', {
        'form': form,
        'action': 'Créer'
    })


def projet_detail(request, pk):
    """Afficher les détails d'un projet et ses tâches"""
    projet = get_object_or_404(Projet, pk=pk)
    taches = projet.taches.all().order_by('code')
    
    return render(request, 'pert/projet_detail.html', {
        'projet': projet,
        'taches': taches,
        'taches_critiques': projet.taches_critiques,
        'duree_totale': projet.duree_totale,
    })


def projet_update(request, pk):
    """Modifier un projet existant"""
    projet = get_object_or_404(Projet, pk=pk)
    
    if request.method == 'POST':
        form = ProjetForm(request.POST, instance=projet)
        if form.is_valid():
            projet = form.save()
            messages.success(request, f'Projet "{projet.nom}" modifié avec succès !')
            return redirect('projet_detail', pk=projet.pk)
    else:
        form = ProjetForm(instance=projet)
    
    return render(request, 'pert/projet_form.html', {
        'form': form,
        'projet': projet,
        'action': 'Modifier'
    })


def projet_delete(request, pk):
    """Supprimer un projet"""
    projet = get_object_or_404(Projet, pk=pk)
    
    if request.method == 'POST':
        nom = projet.nom
        projet.delete()
        messages.success(request, f'Projet "{nom}" supprimé avec succès !')
        return redirect('projet_list')
    
    return render(request, 'pert/projet_confirm_delete.html', {
        'projet': projet
    })


def tache_create(request, projet_id):
    """Créer une nouvelle tâche dans un projet"""
    projet = get_object_or_404(Projet, pk=projet_id)
    
    if request.method == 'POST':
        form = TacheForm(request.POST, projet=projet)
        if form.is_valid():
            tache = form.save(commit=False)
            tache.projet = projet
            tache.save()
            form.save_m2m()  # Sauvegarder les relations ManyToMany (dépendances)
            
            # Recalculer le PERT après ajout de la tâche
            _recalculer_pert(projet)
            
            messages.success(request, f'Tâche "{tache.code}" ajoutée avec succès !')
            return redirect('projet_detail', pk=projet.pk)
    else:
        form = TacheForm(projet=projet)
    
    # Récupérer les tâches disponibles pour les dépendances
    taches_disponibles = projet.taches.all().order_by('code')
    
    return render(request, 'pert/tache_form.html', {
        'form': form,
        'projet': projet,
        'taches_disponibles': taches_disponibles,
        'action': 'Créer'
    })


def tache_update(request, pk):
    """Modifier une tâche existante"""
    tache = get_object_or_404(Tache, pk=pk)
    projet = tache.projet
    
    if request.method == 'POST':
        form = TacheForm(request.POST, instance=tache, projet=projet)
        if form.is_valid():
            tache = form.save()
            
            # Recalculer le PERT après modification
            _recalculer_pert(projet)
            
            messages.success(request, f'Tâche "{tache.code}" modifiée avec succès !')
            return redirect('projet_detail', pk=projet.pk)
    else:
        form = TacheForm(instance=tache, projet=projet)
    
    # Récupérer les tâches disponibles (sauf la tâche courante)
    taches_disponibles = projet.taches.exclude(pk=tache.pk).order_by('code')
    
    return render(request, 'pert/tache_form.html', {
        'form': form,
        'projet': projet,
        'tache': tache,
        'taches_disponibles': taches_disponibles,
        'action': 'Modifier'
    })


def tache_delete(request, pk):
    """Supprimer une tâche"""
    tache = get_object_or_404(Tache, pk=pk)
    projet = tache.projet
    
    if request.method == 'POST':
        code = tache.code
        tache.delete()
        
        # Recalculer le PERT après suppression
        _recalculer_pert(projet)
        
        messages.success(request, f'Tâche "{code}" supprimée avec succès !')
        return redirect('projet_detail', pk=projet.pk)
    
    return render(request, 'pert/tache_confirm_delete.html', {
        'tache': tache,
        'projet': projet
    })


def diagramme(request, projet_id):
    """Afficher le diagramme PERT d'un projet"""
    projet = get_object_or_404(Projet, pk=projet_id)
    taches = projet.taches.all()
    
    # Recalculer le PERT avant l'affichage
    _recalculer_pert(projet)
    
    # Préparer les données pour le JavaScript
    taches_json = []
    for tache in taches:
        taches_json.append({
            'code': tache.code,
            'nom': tache.nom,
            'duree': tache.duree,
            'dependances': tache.get_dependances_codes(),
            'date_debut_tot': tache.date_debut_tot,
            'date_fin_tot': tache.date_fin_tot,
            'date_debut_tard': tache.date_debut_tard,
            'date_fin_tard': tache.date_fin_tard,
            'marge_totale': tache.marge_totale,
            'marge_libre': tache.marge_libre,
        })
    
    # Chemin critique
    chemin_critique = list(projet.chemin_critique)
    chemin_critique_codes = [t.code for t in chemin_critique]
    
    return render(request, 'pert/diagramme.html', {
        'projet': projet,
        'taches': taches,
        'taches_json': json.dumps(taches_json),
        'chemin_critique': chemin_critique,
        'chemin_critique_codes': json.dumps(chemin_critique_codes),
        'taches_critiques': projet.taches_critiques,
        'duree_totale': projet.duree_totale,
        'marge_max': projet.marge_max,
    })


def _recalculer_pert(projet):
    """
    Fonction utilitaire pour recalculer les dates et marges PERT d'un projet
    """
    taches = projet.taches.all()
    if taches.exists():
        try:
            calculator = PertCalculator(taches)
            success = calculator.calculer()
            if not success:
                messages.warning(
                    None, 
                    "Erreur lors du calcul PERT. Vérifiez les dépendances."
                )
        except ValueError as e:
            messages.error(None, f"Erreur: {str(e)}")