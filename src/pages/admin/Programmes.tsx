import AdminShell from "../../components/AdminShell";
import CatalogueManager from "../../components/CatalogueManager";
import Icon from "../../components/Icon";

/** Administrator: the whole catalogue, both institutions (academic heads manage their own from /equipe/catalogue). */
export default function Programmes() {
  return (
    <AdminShell title="Des parcours clairs, des informations vérifiées" sub="Formations, spécialités, programmes pédagogiques, matières et conditions d’admission · IIT / ISB · Campagne 2026-2027">
      <div className="warnbox"><Icon name="shield" size={15} color="#8d6417" />SmartCampus.pdf présente le projet, pas les conditions officielles. Prérequis, durées et modalités doivent être confirmés par l’établissement avant d’activer un élément.</div>
      <CatalogueManager />
    </AdminShell>
  );
}
