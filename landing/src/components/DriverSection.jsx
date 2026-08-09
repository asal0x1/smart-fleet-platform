import { Car, FileText, User, Briefcase } from 'lucide-react';
import { screenshots } from '../assets';
import './DriverSection.css';

const features = [
  { icon: Car, text: 'Выбор марки автомобиля' },
  { icon: Briefcase, text: 'Опыт водителя: от 1 до 10+ лет' },
  { icon: FileText, text: 'Срок договора: от 1 дня до 1 года' },
  { icon: User, text: 'Контактные данные клиента' },
];

export default function DriverSection() {
  return (
    <section className="section section--alt driver-section">
      <div className="container container--narrow">
        <div className="driver-section__layout">
          <div className="driver-section__content">
            <span className="section__label">Personal Driver</span>
            <h2 className="section__title">Информация о водителях</h2>
            <ul className="feature-list">
              {features.map(({ icon: Icon, text }) => (
                <li key={text} className="feature-list__item">
                  <Icon className="feature-list__icon" size={18} strokeWidth={2} />
                  <span>{text}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="driver-section__media">
            <div className="phone-frame phone-frame--small">
              <img
                src={screenshots.driver}
                alt="Экран заказа персонального водителя"
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
