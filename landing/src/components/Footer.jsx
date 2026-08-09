import './Footer.css';

const links = [
  { label: 'О SmartFleet', href: '#about' },
  { label: 'Возможности', href: '#features' },
  { label: 'Услуги', href: '#services' },
  { label: 'Как работает', href: '#ecosystem' },
];

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="footer__brand">
          <span className="footer__logo">SmartFleet</span>
          <p className="footer__tagline">
            Единая цифровая платформа для транспортных услуг
          </p>
        </div>

        <nav className="footer__nav" aria-label="Навигация в подвале">
          {links.map((link) => (
            <a key={link.href} href={link.href} className="footer__link">
              {link.label}
            </a>
          ))}
        </nav>

        <p className="footer__copy">
          &copy; {new Date().getFullYear()} SmartFleet. Все права защищены.
        </p>
      </div>
    </footer>
  );
}
