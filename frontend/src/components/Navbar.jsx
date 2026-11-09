import { Link, useLocation } from "react-router-dom";
import SearchBox from "./SearchBox";

export default function Navbar() {
  const { pathname } = useLocation();
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
        <Link to="/" className="shrink-0 font-display text-lg font-bold text-gold">
          Telugu Cinema <span className="hidden text-white sm:inline">to the World</span>
        </Link>
        {/* The home page has its own big search box */}
        {pathname !== "/" && (
          <div className="ml-auto w-full max-w-sm"><SearchBox /></div>
        )}
      </div>
    </header>
  );
}