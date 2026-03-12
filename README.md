# pointage-employes

Application de pointage en **PHP** (sans dépendances externes) pour enregistrer les entrées/sorties des employés et consulter le récapitulatif du jour.

## Lancer l'application

```bash
php -S 0.0.0.0:8000
```

Puis ouvrir `http://localhost:8000`.

## Structure

- `index.php` : interface web et contrôleur principal.
- `src/PointageService.php` : logique métier (enregistrement et calcul des heures).
- `storage/pointages.json` : stockage des pointages.

## Notes

- Les pointages sont enregistrés dans un fichier JSON local.
- Le calcul des heures travaillées cumule les paires `entree`/`sortie` par employé pour la date du jour.
