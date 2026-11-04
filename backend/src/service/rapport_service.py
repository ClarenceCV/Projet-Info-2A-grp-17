"""Service de génération de rapports PDF (FO3)."""

import io
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF

from service.comparaison_pays_service import ComparaisonPaysService
from service.evolution_service import EvolutionService


class LaborScopePDF(FPDF):
    """Classe FPDF personnalisée pour l'en-tête et le pied de page du rapport."""

    def header(self) -> None:
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
        self.set_y(-15)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


class RapportService:
    """Service d'assemblage et de génération de rapports PDF synthétiques."""

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

    def conclusion(self, stats: dict[str, dict[str, Any]], df_comparaison: pd.DataFrame) -> str:
        """Génère des phrases automatiques d'analyse à partir des chiffres calculés."""
        if not stats:
            return "Aucune donnee disponible pour etablir une conclusion."

        phrases = []

        # Analyse d'évolution par pays
        for pays, s in stats.items():
            sens = "augmente" if s["evolution"] >= 0 else "diminue"
            diff_abs = abs(s["evolution"])
            phrases.append(
                f"Entre {s['periode_debut']} et {s['periode_fin']}, le marche dans le pays {s['nom_pays']} ({pays}) "
                f"a {sens} de {diff_abs:.2f} points (passant de {s['val_debut']:.2f} a {s['val_fin']:.2f})."
            )

        # Classement issu de la comparaison
        if not df_comparaison.empty and "valeur" in df_comparaison.columns:
            df_sorted = df_comparaison.sort_values("valeur", ascending=False)
            top_row = df_sorted.iloc[0]
            bottom_row = df_sorted.iloc[-1]
            phrases.append(
                f"Sur la periode la plus recente, {top_row.get('nom_pays', top_row['code_iso'])} presente la valeur la plus elevee "
                f"({top_row['valeur']:.2f}), tandis que {bottom_row.get('nom_pays', bottom_row['code_iso'])} enregistre la valeur la plus basse ({bottom_row['valeur']:.2f})."
            )

        return " ".join(phrases)

    def _generer_graphique_bytes(self, df_evolution: pd.DataFrame) -> io.BytesIO:
        """Génère un graphique d'évolution Matplotlib en mémoire (sans sauvegarde disque)."""
        fig, ax = plt.subplots(figsize=(7, 3.5))

        for nom_pays, group in df_evolution.groupby("nom_pays"):
            group_sorted = group.sort_values("periode")
            ax.plot(group_sorted["periode"], group_sorted["valeur"], marker="o", label=nom_pays)

        ax.set_title("Evolution Temporelle de l'Indicateur", fontsize=11, fontweight="bold")
        ax.set_xlabel("Periode")
        ax.set_ylabel("Valeur")
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
        # 1. Appel des services
        evolution = EvolutionService().evolution(code_indicateur, pays, classif1, sexe, n_periodes)
        comparaison = ComparaisonPaysService().comparer_pays(code_indicateur, classif1, pays, sexe)

        # 2. Calculs statistiques et conclusion
        stats = self.resume_statistique(evolution)
        conclusion_texte = self.conclusion(stats, comparaison)

        # 3. Assemblage FPDF2
        pdf = LaborScopePDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "", 11)

        # Section Métadonnées
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "1. Parametres de la Synthese", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(
            0,
            6,
            f"Indicateur : {code_indicateur}\nPays analyses : {', '.join(pays)}\nClassification : {classif1} | Sexe : {sexe}",
        )
        pdf.ln(4)

        # Section Graphique
        if not evolution.empty:
            img_buf = self._generer_graphique_bytes(evolution)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "2. Graphique d'Evolution", new_x="LMARGIN", new_y="NEXT")
            pdf.image(img_buf, w=170)
            pdf.ln(5)

        # Section Résumé Statistique (Tableau)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "3. Resume Statistique", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 9)

        # En-tête Tableau
        col_widths = [35, 25, 25, 25, 30]
        pdf.cell(col_widths[0], 7, "Pays", border=1)
        pdf.cell(col_widths[1], 7, "Min", border=1)
        pdf.cell(col_widths[2], 7, "Max", border=1)
        pdf.cell(col_widths[3], 7, "Moyenne", border=1)
        pdf.cell(col_widths[4], 7, "Evolution", border=1, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        for st_data in stats.values():
            pdf.cell(col_widths[0], 6, str(st_data["nom_pays"])[:18], border=1)
            pdf.cell(col_widths[1], 6, f"{st_data['min']:.2f}", border=1)
            pdf.cell(col_widths[2], 6, f"{st_data['max']:.2f}", border=1)
            pdf.cell(col_widths[3], 6, f"{st_data['moyenne']:.2f}", border=1)
            pdf.cell(
                col_widths[4],
                6,
                f"{st_data['evolution']:+.2f}",
                border=1,
                new_x="LMARGIN",
                new_y="NEXT",
            )

        pdf.ln(6)

        # Section Conclusion Automatique
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "4. Analyse & Conclusion Automatique", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, conclusion_texte)

        return bytes(pdf.output())
