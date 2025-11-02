from collections import defaultdict, deque

class PertCalculator:
    """
    Classe pour calculer les dates et marges d'un diagramme PERT
    Implémente l'algorithme CPM (Critical Path Method)
    """
    
    def __init__(self, taches):
        """
        Initialise le calculateur avec une liste de tâches
        Args:
            taches: QuerySet ou liste d'objets Tache
        """
        self.taches = list(taches)
        self.taches_dict = {t.code: t for t in self.taches}
        self.dates_debut_tot = {}
        self.dates_fin_tot = {}
        self.dates_debut_tard = {}
        self.dates_fin_tard = {}
    
    def calculer(self):
        """
        Lance tous les calculs PERT dans l'ordre
        Retourne True si succès, False si erreur
        """
        if not self.taches:
            return True
        
        try:
            # 1. Vérifier les dépendances circulaires
            if self._has_circular_dependency():
                raise ValueError("Dépendances circulaires détectées dans le projet !")
            
            # 2. Calcul des dates au plus tôt (forward pass)
            self._calculer_dates_tot()
            
            # 3. Calcul des dates au plus tard (backward pass)
            self._calculer_dates_tard()
            
            # 4. Calcul des marges
            self._calculer_marges()
            
            # 5. Sauvegarder tous les résultats
            self._sauvegarder_resultats()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors du calcul PERT: {e}")
            return False
    
    def _has_circular_dependency(self):
        """
        Détecte les dépendances circulaires avec un algorithme DFS
        Retourne True si cycle détecté
        """
        visited = set()
        rec_stack = set()
        
        def dfs(tache_code):
            """DFS récursif pour détecter les cycles"""
            visited.add(tache_code)
            rec_stack.add(tache_code)
            
            tache = self.taches_dict.get(tache_code)
            if tache:
                for dep in tache.dependances.all():
                    if dep.code not in visited:
                        if dfs(dep.code):
                            return True
                    elif dep.code in rec_stack:
                        return True
            
            rec_stack.remove(tache_code)
            return False
        
        # Tester depuis chaque tâche non visitée
        for tache in self.taches:
            if tache.code not in visited:
                if dfs(tache.code):
                    return True
        
        return False
    
    def _calculer_dates_tot(self):
        """
        Calcule les dates au plus tôt (forward pass)
        Pour chaque tâche: date_debut = max(dates_fin des dépendances)
        """
        # Initialiser toutes les dates à 0
        for t in self.taches:
            self.dates_debut_tot[t.code] = 0
            self.dates_fin_tot[t.code] = 0
        
        # Tri topologique pour traiter les tâches dans l'ordre
        ordre = self._tri_topologique()
        
        for tache_code in ordre:
            tache = self.taches_dict[tache_code]
            
            # Date de début = max des dates de fin des dépendances
            deps = list(tache.dependances.all())
            if deps:
                self.dates_debut_tot[tache_code] = max(
                    self.dates_fin_tot[d.code] for d in deps
                )
            else:
                # Tâche de départ
                self.dates_debut_tot[tache_code] = 0
            
            # Date de fin = date de début + durée
            self.dates_fin_tot[tache_code] = (
                self.dates_debut_tot[tache_code] + tache.duree
            )
    
    def _calculer_dates_tard(self):
        """
        Calcule les dates au plus tard (backward pass)
        Pour chaque tâche: date_fin_tard = min(dates_debut_tard des successeurs)
        """
        # Trouver la date de fin du projet (durée totale)
        date_fin_projet = max(self.dates_fin_tot.values())
        
        # Initialiser les dates au plus tard
        for t in self.taches:
            self.dates_fin_tard[t.code] = date_fin_projet
            self.dates_debut_tard[t.code] = date_fin_projet
        
        # Tâches finales (sans successeurs) : date_fin_tard = date_fin_tot
        for tache in self.taches:
            if not tache.successeurs.exists():
                self.dates_fin_tard[tache.code] = self.dates_fin_tot[tache.code]
                self.dates_debut_tard[tache.code] = (
                    self.dates_fin_tard[tache.code] - tache.duree
                )
        
        # Tri topologique inverse (traiter dans l'ordre inverse)
        ordre = list(reversed(self._tri_topologique()))
        
        for tache_code in ordre:
            tache = self.taches_dict[tache_code]
            
            # Date de fin au plus tard = min des dates de début au plus tard des successeurs
            successeurs = list(tache.successeurs.all())
            if successeurs:
                self.dates_fin_tard[tache_code] = min(
                    self.dates_debut_tard[s.code] for s in successeurs
                )
            
            # Date de début au plus tard = date de fin au plus tard - durée
            self.dates_debut_tard[tache_code] = (
                self.dates_fin_tard[tache_code] - tache.duree
            )
    
    def _calculer_marges(self):
        """
        Calcule les marges totale et libre pour chaque tâche
        - Marge totale = retard acceptable sans retarder le projet
        - Marge libre = retard acceptable sans retarder les successeurs
        """
        for tache in self.taches:
            # Marge totale = date début tard - date début tôt
            tache.marge_totale = (
                self.dates_debut_tard[tache.code] - 
                self.dates_debut_tot[tache.code]
            )
            
            # Marge libre = min(date début tôt successeurs) - date fin tôt
            successeurs = list(tache.successeurs.all())
            if successeurs:
                min_debut_successeurs = min(
                    self.dates_debut_tot[s.code] for s in successeurs
                )
                tache.marge_libre = (
                    min_debut_successeurs - self.dates_fin_tot[tache.code]
                )
            else:
                # Pas de successeurs = marge libre = marge totale
                tache.marge_libre = tache.marge_totale
    
    def _tri_topologique(self):
        """
        Effectue un tri topologique des tâches (algorithme de Kahn avec BFS)
        Retourne la liste des codes de tâches dans l'ordre topologique
        """
        # Compter les dépendances entrantes de chaque tâche
        in_degree = defaultdict(int)
        
        for tache in self.taches:
            if tache.code not in in_degree:
                in_degree[tache.code] = 0
            for dep in tache.dependances.all():
                in_degree[tache.code] += 1
        
        # File pour le BFS - commencer par les tâches sans dépendances
        queue = deque([t.code for t in self.taches if in_degree[t.code] == 0])
        ordre = []
        
        # BFS
        while queue:
            tache_code = queue.popleft()
            ordre.append(tache_code)
            
            # Pour chaque successeur, diminuer son degré entrant
            tache = self.taches_dict[tache_code]
            for successeur in tache.successeurs.all():
                in_degree[successeur.code] -= 1
                # Si plus de dépendances, ajouter à la file
                if in_degree[successeur.code] == 0:
                    queue.append(successeur.code)
        
        return ordre
    
    def _sauvegarder_resultats(self):
        """Sauvegarde tous les résultats calculés dans la base de données"""
        for tache in self.taches:
            tache.date_debut_tot = self.dates_debut_tot[tache.code]
            tache.date_fin_tot = self.dates_fin_tot[tache.code]
            tache.date_debut_tard = self.dates_debut_tard[tache.code]
            tache.date_fin_tard = self.dates_fin_tard[tache.code]
            # marge_totale et marge_libre déjà assignées dans _calculer_marges
            tache.save()
    
    def get_chemin_critique(self):
        """
        Retourne la liste ordonnée des tâches du chemin critique
        (tâches avec marge totale = 0)
        """
        taches_critiques = [t for t in self.taches if t.marge_totale == 0]
        # Trier par date de début au plus tôt
        return sorted(taches_critiques, key=lambda t: t.date_debut_tot)