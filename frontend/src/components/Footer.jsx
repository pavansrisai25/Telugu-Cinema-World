export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-line px-4 py-8 text-xs text-muted">
      <div className="mx-auto max-w-6xl space-y-2">
        <p>
          Money figures are <strong className="text-gold">Reported</strong> by public sources
          (such as Wikipedia lists and news outlets) and can differ between sources.
          Missing values are shown as "Not available".
        </p>
        <p>This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
        <p>Ratings information courtesy of IMDb (https://www.imdb.com).</p>
      </div>
    </footer>
  );
}