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
    text: 'Быстрые поездки и доставка с выбором тарифа и оплаты.',
  },
  {
    icon: UserCircle,
    title: 'Personal Driver',
    text: 'Персональный водитель на нужный срок с выбором опыта.',
  },
  {
    icon: Heart,
    title: 'Wedding & Events',
    text: 'Транспорт для свадеб и торжеств с оформлением.',
  },
  {
    icon: Bus,
    title: 'Bus Booking',
    text: 'Автобусы для групповых поездок и мероприятий.',
  },
  {
    icon: Construction,
    title: 'Heavy Equipment',
    text: 'Спецтехника для строительства и дорожных работ.',
  },
  {
    icon: Gift,
    title: 'Gift & Memorial',
    text: 'Транспорт для памятных и торжественных событий.',
  },
];

export default function AdditionalFeatures() {
  return (
    <section className="section">
      <div className="container">
        <div className="section__header" style={{ marginBottom: '2.5rem' }}>
          <h2 className="section__title">Дополнительные возможности</h2>
          <p className="section__desc">
            Каждое направление доступно через единый интерфейс SmartFleet.
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
