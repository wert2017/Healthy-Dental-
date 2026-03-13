import React from 'react';
import { Calendar, ChevronRight } from 'lucide-react';

const Hero = () => {
    return (
        <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
            {/* BACKGROUND ELEMENTS */}
            <div className="absolute top-0 right-0 -z-10 w-1/2 h-full bg-dentist-light rounded-l-[100px] opacity-70 hidden lg:block"></div>
            <div className="absolute top-1/4 left-1/4 -z-10 w-64 h-64 bg-dentist-turquoise/10 blur-[100px] rounded-full animate-pulse"></div>

            <div className="container mx-auto px-4 md:px-6">
                <div className="flex flex-col lg:flex-row items-center gap-12">
                    {/* TEXT CONTENT */}
                    <div className="flex-1 text-center lg:text-left space-y-8 max-w-2xl">
                        <div className="inline-flex items-center space-x-2 bg-dentist-light border border-dentist-blue/20 text-dentist-dark px-4 py-1.5 rounded-full text-sm font-semibold animate-bounce-subtle">
                            <span className="flex h-2 w-2 rounded-full bg-dentist-blue"></span>
                            <span>Sonrisas saludables, vidas felices</span>
                        </div>

                        <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 leading-tight">
                            Cuidado Dental de <span className="text-dentist-blue">Excelencia</span> para toda tu Familia
                        </h1>

                        <p className="text-lg md:text-xl text-gray-600 leading-relaxed font-light">
                            En Healthy Dental combinamos tecnología de vanguardia con un trato humano
                            y profesional para brindarte la mejor atención odontológica en Quito.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-4">
                            <button className="w-full sm:w-auto flex items-center justify-center space-x-3 bg-dentist-blue hover:bg-dentist-dark text-white px-8 py-4 rounded-2xl font-bold text-lg transition-all shadow-xl shadow-dentist-blue/30 group">
                                <Calendar className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                                <span>Agendar Cita Ahora</span>
                            </button>

                            <button className="w-full sm:w-auto flex items-center justify-center space-x-2 text-gray-700 hover:text-dentist-blue px-6 py-4 font-semibold transition-colors">
                                <span>Nuestros Servicios</span>
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>

                        {/* STATS/PROOFS */}
                        <div className="flex items-center justify-center lg:justify-start space-x-8 pt-6 border-t border-gray-100">
                            <div>
                                <p className="text-2xl font-bold text-gray-900">10k+</p>
                                <p className="text-sm text-gray-500 font-medium tracking-wide border-b-2 border-dentist-turquoise">Pacientes</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900">15+</p>
                                <p className="text-sm text-gray-500 font-medium tracking-wide border-b-2 border-dentist-blue">Especialistas</p>
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900">4.9/5</p>
                                <p className="text-sm text-gray-500 font-medium tracking-wide border-b-2 border-dentist-accent">Valoración</p>
                            </div>
                        </div>
                    </div>

                    {/* IMAGE/ALT CONTENT */}
                    <div className="flex-1 relative w-full max-w-xl">
                        <div className="relative z-10 rounded-[40px] overflow-hidden border-8 border-white shadow-2xl animate-float">
                            <img
                                src="https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&q=80&w=800"
                                alt="Doctora dental en Healthy Dental"
                                className="w-full h-auto object-cover aspect-[4/5]"
                            />
                        </div>
                        {/* DECORATIVE SHAPES */}
                        <div className="absolute -top-10 -right-10 -z-10 w-40 h-40 bg-dentist-turquoise/20 rounded-full blur-2xl"></div>
                        <div className="absolute -bottom-10 -left-10 -z-10 w-40 h-40 bg-dentist-blue/20 rounded-full blur-2xl"></div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Hero;
