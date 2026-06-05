import React from 'react';
import { MapPin, Phone, MessageSquare, Mail, Facebook, Instagram, Twitter, Stethoscope } from 'lucide-react';

const Footer = () => {
    return (
        <footer id="contacto" className="bg-slate-900 text-slate-300 pt-20 pb-10 border-t border-slate-800">
            <div className="container mx-auto px-4 md:px-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
                    {/* BRAND/INFO */}
                    <div className="space-y-6">
                        <div className="flex items-center space-x-2">
                            <div className="bg-gradient-to-br from-blue-600 to-sky-500 p-2.5 rounded-xl">
                                <Stethoscope className="text-white w-5 h-5" />
                            </div>
                            <span className="text-xl font-bold tracking-tight text-white">
                                Healthy <span className="bg-gradient-to-r from-blue-400 to-sky-400 text-transparent bg-clip-text font-black">Dental</span>
                            </span>
                        </div>
                        <p className="text-sm leading-relaxed text-slate-400">
                            Comprometidos con la salud bucal de nuestra comunidad en Quito. Ofrecemos excelencia médica y calidez humana.
                        </p>
                        <div className="flex space-x-4">
                            <a href="#" className="hover:text-blue-500 transition-colors bg-white/5 p-2.5 rounded-xl">
                                <Facebook className="w-5 h-5" />
                            </a>
                            <a href="#" className="hover:text-blue-500 transition-colors bg-white/5 p-2.5 rounded-xl">
                                <Instagram className="w-5 h-5" />
                            </a>
                            <a href="#" className="hover:text-blue-500 transition-colors bg-white/5 p-2.5 rounded-xl">
                                <Twitter className="w-5 h-5" />
                            </a>
                        </div>
                    </div>

                    {/* QUICK LINKS */}
                    <div>
                        <h4 className="text-white font-bold mb-6 text-sm uppercase tracking-wider">Enlaces Rápidos</h4>
                        <ul className="space-y-3.5 text-sm">
                            <li><a href="#" className="hover:text-sky-400 transition-colors">Inicio</a></li>
                            <li><a href="#servicios" className="hover:text-sky-400 transition-colors">Nuestros Servicios</a></li>
                            <li><a href="#contacto" className="hover:text-sky-400 transition-colors">Contacto</a></li>
                            <li><a href="/login" className="hover:text-sky-400 transition-colors">Portal del Personal</a></li>
                        </ul>
                    </div>

                    {/* CONTACT INFO (REQUESTED) */}
                    <div className="lg:col-span-2">
                        <h4 className="text-white font-bold mb-6 text-sm uppercase tracking-wider">Información de Contacto</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="flex items-start space-x-4">
                                <div className="bg-blue-500/10 p-3 rounded-xl text-blue-400 mt-1">
                                    <MapPin className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Dirección</h5>
                                    <p className="text-sm text-slate-400 leading-relaxed">
                                        Ave. Mariscal Sucre S10-462 e Illescas, Quito Sur, Ecuador, 170608
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start space-x-4">
                                <div className="bg-sky-500/10 p-3 rounded-xl text-sky-400 mt-1">
                                    <Phone className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Teléfono</h5>
                                    <p className="text-sm text-slate-400">093 975 2666</p>
                                    <div className="flex items-center space-x-2 mt-1 text-sky-400">
                                        <MessageSquare className="w-4 h-4" />
                                        <span className="text-xs font-semibold">+593 93 975 2666</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-start space-x-4">
                                <div className="bg-teal-500/10 p-3 rounded-xl text-teal-400 mt-1">
                                    <Mail className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Email</h5>
                                    <p className="text-sm text-slate-400">hdental3@outlook.com</p>
                                </div>
                            </div>

                            <div className="flex items-start space-x-4">
                                <div className="bg-indigo-500/10 p-3 rounded-xl text-indigo-400 mt-1">
                                    <MessageCircle className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Facebook Messenger</h5>
                                    <p className="text-sm text-slate-400">Healthy Dental II</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="pt-10 border-t border-slate-800 text-center text-xs text-slate-500 uppercase tracking-widest">
                    <p>© {new Date().getFullYear()} Healthy Dental - Todos los derechos reservados.</p>
                </div>
            </div>
        </footer>
    );
};

// Internal MessageCircle Import override for footer style consistency if needed
const MessageCircle = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
    </svg>
);

export default Footer;

