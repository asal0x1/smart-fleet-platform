import { Car, Calendar, Clock, MapPin, Sparkles } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Car, text: 'Выбор марки автомобиля и количества' },
  { icon: Sparkles, text: 'Тип украшения: цветы, шары, ленты' },
  { icon: MapPin, text: 'Адрес мероприятия' },
  { icon: Calendar, text: 'Дата и время проведения' },
  { icon: Clock, text: 'Продолжительность аренды в часах' },
];

export default function EventsSection() {
  return (
    <section className="section">
      <div className="container">
        <div className="split-section split-section--reverse">
          <div className="split-section__content">
            <span className="section__label">Wedding & Events</span>
            <h2 className="section__title">Транспорт для мероприятий</h2>
            <p className="section__desc">
              Организуйте транспорт для свадеб, торжеств и других мероприятий в одном
              интерфейсе.
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
                src={screenshots.wedding}
                alt="Экран заказа транспорта для мероприятий"
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
