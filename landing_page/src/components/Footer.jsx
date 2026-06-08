import React from 'react';
import { MapPin, Phone, MessageSquare, Mail, Facebook, Instagram, Twitter, Stethoscope } from 'lucide-react';

const Footer = () => {
    return (
        <footer id="contacto" className="bg-slate-950 text-slate-400 pt-24 pb-12 border-t border-slate-900">
            <div className="container mx-auto px-4 md:px-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-20">
                    {/* BRAND/INFO */}
                    <div className="space-y-6">
                        <div className="flex items-center space-x-3">
                            <div className="bg-gradient-to-br from-indigo-600 to-emerald-500 p-2.5 rounded-xl shadow-lg shadow-indigo-600/10">
                                <Stethoscope className="text-white w-5 h-5" />
                            </div>
                            <span className="text-xl font-extrabold tracking-tight text-white">
                                Healthy <span className="bg-gradient-to-r from-indigo-400 to-emerald-400 text-transparent bg-clip-text font-black">Dental</span>
                            </span>
                        </div>
                        <p className="text-sm leading-relaxed text-slate-400 font-light">
                            Comprometidos con la salud bucal de nuestra comunidad en Quito. Ofrecemos excelencia médica y calidez humana con tecnología de punta.
                        </p>
                        <div className="flex space-x-3.5">
                            <a href="#" className="hover:text-white hover:bg-indigo-600 transition-all duration-300 bg-white/5 p-2.5 rounded-xl text-slate-400">
                                <Facebook className="w-5 h-5" />
                            </a>
                            <a href="#" className="hover:text-white hover:bg-indigo-600 transition-all duration-300 bg-white/5 p-2.5 rounded-xl text-slate-400">
                                <Instagram className="w-5 h-5" />
                            </a>
                            <a href="#" className="hover:text-white hover:bg-indigo-600 transition-all duration-300 bg-white/5 p-2.5 rounded-xl text-slate-400">
                                <Twitter className="w-5 h-5" />
                            </a>
                        </div>
                    </div>

                    {/* QUICK LINKS */}
                    <div>
                        <h4 className="text-white font-extrabold mb-6 text-xs sm:text-sm uppercase tracking-widest">Enlaces Rápidos</h4>
                        <ul className="space-y-3.5 text-sm font-light">
                            <li><a href="#" className="hover:text-indigo-400 transition-colors">Inicio</a></li>
                            <li><a href="#servicios" className="hover:text-indigo-400 transition-colors">Nuestros Servicios</a></li>
                            <li><a href="#contacto" className="hover:text-indigo-400 transition-colors">Contacto</a></li>
                            <li><a href="/login" className="hover:text-indigo-400 transition-colors font-semibold">Portal del Personal</a></li>
                        </ul>
                    </div>

                    {/* CONTACT INFO */}
                    <div className="lg:col-span-2">
                        <h4 className="text-white font-extrabold mb-6 text-xs sm:text-sm uppercase tracking-widest">Información de Contacto</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="flex items-start space-x-4">
                                <div className="bg-indigo-500/10 p-3 rounded-xl text-indigo-400 mt-1 flex-shrink-0">
                                    <MapPin className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Dirección</h5>
                                    <p className="text-sm text-slate-400 leading-relaxed font-light">
                                        Ave. Mariscal Sucre S10-462 e Illescas, Quito Sur, Ecuador, 170608
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start space-x-4">
                                <div className="bg-indigo-500/10 p-3 rounded-xl text-indigo-400 mt-1 flex-shrink-0">
                                    <Phone className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Teléfono</h5>
                                    <p className="text-sm text-slate-400 font-light">093 975 2666</p>
                                    <div className="flex items-center space-x-1.5 mt-1 text-emerald-400">
                                        <MessageSquare className="w-4 h-4" />
                                        <span className="text-xs font-bold">+593 93 975 2666</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-start space-x-4">
                                <div className="bg-indigo-500/10 p-3 rounded-xl text-indigo-400 mt-1 flex-shrink-0">
                                    <Mail className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Email</h5>
                                    <p className="text-sm text-slate-400 font-light">hdental3@outlook.com</p>
                                </div>
                            </div>

                            <div className="flex items-start space-x-4">
                                <div className="bg-indigo-500/10 p-3 rounded-xl text-indigo-400 mt-1 flex-shrink-0">
                                    <MessageCircle className="w-5 h-5" />
                                </div>
                                <div>
                                    <h5 className="text-white text-sm font-bold mb-1">Facebook Messenger</h5>
                                    <p className="text-sm text-slate-400 font-light">Healthy Dental II</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="pt-10 border-t border-slate-900 text-center text-[10px] text-slate-600 uppercase tracking-widest font-bold">
                    <p>© {new Date().getFullYear()} Healthy Dental - Todos los derechos reservados.</p>
                </div>
            </div>
        </footer>
    );
};

const MessageCircle = ({ className }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
    </svg>
);

export default Footer;
