import { Link, NavLink, useLocation } from "react-router-dom";
import SearchBox from "./SearchBox";

const LINKS = [
  ["/analytics", "Overview"],
  ["/analytics/language-share", "Language share"],
  ["/analytics/pan-india", "Pan-India"],
  ["/analytics/budget", "Budget vs gross"],
  ["/duel", "Duel"],
];

export default function Navbar() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
        <Link to="/" className="shrink-0 font-display text-lg font-bold text-gold">
          Telugu Cinema <span className="hidden text-white sm:inline">to the World</span>
        </Link>
        {pathname !== "/" && (
          <div className="ml-auto w-full max-w-sm"><SearchBox /></div>
        )}
      </div>
      <nav aria-label="Main" className="mx-auto max-w-6xl overflow-x-auto px-4">
        <ul className="flex gap-5 whitespace-nowrap text-sm">
          {LINKS.map(([to, label]) => (
            <li key={to}>
              <NavLink
                to={to}
                end
                className={({ isActive }) =>
                  `block border-b-2 py-2 ${
                    isActive ? "border-gold text-gold" : "border-transparent text-muted hover:text-white"
                  }`
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}