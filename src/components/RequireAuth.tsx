import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { homeFor, useAuth } from "../lib/auth";

/** Redirects to /connexion when signed out, and to the user's own home when the role is not allowed. */
export default function RequireAuth({ roles, children }: { roles?: string[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <p className="ws small">Chargement…</p>;
  if (!user) return <Navigate to="/connexion" state={{ from: loc.pathname }} replace />;
  if (roles && !roles.includes(user.role) && user.role !== "admin") return <Navigate to={homeFor(user.role)} replace />;
  return <>{children}</>;
}
