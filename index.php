<?php

declare(strict_types=1);

require_once __DIR__ . '/src/PointageService.php';

$service = new PointageService(__DIR__ . '/storage/pointages.json');
$message = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $employe = trim((string) ($_POST['employe'] ?? ''));
    $type = (string) ($_POST['type'] ?? '');

    if ($employe === '' || !in_array($type, ['entree', 'sortie'], true)) {
        $message = ['type' => 'erreur', 'texte' => 'Veuillez fournir un nom et un type valide.'];
    } else {
        $service->enregistrer($employe, $type);
        $message = ['type' => 'succes', 'texte' => 'Pointage enregistré avec succès.'];
    }
}

$pointages = $service->listerAujourdhui();
$heuresParEmploye = $service->heuresAujourdhuiParEmploye();
?>
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Pointage employés</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; background: #f5f7fb; color: #1f2937; }
        .card { background: white; border-radius: 12px; padding: 1rem 1.25rem; box-shadow: 0 2px 10px rgba(0,0,0,.05); margin-bottom: 1rem; }
        form { display: flex; gap: .75rem; flex-wrap: wrap; align-items: end; }
        label { display: flex; flex-direction: column; font-size: .9rem; }
        input, select, button { padding: .6rem; border-radius: 8px; border: 1px solid #cbd5e1; }
        button { background: #2563eb; color: white; border: none; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: .5rem; border-bottom: 1px solid #e2e8f0; }
        .msg { padding: .7rem; border-radius: 8px; margin-bottom: 1rem; }
        .succes { background: #dcfce7; color: #166534; }
        .erreur { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <h1>Application de pointage des employés (PHP)</h1>

    <?php if ($message !== null): ?>
        <p class="msg <?= htmlspecialchars($message['type']) ?>"><?= htmlspecialchars($message['texte']) ?></p>
    <?php endif; ?>

    <section class="card">
        <h2>Nouveau pointage</h2>
        <form method="post">
            <label>
                Employé
                <input type="text" name="employe" required placeholder="Ex: Alice">
            </label>
            <label>
                Type
                <select name="type" required>
                    <option value="entree">Entrée</option>
                    <option value="sortie">Sortie</option>
                </select>
            </label>
            <button type="submit">Enregistrer</button>
        </form>
    </section>

    <section class="card">
        <h2>Pointages du jour</h2>
        <table>
            <thead>
            <tr><th>Employé</th><th>Type</th><th>Horodatage</th></tr>
            </thead>
            <tbody>
            <?php if ($pointages === []): ?>
                <tr><td colspan="3">Aucun pointage aujourd'hui.</td></tr>
            <?php else: ?>
                <?php foreach ($pointages as $pointage): ?>
                    <tr>
                        <td><?= htmlspecialchars($pointage['employe']) ?></td>
                        <td><?= htmlspecialchars(ucfirst($pointage['type'])) ?></td>
                        <td><?= htmlspecialchars((new DateTimeImmutable($pointage['horodatage']))->format('d/m/Y H:i:s')) ?></td>
                    </tr>
                <?php endforeach; ?>
            <?php endif; ?>
            </tbody>
        </table>
    </section>

    <section class="card">
        <h2>Heures cumulées (aujourd'hui)</h2>
        <table>
            <thead><tr><th>Employé</th><th>Heures</th></tr></thead>
            <tbody>
            <?php if ($heuresParEmploye === []): ?>
                <tr><td colspan="2">Pas de calcul disponible.</td></tr>
            <?php else: ?>
                <?php foreach ($heuresParEmploye as $employe => $heures): ?>
                    <tr>
                        <td><?= htmlspecialchars($employe) ?></td>
                        <td><?= htmlspecialchars((string) $heures) ?> h</td>
                    </tr>
                <?php endforeach; ?>
            <?php endif; ?>
            </tbody>
        </table>
    </section>
</body>
</html>
