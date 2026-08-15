import { MapPin, CreditCard, Clock, Route } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Route, text: 'Route from point A to point B' },
  { icon: MapPin, text: 'Tariff options: Standart, Komfort, Biznes, Premium' },
  { icon: CreditCard, text: 'Payment method — cash to the driver' },
  { icon: Clock, text: 'Estimated trip time and distance' },
];

export default function TaxiSection() {
  return (
    <section id="services" className="section section--alt">
      <div className="container">
        <div className="split-section">
          <div className="split-section__content">
            <span className="section__label">Taxi & Delivery</span>
            <h2 className="section__title">A ride from point A to point B</h2>
            <p className="section__desc">
              Choose your route, tariff and payment method. SmartFleet makes booking a
              ride quick and simple.
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
                alt="SmartFleet taxi booking screen"
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
