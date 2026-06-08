import React from 'react';
import { Calendar, ChevronRight, CheckCircle, Award, Sparkles } from 'lucide-react';
import heroClinic from '../assets/hero_clinic.png';

const Hero = () => {
    return (
        <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden bg-transparent">
            {/* GLOWING AURORA BACKGROUND */}
            <div className="absolute top-0 right-0 -z-10 w-2/3 h-full bg-gradient-to-br from-indigo-50/50 via-purple-50/20 to-transparent rounded-l-[150px] hidden lg:block"></div>
            <div className="absolute top-12 left-1/4 -z-10 w-80 h-80 bg-indigo-100/30 blur-[130px] rounded-full animate-pulse"></div>
            <div className="absolute top-1/2 right-1/4 -z-10 w-96 h-96 bg-emerald-50/40 blur-[140px] rounded-full"></div>
            <div className="absolute -bottom-16 left-10 -z-10 w-96 h-96 bg-indigo-50/30 blur-[150px] rounded-full"></div>

            <div className="container mx-auto px-4 md:px-6">
                <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-20">
                    {/* TEXT CONTENT */}
                    <div className="flex-1 text-center lg:text-left space-y-8 max-w-2xl">
                        <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-indigo-50 to-emerald-50 border border-indigo-100/50 shadow-sm px-4.5 py-2 rounded-full">
                            <span className="flex h-2.5 w-2.5 rounded-full bg-indigo-600 animate-ping"></span>
                            <span className="flex h-2.5 w-2.5 rounded-full bg-indigo-600 absolute"></span>
                            <span className="pl-4.5 text-slate-700 text-xs sm:text-sm font-bold tracking-tight flex items-center gap-1.5">
                                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                                Tecnología Dental de Vanguardia en Quito
                            </span>
                        </div>

                        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 leading-[1.12] tracking-tight">
                            Tu Sonrisa en Manos de <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-emerald-500 text-transparent bg-clip-text">Expertos</span>
                        </h1>

                        <p className="text-base sm:text-lg md:text-xl text-slate-600 leading-relaxed font-light">
                            En <strong className="font-semibold text-slate-800">Healthy Dental</strong> combinamos el más alto nivel clínico con tecnología de punta y un trato humano excepcional para cuidar la salud bucal de toda tu familia.
                        </p>

                        {/* TRUST ITEMS */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-3 text-left max-w-md mx-auto lg:mx-0">
                            <div className="flex items-center space-x-2.5 text-sm text-slate-700 font-semibold">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Odontólogos Especializados</span>
                            </div>
                            <div className="flex items-center space-x-2.5 text-sm text-slate-700 font-semibold">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Equipos de Última Generación</span>
                            </div>
                            <div className="flex items-center space-x-2.5 text-sm text-slate-700 font-semibold">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Atención 100% Personalizada</span>
                            </div>
                            <div className="flex items-center space-x-2.5 text-sm text-slate-700 font-semibold">
                                <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                <span>Ambientes Seguros y Cómodos</span>
                            </div>
                        </div>

                        {/* ACTION BUTTONS */}
                        <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
                            <a 
                                href="https://wa.me/593939752666" 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="w-full sm:w-auto flex items-center justify-center space-x-3 bg-gradient-to-r from-indigo-600 to-emerald-500 hover:from-indigo-700 hover:to-emerald-600 text-white px-8 py-4 rounded-2xl font-extrabold text-base transition-all duration-300 transform active:scale-95 shadow-lg shadow-indigo-600/20"
                            >
                                <Calendar className="w-5 h-5" />
                                <span>Agendar Cita Ahora</span>
                            </a>

                            <a 
                                href="#servicios" 
                                className="w-full sm:w-auto flex items-center justify-center space-x-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200/80 px-8 py-4 rounded-2xl font-extrabold text-base transition duration-300 transform active:scale-95 shadow-sm"
                            >
                                <span>Nuestros Servicios</span>
                                <ChevronRight className="w-5 h-5 text-slate-400" />
                            </a>
                        </div>

                        {/* STATS/PROOFS */}
                        <div className="flex items-center justify-center lg:justify-start space-x-8 pt-8 border-t border-slate-100">
                            <div>
                                <p className="text-3xl font-extrabold text-slate-900 bg-gradient-to-r from-indigo-600 to-indigo-800 text-transparent bg-clip-text">10k+</p>
                                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Pacientes Felices</p>
                            </div>
                            <div className="w-px h-8 bg-slate-200/60"></div>
                            <div>
                                <p className="text-3xl font-extrabold text-slate-900 bg-gradient-to-r from-indigo-600 to-indigo-800 text-transparent bg-clip-text">15+</p>
                                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Especialistas</p>
                            </div>
                            <div className="w-px h-8 bg-slate-200/60"></div>
                            <div>
                                <p className="text-3xl font-extrabold text-slate-900 bg-gradient-to-r from-indigo-600 to-indigo-800 text-transparent bg-clip-text">4.9/5</p>
                                <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Calificación Google</p>
                            </div>
                        </div>
                    </div>

                    {/* IMAGE CONTENT WITH FLOATING INTERACTIVE CARDS */}
                    <div className="flex-1 relative w-full max-w-xl lg:max-w-none">
                        {/* DECORATIVE BACKGROUND RING */}
                        <div className="absolute -inset-4 bg-gradient-to-tr from-indigo-500/10 to-emerald-500/10 rounded-[54px] blur-xl -z-10"></div>
                        
                        <div className="relative z-10 rounded-[48px] overflow-hidden border-8 border-white shadow-2xl shadow-slate-900/8 group">
                            <img
                                src={heroClinic}
                                alt="Clínica Dental Moderna Healthy Dental"
                                className="w-full h-auto object-cover aspect-[4/3] sm:aspect-[16/10] lg:aspect-[4/3] group-hover:scale-102 transition-transform duration-700"
                            />
                        </div>

                        {/* FLOATING CARD 1 */}
                        <div className="absolute -top-4 -left-4 z-20 bg-white/95 backdrop-blur-md px-5 py-3 rounded-2xl shadow-xl shadow-slate-900/5 border border-slate-100 flex items-center space-x-3 animate-float">
                            <div className="bg-emerald-50 p-2 rounded-xl">
                                <Award className="w-5 h-5 text-emerald-600" />
                            </div>
                            <div>
                                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Certificación</p>
                                <p className="text-xs font-black text-slate-800">Calidad Premium</p>
                            </div>
                        </div>

                        {/* FLOATING CARD 2 */}
                        <div className="absolute -bottom-6 -right-4 z-20 bg-white/95 backdrop-blur-md px-6 py-4 rounded-2xl shadow-xl shadow-slate-900/5 border border-slate-100 text-center">
                            <p className="text-2xl font-black text-indigo-600 leading-none">99.8%</p>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-1.5">Satisfacción Clínica</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Hero;
