import React, { useState, useEffect } from 'react';
import { Menu, X, LogIn, Stethoscope } from 'lucide-react';

const Header = () => {
    const [isScrolled, setIsScrolled] = useState(false);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'bg-white/90 glass shadow-sm py-2' : 'bg-transparent py-4'}`}>
            <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
                {/* LOGO */}
                <div className="flex items-center space-x-2">
                    <div className="bg-dentist-blue p-2 rounded-lg">
                        <Stethoscope className="text-white w-6 h-6" />
                    </div>
                    <span className={`text-xl font-bold tracking-tight ${isScrolled ? 'text-dentist-dark' : 'text-dentist-dark'}`}>
                        Healthy <span className="text-dentist-blue">Dental</span>
                    </span>
                </div>

                {/* DESKTOP NAV */}
                <nav className="hidden md:flex items-center space-x-8">
                    <a href="#" className="text-gray-600 hover:text-dentist-blue font-medium transition-colors">Inicio</a>
                    <a href="#servicios" className="text-gray-600 hover:text-dentist-blue font-medium transition-colors">Servicios</a>
                    <a href="#contacto" className="text-gray-600 hover:text-dentist-blue font-medium transition-colors">Contacto</a>
                </nav>

                {/* PORTAL BUTTON */}
                <div className="hidden md:block">
                    <a
                        href="/login"
                        className="flex items-center space-x-2 bg-dentist-blue hover:bg-dentist-dark text-white px-5 py-2.5 rounded-full font-semibold transition-all shadow-lg shadow-dentist-blue/20 hover:scale-105"
                    >
                        <LogIn className="w-4 h-4" />
                        <span>Portal del Personal</span>
                    </a>
                </div>

                {/* MOBILE MENU BUTTON */}
                <button className="md:hidden text-gray-700" onClick={() => setIsMenuOpen(!isMenuOpen)}>
                    {isMenuOpen ? <X className="w-7 h-7" /> : <Menu className="w-7 h-7" />}
                </button>
            </div>

            {/* MOBILE NAV CIRCLE OVERLAY (SIMPLE) */}
            {isMenuOpen && (
                <div className="md:hidden absolute top-full left-0 right-0 bg-white border-b border-gray-100 shadow-xl overflow-hidden animate-in slide-in-from-top duration-300">
                    <nav className="flex flex-col p-6 space-y-4">
                        <a href="#" onClick={() => setIsMenuOpen(false)} className="text-lg font-medium text-gray-800">Inicio</a>
                        <a href="#servicios" onClick={() => setIsMenuOpen(false)} className="text-lg font-medium text-gray-800">Servicios</a>
                        <a href="#contacto" onClick={() => setIsMenuOpen(false)} className="text-lg font-medium text-gray-800">Contacto</a>
                        <a
                            href="/login"
                            onClick={() => setIsMenuOpen(false)}
                            className="flex items-center justify-center space-x-2 bg-dentist-blue text-white p-3 rounded-xl font-bold"
                        >
                            <LogIn className="w-5 h-5" />
                            <span>Portal del Personal</span>
                        </a>
                    </nav>
                </div>
            )}
        </header>
    );
};

export default Header;
