import CatalogueManager from "../../components/CatalogueManager";
import { useAuth } from "../../lib/auth";

/** Academic head: manages the catalogue of their own institution (formations, specialties, programmes, subjects, conditions). */
export default function Catalogue() {
  const { user } = useAuth();
  const own = user?.role === "isb_head" ? "ISB" : "IIT";
  return (
    <div className="ws" style={{ gap: 18 }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, letterSpacing: -0.8, color: "var(--navy)" }}>Catalogue des formations · {own}</h1>
        <p className="p-muted" style={{ margin: "6px 0 0", fontSize: 13, color: "var(--muted3)" }}>Formations, spécialités, programmes pédagogiques, matières, frais de scolarité, modalités de paiement et conditions d’admission · Les informations officielles (frais, paiement, conditions) se publient avec une période de validité · Campagne 2026-2027</p>
      </div>
      <CatalogueManager scope={own} />
    </div>
  );
}
