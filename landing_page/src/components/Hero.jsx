import React from 'react';
import { Calendar, ChevronRight, CheckCircle } from 'lucide-react';
import heroClinic from '../assets/hero_clinic.png';

const Hero = () => {
    return (
        <section className="relative pt-32 pb-20 md:pt-44 md:pb-28 overflow-hidden bg-slate-50">
            {/* BACKGROUND DECORATIVE ELEMENTS */}
            <div className="absolute top-0 right-0 -z-10 w-2/3 h-full bg-gradient-to-br from-blue-50/70 via-sky-50/40 to-transparent rounded-l-[120px] hidden lg:block"></div>
            <div className="absolute top-1/4 left-1/4 -z-10 w-72 h-72 bg-sky-200/20 blur-[120px] rounded-full animate-pulse"></div>
            <div className="absolute -bottom-10 right-10 -z-10 w-96 h-96 bg-teal-50/50 blur-[150px] rounded-full"></div>

            <div className="container mx-auto px-4 md:px-6">
                <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-16">
                    {/* TEXT CONTENT */}
                    <div className="flex-1 text-center lg:text-left space-y-8 max-w-2xl">
                        <div className="inline-flex items-center space-x-2 bg-white border border-blue-100 shadow-sm text-slate-800 px-4 py-1.5 rounded-full text-xs sm:text-sm font-semibold">
                            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
                            <span className="flex h-2 w-2 rounded-full bg-emerald-500 absolute"></span>
                            <span className="pl-3 text-slate-600 font-medium">Tecnología Dental de Vanguardia en Quito</span>
                        </div>

                        <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-slate-900 leading-[1.15] tracking-tight">
                            Tu Sonrisa en Manos de <span className="bg-gradient-to-r from-blue-600 to-sky-500 text-transparent bg-clip-text">Expertos</span>
                        </h1>

                        <p className="text-base sm:text-lg md:text-xl text-slate-600 leading-relaxed font-light">
                            En <strong className="font-semibold text-slate-800">Healthy Dental</strong> combinamos el más alto nivel clínico con tecnología de punta y un trato humano excepcional para cuidar la salud bucal de toda tu familia.
                        </p>

                        {/* TRUST ITEMS */}
                        <div className="grid grid-cols-2 gap-4 py-2 text-left max-w-md mx-auto lg:mx-0">
                            <div className="flex items-center space-x-2 text-sm text-slate-700 font-medium">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Odontólogos Especializados</span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-slate-700 font-medium">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Equipos de Última Generación</span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-slate-700 font-medium">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Atención 100% Personalizada</span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-slate-700 font-medium">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Ambientes Seguros y Cómodos</span>
                            </div>
                        </div>

                        <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
                            <a 
                                href="https://wa.me/593939752666" 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="w-full sm:w-auto flex items-center justify-center space-x-3 bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-2xl font-bold text-base transition duration-300 transform active:scale-95 shadow-lg shadow-blue-500/20"
                            >
                                <Calendar className="w-5 h-5" />
                                <span>Agendar Cita Ahora</span>
                            </a>

                            <a 
                                href="#servicios" 
                                className="w-full sm:w-auto flex items-center justify-center space-x-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 px-8 py-4 rounded-2xl font-bold text-base transition duration-300 transform active:scale-95 shadow-sm"
                            >
                                <span>Nuestros Servicios</span>
                                <ChevronRight className="w-5 h-5 text-slate-400" />
                            </a>
                        </div>

                        {/* STATS/PROOFS */}
                        <div className="flex items-center justify-center lg:justify-start space-x-8 pt-8 border-t border-slate-200/60">
                            <div>
                                <p className="text-3xl font-black text-slate-900">10k+</p>
                                <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mt-0.5">Pacientes Felices</p>
                            </div>
                            <div className="w-px h-8 bg-slate-200"></div>
                            <div>
                                <p className="text-3xl font-black text-slate-900">15+</p>
                                <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mt-0.5">Especialistas</p>
                            </div>
                            <div className="w-px h-8 bg-slate-200"></div>
                            <div>
                                <p className="text-3xl font-black text-slate-900">4.9/5</p>
                                <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mt-0.5">Calificación Google</p>
                            </div>
                        </div>
                    </div>

                    {/* IMAGE CONTENT */}
                    <div className="flex-1 relative w-full max-w-xl lg:max-w-none">
                        <div className="relative z-10 rounded-[48px] overflow-hidden border-8 border-white shadow-2xl shadow-slate-900/10">
                            <img
                                src={heroClinic}
                                alt="Clínica Dental Moderna Healthy Dental"
                                className="w-full h-auto object-cover aspect-[4/3] sm:aspect-[16/10] lg:aspect-[4/3]"
                            />
                        </div>
                        {/* DECORATIVE FLOATING SHAPES */}
                        <div className="absolute -top-6 -right-6 w-36 h-36 bg-blue-100 rounded-full blur-2xl opacity-80 animate-pulse"></div>
                        <div className="absolute -bottom-8 -left-8 w-44 h-44 bg-teal-100 rounded-full blur-2xl opacity-75"></div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Hero;

