import Navbar from './components/Navbar';
import Hero from './components/Hero';
import About from './components/About';
import Services from './components/Services';
import TaxiSection from './components/TaxiSection';
import EventsSection from './components/EventsSection';
import BusSection from './components/BusSection';
import HeavyEquipmentSection from './components/HeavyEquipmentSection';
import OrdersSection from './components/OrdersSection';
import Ecosystem from './components/Ecosystem';
import DriverSection from './components/DriverSection';
import AdditionalFeatures from './components/AdditionalFeatures';
import FinalCTA from './components/FinalCTA';
import Footer from './components/Footer';

export default function App() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <About />
        <Services />
        <TaxiSection />
        <EventsSection />
        <BusSection />
        <HeavyEquipmentSection />
        <OrdersSection />
        <Ecosystem />
        <DriverSection />
        <AdditionalFeatures />
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
