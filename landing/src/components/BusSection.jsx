import { Bus, Calendar, MapPin, Users } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Bus, text: 'Выбор модели автобуса: Isuzu, MAN, Mercedes-Benz' },
  { icon: Users, text: 'Тип мероприятия и количество автобусов' },
  { icon: MapPin, text: 'Адрес подачи транспорта' },
  { icon: Calendar, text: 'Дата, время и продолжительность поездки' },
];

export default function BusSection() {
  return (
    <section className="section section--alt">
      <div className="container">
        <div className="split-section">
          <div className="split-section__content">
            <span className="section__label">Bus Booking</span>
            <h2 className="section__title">Групповые поездки без лишних хлопот</h2>
            <p className="section__desc">
              Организуйте транспорт для групповых поездок, экскурсий, корпоративных
              мероприятий и других задач.
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
                src={screenshots.bus}
                alt="Экран бронирования автобуса SmartFleet"
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
