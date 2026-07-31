import TopNav from "../components/layout/TopNav";
import Footer from "../components/layout/Footer";
import HeroBand from "../components/landing/HeroBand";
import FeatureGrid from "../components/landing/FeatureGrid";
import CTABand from "../components/landing/CTABand";

export default function LandingPage() {
  return (
    <>
      <TopNav />
      <main>
        <HeroBand />
        <FeatureGrid />
        <CTABand />
      </main>
      <Footer />
    </>
  );
}
