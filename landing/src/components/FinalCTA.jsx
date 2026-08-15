import { Download, Smartphone } from 'lucide-react';
import { screenshots } from '../assets';
import { APK } from '../config';
import './FinalCTA.css';

export default function FinalCTA() {
  return (
    <section id="cta" className="section final-cta">
      <div className="container">
        <div className="final-cta__inner">
          <div className="final-cta__content">
            <h2 className="final-cta__title">
              Manage transport smarter with SmartFleet
            </h2>
            <p className="final-cta__desc">
              Every transport service you need — in one modern digital platform.
            </p>

            <a
              href={APK.url}
              download
              className="btn final-cta__btn--download"
            >
              <Download size={18} />
              Download the app
            </a>

            <p className="final-cta__meta">
              <Smartphone size={15} aria-hidden="true" />
              Android · APK {APK.size} · version {APK.version}
            </p>
          </div>

          <div className="final-cta__visual">
            <div className="phone-frame phone-frame--small">
              <img
                src={screenshots.home}
                alt="SmartFleet app interface"
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
