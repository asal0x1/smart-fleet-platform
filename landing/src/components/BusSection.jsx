import { Bus, Calendar, MapPin, Users } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Bus, text: 'Bus model: Isuzu, MAN, Mercedes-Benz' },
  { icon: Users, text: 'Event type and number of buses' },
  { icon: MapPin, text: 'Pickup address' },
  { icon: Calendar, text: 'Date, time and trip duration' },
];

export default function BusSection() {
  return (
    <section className="section section--alt">
      <div className="container">
        <div className="split-section">
          <div className="split-section__content">
            <span className="section__label">Bus Booking</span>
            <h2 className="section__title">Group travel without the hassle</h2>
            <p className="section__desc">
              Arrange transport for group trips, excursions, corporate events and more.
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
                alt="SmartFleet bus booking screen"
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
