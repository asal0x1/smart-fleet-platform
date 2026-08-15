import { Car, Calendar, Clock, MapPin, Sparkles } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Car, text: 'Choose the car brand and how many you need' },
  { icon: Sparkles, text: 'Decoration type: flowers, balloons, ribbons' },
  { icon: MapPin, text: 'Event address' },
  { icon: Calendar, text: 'Date and time of the event' },
  { icon: Clock, text: 'Rental duration in hours' },
];

export default function EventsSection() {
  return (
    <section className="section">
      <div className="container">
        <div className="split-section split-section--reverse">
          <div className="split-section__content">
            <span className="section__label">Wedding & Events</span>
            <h2 className="section__title">Transport for special occasions</h2>
            <p className="section__desc">
              Arrange transport for weddings, celebrations and other events from a
              single interface.
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
                alt="Event transport booking screen"
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
