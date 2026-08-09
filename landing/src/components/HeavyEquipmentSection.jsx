import { Calendar, Construction, MapPin, Plus } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Construction, text: 'Категории: земляные работы, перевозка, дорожные работы' },
  { icon: Plus, text: 'Выбор техники: экскаватор, бульдозер, грейдер' },
  { icon: MapPin, text: 'Адрес объекта' },
  { icon: Calendar, text: 'Дата и время начала работ' },
];

export default function HeavyEquipmentSection() {
  return (
    <section className="section">
      <div className="container">
        <div className="split-section split-section--reverse">
          <div className="split-section__content">
            <span className="section__label">Heavy Equipment</span>
            <h2 className="section__title">Не только автомобили</h2>
            <p className="section__desc" style={{ marginBottom: '0.5rem' }}>
              <strong>Спецтехника на одной платформе</strong>
            </p>
            <p className="section__desc">
              SmartFleet позволяет работать не только с легковым транспортом, но и с
              различными категориями специализированной техники.
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
                src={screenshots.heavyEquipment}
                alt="Экран заказа спецтехники SmartFleet"
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
