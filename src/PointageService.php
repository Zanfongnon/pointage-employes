<?php

declare(strict_types=1);

final class PointageService
{
    public function __construct(private readonly string $storageFile)
    {
        if (!file_exists($this->storageFile)) {
            file_put_contents($this->storageFile, json_encode([], JSON_PRETTY_PRINT));
        }
    }

    public function enregistrer(string $employe, string $type): void
    {
        $pointages = $this->lire();

        $pointages[] = [
            'employe' => trim($employe),
            'type' => $type,
            'horodatage' => (new DateTimeImmutable())->format(DateTimeInterface::ATOM),
        ];

        $this->ecrire($pointages);
    }

    /** @return array<int, array{employe:string,type:string,horodatage:string}> */
    public function listerAujourdhui(): array
    {
        $aujourdhui = (new DateTimeImmutable('today'))->format('Y-m-d');

        return array_values(array_filter(
            $this->lire(),
            static fn (array $pointage): bool => str_starts_with($pointage['horodatage'], $aujourdhui)
        ));
    }

    /** @return array<string, float> */
    public function heuresAujourdhuiParEmploye(): array
    {
        $pointages = $this->listerAujourdhui();
        $groupes = [];

        foreach ($pointages as $pointage) {
            $groupes[$pointage['employe']][] = $pointage;
        }

        $resultat = [];

        foreach ($groupes as $employe => $lignes) {
            usort($lignes, static fn (array $a, array $b): int => strcmp($a['horodatage'], $b['horodatage']));

            $debut = null;
            $secondes = 0;

            foreach ($lignes as $ligne) {
                if ($ligne['type'] === 'entree') {
                    $debut = new DateTimeImmutable($ligne['horodatage']);
                    continue;
                }

                if ($ligne['type'] === 'sortie' && $debut instanceof DateTimeImmutable) {
                    $fin = new DateTimeImmutable($ligne['horodatage']);
                    $secondes += $fin->getTimestamp() - $debut->getTimestamp();
                    $debut = null;
                }
            }

            $resultat[$employe] = round(max(0, $secondes) / 3600, 2);
        }

        ksort($resultat);

        return $resultat;
    }

    /** @return array<int, array{employe:string,type:string,horodatage:string}> */
    private function lire(): array
    {
        $contenu = file_get_contents($this->storageFile);

        if ($contenu === false || $contenu === '') {
            return [];
        }

        $decode = json_decode($contenu, true);

        return is_array($decode) ? $decode : [];
    }

    /** @param array<int, array{employe:string,type:string,horodatage:string}> $pointages */
    private function ecrire(array $pointages): void
    {
        file_put_contents($this->storageFile, json_encode($pointages, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    }
}
