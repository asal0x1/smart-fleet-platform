import './Ecosystem.css';

const steps = [
  { id: 'client', label: 'Client', desc: 'The client places an order in the app' },
  { id: 'platform', label: 'SmartFleet', desc: 'The platform processes and routes the request' },
  { id: 'driver', label: 'Driver', desc: 'The driver accepts the order and completes the trip' },
  { id: 'vehicle', label: 'Vehicle', desc: 'The vehicle carries out the job' },
];

export default function Ecosystem() {
  return (
    <section id="ecosystem" className="section">
      <div className="container container--narrow">
        <div className="ecosystem__header">
          <h2 className="section__title">A single ecosystem</h2>
          <p className="section__desc">
            SmartFleet connects the client, the driver and the transport
            infrastructure in one system.
          </p>
        </div>

        <div className="ecosystem__flow" aria-label="SmartFleet ecosystem diagram">
          {steps.map((step, index) => (
            <div key={step.id} className="ecosystem__step">
              <div className="ecosystem__node">
                <span className="ecosystem__node-label">{step.label}</span>
              </div>
              <p className="ecosystem__step-desc">{step.desc}</p>
              {index < steps.length - 1 && (
                <div className="ecosystem__connector" aria-hidden="true">
                  <span className="ecosystem__line" />
                  <span className="ecosystem__arrow">↓</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
