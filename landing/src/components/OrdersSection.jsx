import { CheckCircle, Clock, XCircle, Receipt } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Clock, text: 'Статус Pending — заказ в обработке' },
  { icon: CheckCircle, text: 'Статус Completed — поездка завершена' },
  { icon: XCircle, text: 'Статус Cancelled — заказ отменён' },
  { icon: Receipt, text: 'Стоимость, тариф и детали маршрута' },
];

export default function OrdersSection() {
  return (
    <section className="section section--alt">
      <div className="container">
        <div className="split-section">
          <div className="split-section__content">
            <span className="section__label">Orders</span>
            <h2 className="section__title">Все заказы под контролем</h2>
            <p className="section__desc">
              Отслеживайте историю заказов и их текущий статус в одном интерфейсе.
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
                alt="История заказов SmartFleet"
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
