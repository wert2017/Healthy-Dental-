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
        <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'bg-white/90 backdrop-blur-md shadow-md shadow-slate-100/40 border-b border-slate-100/80 py-3' : 'bg-transparent py-6'}`}>
            <div className="container mx-auto px-4 md:px-6 flex items-center justify-between">
                {/* LOGO */}
                <div className="flex items-center space-x-3 group cursor-pointer">
                    <div className="bg-gradient-to-br from-indigo-600 to-emerald-500 p-2.5 rounded-xl shadow-lg shadow-indigo-500/15 group-hover:scale-105 transition-transform duration-300">
                        <Stethoscope className="text-white w-5.5 h-5.5" />
                    </div>
                    <span className="text-xl font-extrabold tracking-tight text-slate-800">
                        Healthy <span className="bg-gradient-to-r from-indigo-600 to-emerald-500 text-transparent bg-clip-text">Dental</span>
                    </span>
                </div>

                {/* DESKTOP NAV */}
                <nav className="hidden md:flex items-center space-x-8">
                    <a href="#" className="text-sm font-bold text-slate-600 hover:text-indigo-600 transition-colors relative py-1 after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 hover:after:w-full after:bg-indigo-600 after:transition-all after:duration-300">Inicio</a>
                    <a href="#servicios" className="text-sm font-bold text-slate-600 hover:text-indigo-600 transition-colors relative py-1 after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 hover:after:w-full after:bg-indigo-600 after:transition-all after:duration-300">Servicios</a>
                    <a href="#contacto" className="text-sm font-bold text-slate-600 hover:text-indigo-600 transition-colors relative py-1 after:absolute after:bottom-0 after:left-0 after:h-[2px] after:w-0 hover:after:w-full after:bg-indigo-600 after:transition-all after:duration-300">Contacto</a>
                </nav>

                {/* PORTAL BUTTON */}
                <div className="hidden md:block">
                    <a
                        href="/login"
                        className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white px-5.5 py-2.5 rounded-2xl text-sm font-bold transition duration-300 shadow-lg shadow-indigo-600/15 hover:shadow-indigo-600/25 active:scale-95"
                    >
                        <LogIn className="w-4 h-4" />
                        <span>Portal del Personal</span>
                    </a>
                </div>

                {/* MOBILE MENU BUTTON */}
                <button className="md:hidden text-slate-700 hover:text-indigo-600 transition-colors" onClick={() => setIsMenuOpen(!isMenuOpen)}>
                    {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
            </div>

            {/* MOBILE NAV OVERLAY */}
            {isMenuOpen && (
                <div className="md:hidden absolute top-full left-0 right-0 bg-white/95 backdrop-blur-md border-b border-slate-100 shadow-xl overflow-hidden animate-in slide-in-from-top duration-300">
                    <nav className="flex flex-col p-6 space-y-4">
                        <a href="#" onClick={() => setIsMenuOpen(false)} className="text-base font-bold text-slate-800 hover:text-indigo-600 transition-colors">Inicio</a>
                        <a href="#servicios" onClick={() => setIsMenuOpen(false)} className="text-base font-bold text-slate-800 hover:text-indigo-600 transition-colors">Servicios</a>
                        <a href="#contacto" onClick={() => setIsMenuOpen(false)} className="text-base font-bold text-slate-800 hover:text-indigo-600 transition-colors">Contacto</a>
                        <div className="pt-2">
                            <a
                                href="/login"
                                onClick={() => setIsMenuOpen(false)}
                                className="flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white p-3.5 rounded-2xl font-bold transition-all shadow-md"
                            >
                                <LogIn className="w-4 h-4" />
                                <span>Portal del Personal</span>
                            </a>
                        </div>
                    </nav>
                </div>
            )}
        </header>
    );
};

export default Header;
