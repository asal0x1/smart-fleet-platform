import { Calendar, Construction, MapPin, Plus } from 'lucide-react';
import { screenshots } from '../assets';

const features = [
  { icon: Construction, text: 'Categories: earthworks, hauling, road works' },
  { icon: Plus, text: 'Equipment: excavator, bulldozer, grader' },
  { icon: MapPin, text: 'Site address' },
  { icon: Calendar, text: 'Start date and time of the work' },
];

export default function HeavyEquipmentSection() {
  return (
    <section className="section">
      <div className="container">
        <div className="split-section split-section--reverse">
          <div className="split-section__content">
            <span className="section__label">Heavy Equipment</span>
            <h2 className="section__title">Not just cars</h2>
            <p className="section__desc" style={{ marginBottom: '0.5rem' }}>
              <strong>Heavy equipment on the same platform</strong>
            </p>
            <p className="section__desc">
              SmartFleet works not only with passenger vehicles, but with a wide range
              of specialised equipment as well.
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
                alt="SmartFleet heavy equipment booking screen"
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
