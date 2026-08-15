import {
  Car,
  UserCircle,
  Heart,
  Bus,
  Construction,
  Gift,
} from 'lucide-react';

const services = [
  {
    icon: Car,
    title: 'Taxi & Delivery',
    text: 'Fast rides and deliveries with your choice of tariff and payment.',
  },
  {
    icon: UserCircle,
    title: 'Personal Driver',
    text: 'A personal driver for as long as you need, with the experience you choose.',
  },
  {
    icon: Heart,
    title: 'Wedding & Events',
    text: 'Decorated transport for weddings and celebrations.',
  },
  {
    icon: Bus,
    title: 'Bus Booking',
    text: 'Buses for group trips and events.',
  },
  {
    icon: Construction,
    title: 'Heavy Equipment',
    text: 'Specialised machinery for construction and road works.',
  },
  {
    icon: Gift,
    title: 'Gift & Memorial',
    text: 'Transport for memorial and ceremonial occasions.',
  },
];

export default function AdditionalFeatures() {
  return (
    <section className="section">
      <div className="container">
        <div className="section__header" style={{ marginBottom: '2.5rem' }}>
          <h2 className="section__title">More services</h2>
          <p className="section__desc">
            Every category is available through the same SmartFleet interface.
          </p>
        </div>

        <div className="cards-grid cards-grid--2 cards-grid--3">
          {services.map(({ icon: Icon, title, text }) => (
            <article key={title} className="card">
              <div className="card__icon">
                <Icon size={20} strokeWidth={2} />
              </div>
              <h3 className="card__title">{title}</h3>
              <p className="card__text">{text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
