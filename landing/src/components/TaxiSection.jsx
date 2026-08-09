import { MapPin, CreditCard, Clock, Route } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Route, text: 'Маршрут от точки А до точки Б' },
  { icon: MapPin, text: 'Выбор тарифа: Standart, Komfort, Biznes, Premium' },
  { icon: CreditCard, text: 'Способ оплаты — наличные водителю' },
  { icon: Clock, text: 'Расчёт времени и расстояния поездки' },
];

export default function TaxiSection() {
  return (
    <section id="services" className="section section--alt">
      <div className="container">
        <div className="split-section">
          <div className="split-section__content">
            <span className="section__label">Taxi & Delivery</span>
            <h2 className="section__title">Поездка от точки А до точки Б</h2>
            <p className="section__desc">
              Выберите маршрут, тариф и способ оплаты. SmartFleet помогает оформить
              поездку быстро и удобно.
            </p>
            <ul className="feature-list">
              {features.map(({ icon: Icon, text }) => (
                <li key={text} className="feature-list__item">
                  <Icon className="feature-list__icon" size={18} strokeWidth={2} />
                  <span>{text}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="split-section__media">
            <div className="phone-frame">
              <img
                src={screenshots.taxi}
                alt="Экран заказа такси SmartFleet"
                className="phone-frame__screen"
                width={390}
                height={844}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
