import './Footer.css';

const links = [
  { label: 'About', href: '#about' },
  { label: 'Features', href: '#features' },
  { label: 'Services', href: '#services' },
  { label: 'How it works', href: '#ecosystem' },
];

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div className="footer__brand">
          <span className="footer__logo">SmartFleet</span>
          <p className="footer__tagline">
            One digital platform for every transport service
          </p>
        </div>

        <nav className="footer__nav" aria-label="Footer navigation">
          {links.map((link) => (
            <a key={link.href} href={link.href} className="footer__link">
              {link.label}
            </a>
          ))}
        </nav>

        <p className="footer__copy">
          &copy; {new Date().getFullYear()} SmartFleet. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
