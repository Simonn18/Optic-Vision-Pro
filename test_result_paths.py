"""Test non-graphique de la logique de chemins des mesures.

Reproduit fidèlement :
  - _racine_result()           (helper ajouté)
  - l'emplacement d'ECRITURE de mesure()  (racine_calcul/mesures_json)
  - l'ordre de RECHERCHE de _charger_image()

But : vérifier que le JSON écrit par mesure() est bien le PREMIER trouvé par
_charger_image() au changement d'image, avec et sans dossier de travail.
"""
import os
import glob
import tempfile
import shutil


# ── Logique recopiée à l'identique depuis newapp.py ───────────────────────

def _racine_result(chemin_dossier, chemin_image):
    """Cf. MainWindow._racine_result."""
    if chemin_dossier:
        return chemin_dossier
    chemin = chemin_image
    if not chemin:
        return None
    dossier_image = os.path.dirname(chemin)
    if os.path.basename(dossier_image) == "fundus_images":
        dossier_image = os.path.dirname(dossier_image)
    return dossier_image


def chemin_ecriture_mesure(chemin_dossier, chemin_image, nom):
    """Cf. mesure() : racine_calcul = <base>/results ; JSON dans mesures_json/."""
    base = _racine_result(chemin_dossier, chemin_image)
    racine_calcul = os.path.join(base, "results")
    return os.path.join(racine_calcul, "mesures_json", f"{nom}_data.json")


def chemin_lecture_charger_image(chemin_dossier, chemin):
    """Cf. _charger_image() : reconstruit la liste de candidats dans l'ordre,
    et renvoie (premier_existant, liste_candidats)."""
    nom_base = os.path.splitext(os.path.basename(chemin))[0]
    while nom_base.endswith("_OVP"):
        nom_base = nom_base[:-4]
    nom_json = nom_base
    nom_ovp = f"{nom_base}_OVP"

    dossier_image = os.path.dirname(chemin)
    if os.path.basename(dossier_image) == "fundus_images":
        dossier_image = os.path.dirname(dossier_image)
    parent_image = os.path.dirname(dossier_image)

    def _json_image_results(nom):
        return os.path.join(dossier_image, "results", "mesures_json", f"{nom}_data.json")

    def _json_parent_glob(nom):
        pattern = os.path.join(parent_image, "*_fundus_images_code_OVP", "results", "mesures_json", f"{nom}_data.json")
        r = glob.glob(pattern)
        return r[0] if r else ""

    racine_result = _racine_result(chemin_dossier, chemin)
    chemin_json = None
    tous_candidats = []
    for nom in (nom_ovp, nom_json):
        candidats = []
        if racine_result:
            candidats.append(os.path.join(racine_result, "results", "mesures_json", f"{nom}_data.json"))
        if chemin_dossier:
            candidats.append(os.path.join(chemin_dossier, f"{nom}_OVP", "results", "mesures_json", f"{nom}_data.json"))
            g = glob.glob(os.path.join(chemin_dossier, "*_fundus_images_code_OVP", "results", "mesures_json", f"{nom}_data.json"))
            candidats.append(g[0] if g else "")
        candidats.append(_json_image_results(nom))
        candidats.append(_json_parent_glob(nom))
        if chemin_dossier:
            candidats.append(os.path.join(chemin_dossier, "mesures_json", f"{nom}_data.json"))
            candidats.append(os.path.join(chemin_dossier, "results", "mesures_json", f"{nom}_data.json"))
        tous_candidats.extend(candidats)
        for candidat in candidats:
            if candidat and os.path.exists(candidat):
                chemin_json = candidat
                break
        if chemin_json:
            break
    return chemin_json, tous_candidats


# ── Harnais de test ───────────────────────────────────────────────────────

def _ecrire(chemin):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write('{"IMAGE_ID": "test"}')


resultats = []


def verifier(nom_scenario, ok, detail=""):
    statut = "OK  " if ok else "ECHEC"
    resultats.append(ok)
    print(f"[{statut}] {nom_scenario}{('  -> ' + detail) if detail else ''}")


def scenario_sans_dossier_travail():
    tmp = tempfile.mkdtemp()
    try:
        chemin_image = os.path.join(tmp, "patient", "fundus_images", "1.png")
        os.makedirs(os.path.dirname(chemin_image), exist_ok=True)
        open(chemin_image, "w").close()

        # mesure() écrit le JSON (nom sans _OVP, comme csv_to_jsons à partir de l'IMAGE_ID)
        ecrit = chemin_ecriture_mesure(None, chemin_image, "1")
        _ecrire(ecrit)

        # changement d'image -> on revient sur cette image
        lu, candidats = chemin_lecture_charger_image(None, chemin_image)

        canonique = os.path.join(_racine_result(None, chemin_image), "results", "mesures_json")
        verifier("Sans dossier de travail : JSON rechargé", lu == ecrit,
                 f"écrit={os.path.relpath(ecrit, tmp)} | lu={os.path.relpath(lu, tmp) if lu else None}")
        verifier("Sans dossier de travail : rechargé depuis le dossier results canonique",
                 lu and os.path.dirname(lu) == canonique)
    finally:
        shutil.rmtree(tmp)


def scenario_avec_dossier_travail():
    tmp = tempfile.mkdtemp()
    try:
        chemin_dossier = os.path.join(tmp, "travail")
        os.makedirs(chemin_dossier, exist_ok=True)
        chemin_image = os.path.join(tmp, "patient", "fundus_images", "2.png")
        os.makedirs(os.path.dirname(chemin_image), exist_ok=True)
        open(chemin_image, "w").close()

        ecrit = chemin_ecriture_mesure(chemin_dossier, chemin_image, "2")
        _ecrire(ecrit)

        lu, candidats = chemin_lecture_charger_image(chemin_dossier, chemin_image)

        canonique = os.path.join(chemin_dossier, "results", "mesures_json")
        verifier("Avec dossier de travail : JSON rechargé", lu == ecrit,
                 f"écrit={os.path.relpath(ecrit, tmp)} | lu={os.path.relpath(lu, tmp) if lu else None}")
        verifier("Avec dossier de travail : rechargé depuis le dossier results canonique",
                 lu and os.path.dirname(lu) == canonique)
    finally:
        shutil.rmtree(tmp)


def scenario_fresh_prioritaire_sur_archive():
    """Une archive _OVP plus ancienne existe : la mesure fraîche doit primer."""
    tmp = tempfile.mkdtemp()
    try:
        chemin_dossier = os.path.join(tmp, "travail")
        os.makedirs(chemin_dossier, exist_ok=True)
        chemin_image = os.path.join(tmp, "patient", "fundus_images", "3.png")
        os.makedirs(os.path.dirname(chemin_image), exist_ok=True)
        open(chemin_image, "w").close()

        # archive ancienne
        archive = os.path.join(chemin_dossier, "3_OVP", "results", "mesures_json", "3_data.json")
        _ecrire(archive)
        # mesure fraîche
        ecrit = chemin_ecriture_mesure(chemin_dossier, chemin_image, "3")
        _ecrire(ecrit)

        lu, _ = chemin_lecture_charger_image(chemin_dossier, chemin_image)
        verifier("Mesure fraîche prioritaire sur archive ancienne", lu == ecrit,
                 f"lu={os.path.relpath(lu, tmp) if lu else None}")
    finally:
        shutil.rmtree(tmp)


def scenario_image_ovp():
    """Image dont le nom porte déjà le suffixe _OVP."""
    tmp = tempfile.mkdtemp()
    try:
        chemin_image = os.path.join(tmp, "patient", "fundus_images", "4_OVP.png")
        os.makedirs(os.path.dirname(chemin_image), exist_ok=True)
        open(chemin_image, "w").close()

        # csv_to_jsons nomme d'après l'IMAGE_ID ; on teste le nom sans _OVP
        ecrit = chemin_ecriture_mesure(None, chemin_image, "4")
        _ecrire(ecrit)

        lu, _ = chemin_lecture_charger_image(None, chemin_image)
        verifier("Image _OVP : JSON (nom normalisé) rechargé", lu == ecrit,
                 f"lu={os.path.relpath(lu, tmp) if lu else None}")
    finally:
        shutil.rmtree(tmp)


def scenario_aucune_mesure_toolbox_masquee():
    """Aucun fichier de mesure : la recherche renvoie None -> la toolbox doit
    rester masquée/désactivée (dispo == False dans _maj_toolbox_mesures)."""
    tmp = tempfile.mkdtemp()
    try:
        chemin_image = os.path.join(tmp, "patient", "fundus_images", "9.png")
        os.makedirs(os.path.dirname(chemin_image), exist_ok=True)
        open(chemin_image, "w").close()

        # On NE crée aucun JSON de mesure.
        lu, _ = chemin_lecture_charger_image(None, chemin_image)
        dispo = bool(lu and os.path.exists(lu))  # logique de _maj_toolbox_mesures
        verifier("Aucune mesure : toolbox masquée (dispo == False)", dispo is False,
                 f"chemin_json={lu}")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    scenario_sans_dossier_travail()
    scenario_avec_dossier_travail()
    scenario_fresh_prioritaire_sur_archive()
    scenario_image_ovp()
    scenario_aucune_mesure_toolbox_masquee()
    print("-" * 60)
    if all(resultats):
        print(f"TOUS LES TESTS PASSENT ({len(resultats)}/{len(resultats)})")
    else:
        print(f"ECHECS : {resultats.count(False)}/{len(resultats)} test(s) en échec")
