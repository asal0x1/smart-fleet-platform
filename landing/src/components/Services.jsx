import { screenshots } from '../assets';
import './Services.css';

const categories = [
  { name: 'Taxi & Delivery', color: '#1e3a5f' },
  { name: 'Wedding & Events', color: '#6b2d3e' },
  { name: 'Personal Driver', color: '#3d3a6b' },
  { name: 'Bus Booking', color: '#1e4d5c' },
  { name: 'Gift & Memorial', color: '#7a3344' },
  { name: 'Heavy Equipment', color: '#5c4a32' },
];

export default function Services() {
  return (
    <section id="features" className="section">
      <div className="container">
        <div className="services__header">
          <h2 className="section__title">Одна платформа — множество возможностей</h2>
          <p className="section__desc">
            Выберите нужную категорию и оформите заказ в несколько шагов — без
            переключения между разными сервисами.
          </p>
        </div>

        <div className="services__layout">
          <div className="services__categories">
            {categories.map(({ name, color }) => (
              <div key={name} className="services__category" style={{ '--cat-color': color }}>
                <span className="services__category-dot" />
                <span>{name}</span>
              </div>
            ))}
          </div>

          <div className="services__preview">
            <div className="phone-frame">
              <img
                src={screenshots.home}
                alt="Категории услуг SmartFleet"
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
