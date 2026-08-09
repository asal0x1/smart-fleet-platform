import { screenshots } from '../assets';
import './Hero.css';

export default function Hero() {
  return (
    <section className="hero section">
      <div className="container hero__grid">
        <div className="hero__content fade-in">
          <h1 className="hero__title">
            SmartFleet — единая платформа для транспортных услуг
          </h1>
          <p className="hero__subtitle">
            От обычной поездки до автобусов, персональных водителей, мероприятий и
            спецтехники — всё в одной цифровой платформе.
          </p>
          <div className="hero__actions">
            <a href="#cta" className="btn btn--primary">
              Начать работу
            </a>
            <a href="#about" className="btn btn--secondary">
              Узнать больше
            </a>
          </div>
        </div>

        <div className="hero__visual fade-in">
          <div className="phone-frame">
            <img
              src={screenshots.home}
              alt="Главный экран SmartFleet с категориями услуг"
              className="phone-frame__screen"
              width={390}
              height={844}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
