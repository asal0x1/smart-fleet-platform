import { ArrowRight } from 'lucide-react';
import { screenshots } from '../assets';
import './FinalCTA.css';

export default function FinalCTA() {
  return (
    <section id="cta" className="section final-cta">
      <div className="container">
        <div className="final-cta__inner">
          <div className="final-cta__content">
            <h2 className="final-cta__title">
              Управляйте транспортом умнее с SmartFleet
            </h2>
            <p className="final-cta__desc">
              Все необходимые транспортные услуги — в одной современной цифровой
              платформе.
            </p>
            <a href="#" className="btn btn--primary final-cta__btn">
              Начать работу
              <ArrowRight size={18} />
            </a>
          </div>

          <div className="final-cta__visual">
            <div className="phone-frame phone-frame--small">
              <img
                src={screenshots.home}
                alt="Интерфейс SmartFleet"
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
