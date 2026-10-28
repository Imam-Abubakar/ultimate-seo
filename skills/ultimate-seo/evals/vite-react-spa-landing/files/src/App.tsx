import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Pricing from "./pages/Pricing";
import Features from "./pages/Features";
import About from "./pages/About";

export default function App() {
  return (
    <>
      <nav>
        <Link to="/">Tidyhive</Link> <Link to="/features">Features</Link> <Link to="/pricing">Pricing</Link> <Link to="/about">About</Link>
        <span onClick={() => (window.location.href = "https://app.tidyhive.com/signup")}>Start free trial</span>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/features" element={<Features />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </>
  );
}
