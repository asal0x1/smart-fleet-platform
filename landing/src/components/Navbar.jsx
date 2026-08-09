import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import './Navbar.css';

const navLinks = [
  { label: 'О SmartFleet', href: '#about' },
  { label: 'Возможности', href: '#features' },
  { label: 'Услуги', href: '#services' },
  { label: 'Как работает', href: '#ecosystem' },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [menuOpen]);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className={`navbar ${scrolled ? 'navbar--scrolled' : ''}`}>
      <div className="container navbar__inner">
        <a href="#" className="navbar__logo" onClick={closeMenu}>
          SmartFleet
        </a>

        <nav className="navbar__nav" aria-label="Основная навигация">
          {navLinks.map((link) => (
            <a key={link.href} href={link.href} className="navbar__link">
              {link.label}
            </a>
          ))}
        </nav>

        <div className="navbar__actions">
          <a href="#cta" className="btn btn--ghost navbar__login">
            Войти
          </a>
          <a href="#cta" className="btn btn--primary navbar__cta">
            Начать работу
          </a>
        </div>

        <button
          type="button"
          className="navbar__burger"
          aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      <div className={`navbar__mobile ${menuOpen ? 'navbar__mobile--open' : ''}`}>
        <nav className="navbar__mobile-nav">
          {navLinks.map((link) => (
            <a key={link.href} href={link.href} className="navbar__mobile-link" onClick={closeMenu}>
              {link.label}
            </a>
          ))}
          <div className="navbar__mobile-actions">
            <a href="#cta" className="btn btn--secondary" onClick={closeMenu}>
              Войти
            </a>
            <a href="#cta" className="btn btn--primary" onClick={closeMenu}>
              Начать работу
            </a>
          </div>
        </nav>
      </div>
    </header>
  );
}
