import { screenshots } from '../assets';
import './Hero.css';

export default function Hero() {
  return (
    <section className="hero section">
      <div className="container hero__grid">
        <div className="hero__content fade-in">
          <h1 className="hero__title">
            SmartFleet — one platform for every transport service
          </h1>
          <p className="hero__subtitle">
            From an everyday ride to buses, personal drivers, events and heavy
            equipment — all in a single digital platform.
          </p>
          <div className="hero__actions">
            <a href="#cta" className="btn btn--primary">
              Download the app
            </a>
            <a href="#about" className="btn btn--secondary">
              Learn more
            </a>
          </div>
        </div>

        <div className="hero__visual fade-in">
          <div className="phone-frame">
            <img
              src={screenshots.home}
              alt="SmartFleet home screen with service categories"
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
