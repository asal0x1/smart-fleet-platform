import { Car, LayoutGrid, ClipboardList, Zap } from 'lucide-react';

const cards = [
  {
    icon: Car,
    title: 'Разные виды транспорта',
    text: 'Такси, автобусы, персональные водители и специализированная техника.',
  },
  {
    icon: LayoutGrid,
    title: 'Единый интерфейс',
    text: 'Основные услуги доступны через одну платформу.',
  },
  {
    icon: ClipboardList,
    title: 'Контроль заказов',
    text: 'История и статусы заказов в одном месте.',
  },
  {
    icon: Zap,
    title: 'Быстрое оформление',
    text: 'Выбор услуги, параметров и оформление заказа в несколько шагов.',
  },
];

export default function About() {
  return (
    <section id="about" className="section section--alt">
      <div className="container">
        <div className="section__header">
          <h2 className="section__title">Все транспортные услуги в одном месте</h2>
          <p className="section__desc">
            SmartFleet объединяет различные транспортные и сервисные направления в
            единой цифровой платформе.
          </p>
        </div>

        <div className="cards-grid cards-grid--4" style={{ marginTop: '2.5rem' }}>
          {cards.map(({ icon: Icon, title, text }) => (
            <article key={title} className="card">
              <div className="card__icon">
                <Icon size={20} strokeWidth={2} />
              </div>
              <h3 className="card__title">{title}</h3>
              <p className="card__text">{text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
