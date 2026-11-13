import { Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Film from "./pages/Film";
import Overview from "./pages/Overview";
import LanguageShare from "./pages/LanguageShare";
import PanIndia from "./pages/PanIndia";
import BudgetVsCollection from "./pages/BudgetVsCollection";
import Hero from "./pages/Hero";
import Duel from "./pages/Duel";
import { NotFound } from "./pages/Simple";

export default function App() {
  const location = useLocation();

  return (
    <>
      <a href="#main"
         className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-gold focus:px-3 focus:py-2 focus:text-black">
        Skip to content
      </a>
      <Navbar />
      <AnimatePresence mode="wait">
        <motion.main
          id="main"
          key={location.pathname}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
        >
          <Routes location={location}>
            <Route path="/" element={<Home />} />
            <Route path="/film/:id" element={<Film />} />
            <Route path="/person/:id" element={<Hero />} />
            <Route path="/duel" element={<Duel />} />
            <Route path="/analytics" element={<Overview />} />
            <Route path="/analytics/language-share" element={<LanguageShare />} />
            <Route path="/analytics/pan-india" element={<PanIndia />} />
            <Route path="/analytics/budget" element={<BudgetVsCollection />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </motion.main>
      </AnimatePresence>
      <Footer />
    </>
  );
}