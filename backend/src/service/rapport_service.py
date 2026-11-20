"""Service de génération de rapports PDF (FO3)."""

import io
import unicodedata
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF

from service.comparaison_pays_service import ComparaisonPaysService
from service.evolution_service import EvolutionService
from service.indicateur_service import IndicateurService

# "Agg" : dessine directement en image, sans fenêtre. Indispensable dans une API, où le graphique
# est créé hors du fil principal (sous Windows, le moteur par défaut Tk refuse et plante).
# matplotlib ne choisit son moteur qu'au premier graphique : l'appeler après les imports suffit.
matplotlib.use("Agg")

MAPPING_SEXE = {
    "F": "Female",
    "M": "Male",
    "FEMALE": "Female",
    "MALE": "Male",
    "TOTAL": "Total",
}


def _nettoyer_texte_pdf(texte: str) -> str:
    """Garantit la compatibilité latin-1 pour la police standard Helvetica de FPDF."""
    try:
        texte.encode("latin-1")
        return texte
    except UnicodeEncodeError:
        normalise = unicodedata.normalize("NFKD", texte)
        return normalise.encode("latin-1", "ignore").decode("latin-1")


class LaborScopePDF(FPDF):
    """Classe FPDF personnalisée pour l'en-tête et le pied de page du rapport."""

    def header(self) -> None:
        """Méthode pour formater haut de page."""
        self.set_font("Helvetica", "B", 14)
        self.cell(
            0,
            10,
            "LaborScope - Rapport d'Analyse Comparative",
            border=False,
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self.ln(5)

    def footer(self) -> None:
        """Méthode pour formater le pied de page."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


class RapportService:
    """Service d'assemblage et de génération de rapports PDF synthétiques."""

    def _infos_indicateur(self, code_indicateur: str) -> tuple[str, str]:
        """Retourne (intitulé_complet, unité) à partir du code ILOSTAT."""
        try:
            indicateur = IndicateurService().trouver_par_code(code_indicateur)
        except (KeyError, OSError, ValueError, RuntimeError):
            indicateur = None

        if indicateur is not None and isinstance(getattr(indicateur, "libelle", None), str):
            intitule = f"{indicateur.libelle} ({indicateur.unite}) [{indicateur.code}]"
            return intitule, indicateur.unite

        return code_indicateur, ""

    def resume_statistique(self, df_evolution: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """Calcule min, max, moyenne et évolution globale par pays."""
        stats = {}
        if df_evolution.empty:
            return stats

        for (pays, nom_pays), group in df_evolution.groupby(["code_iso", "nom_pays"]):
            group_sorted = group.sort_values("periode")
            val_debut = group_sorted["valeur"].iloc[0]
            val_fin = group_sorted["valeur"].iloc[-1]
            diff = val_fin - val_debut

            stats[pays] = {
                "nom_pays": nom_pays,
                "min": float(group["valeur"].min()),
                "max": float(group["valeur"].max()),
                "moyenne": float(group["valeur"].mean()),
                "val_debut": float(val_debut),
                "val_fin": float(val_fin),
                "evolution": float(diff),
                "periode_debut": str(group_sorted["periode"].iloc[0]),
                "periode_fin": str(group_sorted["periode"].iloc[-1]),
            }
        return stats

    def conclusion(self, stats: dict[str, dict[str, Any]], comparaison: Any) -> str:
        """Génère des phrases automatiques d'analyse à partir des chiffres calculés."""
        if not stats:
            return "Aucune donnee disponible pour etablir une conclusion."

        phrases = []

        # 1. Analyse d'évolution par pays
        for pays, s in stats.items():
            sens = "augmente" if s["evolution"] >= 0 else "diminue"
            phrases.append(
                f"Entre {s['periode_debut']} et {s['periode_fin']}, le marche dans le pays "
                f"{s['nom_pays']} ({pays}) a {sens} de {abs(s['evolution']):.2f} points "
                f"(passant de {s['val_debut']:.2f} a {s['val_fin']:.2f})."
            )

        # 2. Classement issu de la comparaison
        df_comparaison, periode_reference = self._normaliser_comparaison(comparaison)
        if not df_comparaison.empty and "valeur" in df_comparaison.columns:
            df_sorted = df_comparaison.sort_values("valeur", ascending=False)
            haut, bas = df_sorted.iloc[0], df_sorted.iloc[-1]
            debut_phrase = (
                f"Pour la periode de reference {periode_reference}"
                if periode_reference
                else "Sur la periode la plus recente"
            )
            phrases.append(
                f"{debut_phrase}, {self._nom_pays(haut)} presente "
                f"la valeur la plus elevee ({haut['valeur']:.2f}), "
                f"tandis que {self._nom_pays(bas)} enregistre "
                f"la valeur la plus basse ({bas['valeur']:.2f})."
            )

        return " ".join(phrases)

    @staticmethod
    def _normaliser_comparaison(comparaison: Any) -> tuple[pd.DataFrame, str | None]:
        """
        Met le résultat de la comparaison entre pays sous une forme unique.

        Args:
            comparaison (Any): dict (clé 'classement', 'observations' ou 'data') ou DataFrame

        Returns:
            tuple[pd.DataFrame, str | None]: le classement et la période de référence (si connue)
        """
        if isinstance(comparaison, pd.DataFrame):
            return comparaison, None
        if isinstance(comparaison, dict):
            # "classement" est un DataFrame : on ne peut pas écrire `a or b` (pandas refuse
            # de dire si un DataFrame est « vrai »), on prend la première clé présente.
            for cle in ("classement", "observations", "data"):
                if comparaison.get(cle) is not None:
                    return pd.DataFrame(comparaison[cle]), comparaison.get("periode_reference")
            return pd.DataFrame(), comparaison.get("periode_reference")
        return pd.DataFrame(), None

    @staticmethod
    def _nom_pays(ligne: pd.Series) -> str:
        """Nom du pays d'une ligne du classement (à défaut, son code ISO)."""
        return ligne.get("nom_pays") or ligne.get("pays") or ligne.get("code_iso", "N/A")

    @staticmethod
    def _ecrire_tableau_stats(pdf: FPDF, stats: dict[str, dict[str, Any]]) -> None:
        """Écrit la partie « 3. Resume Statistique » : tableau min / max / moyenne / évolution."""
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "3. Resume Statistique", new_x="LMARGIN", new_y="NEXT")

        largeurs = [35, 25, 25, 25, 30]
        pdf.set_font("Helvetica", "B", 9)
        for largeur, titre in zip(largeurs[:-1], ["Pays", "Min", "Max", "Moyenne"]):
            pdf.cell(largeur, 7, titre, border=1)
        pdf.cell(largeurs[-1], 7, "Evolution", border=1, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        for s in stats.values():
            # nom nettoyé : la police Helvetica du PDF ne connaît que les caractères latin-1
            pdf.cell(largeurs[0], 6, _nettoyer_texte_pdf(str(s["nom_pays"])[:18]), border=1)
            pdf.cell(largeurs[1], 6, f"{s['min']:.2f}", border=1)
            pdf.cell(largeurs[2], 6, f"{s['max']:.2f}", border=1)
            pdf.cell(largeurs[3], 6, f"{s['moyenne']:.2f}", border=1)
            pdf.cell(
                largeurs[4], 6, f"{s['evolution']:+.2f}", border=1, new_x="LMARGIN", new_y="NEXT"
            )

    def _generer_graphique_bytes(
        self,
        df_evolution: pd.DataFrame,
        titre_indicateur: str = "Evolution Temporelle de l'Indicateur",
        unite: str = "",
    ) -> io.BytesIO:
        """Génère un graphique d'évolution Matplotlib en mémoire (sans sauvegarde disque)."""
        fig, ax = plt.subplots(figsize=(7, 3.5))

        for nom_pays, group in df_evolution.groupby("nom_pays"):
            group_sorted = group.sort_values("periode")
            ax.plot(group_sorted["periode"], group_sorted["valeur"], marker="o", label=nom_pays)

        ax.set_title(titre_indicateur, fontsize=10, fontweight="bold")
        ax.set_xlabel("Periode")
        ax.set_ylabel(f"Valeur ({unite})" if unite else "Valeur")
        ax.legend(loc="best")
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()

        img_buf = io.BytesIO()
        plt.savefig(img_buf, format="png", dpi=150)
        plt.close(fig)
        img_buf.seek(0)
        return img_buf

    def generer(
        self,
        code_indicateur: str,
        pays: list[str],
        classif1: str,
        sexe: str = "Total",
        n_periodes: int = 8,
    ) -> bytes:
        """Renvoie le contenu binaire du fichier PDF généré."""
        sexe_db = MAPPING_SEXE.get(sexe.upper(), sexe)
        intitule_indicateur, unite_indicateur = self._infos_indicateur(code_indicateur)

        # 1. Appel des services backend
        evolution = EvolutionService().evolution(
            code_indicateur, pays, classif1, sexe_db, n_periodes
        )

        if evolution.empty and classif1.lower() == "total":
            for alternative in ["15+", "OC2_SKILL_TOTAL", "AGE_AGGREGATE_TOTAL"]:
                evolution_alt = EvolutionService().evolution(
                    code_indicateur, pays, alternative, sexe_db, n_periodes
                )
                if not evolution_alt.empty:
                    evolution = evolution_alt
                    classif1 = alternative
                    break

        comparaison = ComparaisonPaysService().comparer_pays(
            code_indicateur, classif1, pays, sexe_db
        )

        # 2. Calculs statistiques et conclusion
        stats = self.resume_statistique(evolution)
        conclusion_texte = self.conclusion(stats, comparaison)

        # 3. Assemblage FPDF2
        pdf = LaborScopePDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "", 11)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "1. Parametres de la Synthese", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(
            0,
            6,
            _nettoyer_texte_pdf(
                f"Indicateur : {intitule_indicateur}\n"
                f"Pays analyses : {', '.join(pays)}\n"
                f"Classification : {classif1} | Sexe : {sexe_db}"
            ),
        )
        pdf.ln(4)

        if not evolution.empty:
            titre_graph = (
                intitule_indicateur.split(" [")[0]
                if " [" in intitule_indicateur
                else "Evolution Temporelle de l'Indicateur"
            )
            img_buf = self._generer_graphique_bytes(
                evolution,
                titre_indicateur=titre_graph,
                unite=unite_indicateur,
            )
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "2. Graphique d'Evolution", new_x="LMARGIN", new_y="NEXT")
            pdf.image(img_buf, w=170)
            pdf.ln(5)

        self._ecrire_tableau_stats(pdf, stats)
        pdf.ln(6)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "4. Analyse & Conclusion Automatique", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _nettoyer_texte_pdf(conclusion_texte))

        return bytes(pdf.output())
