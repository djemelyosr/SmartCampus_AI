import { CandidateHeader } from "./CandidateLayout";
import PublicNav from "./PublicNav";
import { RoleHeader, tabsFor } from "./RoleLayout";
import { useAuth } from "../lib/auth";

/**
 * The header for pages shared by everyone (home, catalogue, formation sheet, comparison).
 * Signed-in users always get their own role's navbar; visitors get the public one.
 */
export default function AppHeader() {
  const { user } = useAuth();
  if (!user) return <PublicNav />;
  if (user.role === "candidate") return <CandidateHeader />;
  return <RoleHeader tabs={tabsFor(user.role)} />;
}
