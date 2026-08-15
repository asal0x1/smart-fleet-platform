import { Car, FileText, User, Briefcase } from 'lucide-react';
import { screenshots } from '../assets';
import './DriverSection.css';

const features = [
  { icon: Car, text: 'Choose the car brand' },
  { icon: Briefcase, text: 'Driver experience: from 1 to 10+ years' },
  { icon: FileText, text: 'Contract length: from one day to one year' },
  { icon: User, text: 'Client contact details' },
];

export default function DriverSection() {
  return (
    <section className="section section--alt driver-section">
      <div className="container container--narrow">
        <div className="driver-section__layout">
          <div className="driver-section__content">
            <span className="section__label">Personal Driver</span>
            <h2 className="section__title">Driver information</h2>
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
                alt="Personal driver booking screen"
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
