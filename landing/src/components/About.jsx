import { Car, LayoutGrid, ClipboardList, Zap } from 'lucide-react';

const cards = [
  {
    icon: Car,
    title: 'Every kind of transport',
    text: 'Taxis, buses, personal drivers and specialised equipment.',
  },
  {
    icon: LayoutGrid,
    title: 'One interface',
    text: 'All core services available through a single platform.',
  },
  {
    icon: ClipboardList,
    title: 'Orders under control',
    text: 'Order history and statuses in one place.',
  },
  {
    icon: Zap,
    title: 'Fast booking',
    text: 'Pick a service, set the details and book in a few steps.',
  },
];

export default function About() {
  return (
    <section id="about" className="section section--alt">
      <div className="container">
        <div className="section__header">
          <h2 className="section__title">All transport services in one place</h2>
          <p className="section__desc">
            SmartFleet brings different transport and service categories together in
            a single digital platform.
          </p>
        </div>

        <div className="cards-grid cards-grid--4" style={{ marginTop: '2.5rem' }}>
          {cards.map(({ icon: Icon, title, text }) => (
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
