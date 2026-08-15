import { CheckCircle, Clock, XCircle, Receipt } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Clock, text: 'Pending — the order is being processed' },
  { icon: CheckCircle, text: 'Completed — the trip is finished' },
  { icon: XCircle, text: 'Cancelled — the order was cancelled' },
  { icon: Receipt, text: 'Price, tariff and route details' },
];

export default function OrdersSection() {
  return (
    <section className="section section--alt">
      <div className="container">
        <div className="split-section">
          <div className="split-section__content">
            <span className="section__label">Orders</span>
            <h2 className="section__title">Every order under control</h2>
            <p className="section__desc">
              Track your order history and current status from a single interface.
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
                src={screenshots.orders}
                alt="SmartFleet order history"
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
