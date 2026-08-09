import './Ecosystem.css';

const steps = [
  { id: 'client', label: 'Client', desc: 'Клиент оформляет заказ через приложение' },
  { id: 'platform', label: 'SmartFleet', desc: 'Платформа обрабатывает и распределяет запрос' },
  { id: 'driver', label: 'Driver', desc: 'Водитель получает заказ и выполняет поездку' },
  { id: 'vehicle', label: 'Vehicle', desc: 'Транспортное средство выполняет задачу' },
];

export default function Ecosystem() {
  return (
    <section id="ecosystem" className="section">
      <div className="container container--narrow">
        <div className="ecosystem__header">
          <h2 className="section__title">Единая экосистема</h2>
          <p className="section__desc">
            SmartFleet объединяет клиента, водителя и транспортную инфраструктуру в
            единой системе.
          </p>
        </div>

        <div className="ecosystem__flow" aria-label="Схема экосистемы SmartFleet">
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
