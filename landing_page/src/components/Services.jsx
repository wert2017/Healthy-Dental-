import React from 'react';
import { Shield, Sparkles, Smile, HeartHandshake } from 'lucide-react';

const services = [
    {
        title: 'Odontología General',
        description: 'Diagnóstico integral, prevención, limpiezas y calzas de alta estética para mantener tu sonrisa sana y libre de dolor.',
        icon: Shield,
        iconColor: 'text-blue-600',
        bgColor: 'bg-blue-50',
    },
    {
        title: 'Ortodoncia Avanzada',
        description: 'Alineación de piezas y corrección de mordida usando brackets estéticos o alineadores invisibles de última tecnología.',
        icon: Smile,
        iconColor: 'text-sky-600',
        bgColor: 'bg-sky-50',
    },
    {
        title: 'Estética Dental',
        description: 'Diseño de sonrisa personalizado, carillas dentales de porcelana y blanqueamiento para lograr la sonrisa de tus sueños.',
        icon: Sparkles,
        iconColor: 'text-teal-600',
        bgColor: 'bg-teal-50',
    },
    {
        title: 'Calidez y Cuidado',
        description: 'Tratamientos especializados con un enfoque humano, sin dolor y adaptado a pacientes con ansiedad o niños.',
        icon: HeartHandshake,
        iconColor: 'text-emerald-600',
        bgColor: 'bg-emerald-50',
    },
];

const Services = () => {
    return (
        <section id="servicios" className="py-24 bg-white border-t border-slate-100">
            <div className="container mx-auto px-4 md:px-6">
                <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
                    <h2 className="text-blue-600 font-extrabold tracking-widest uppercase text-xs sm:text-sm">Nuestros Servicios</h2>
                    <h3 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">Soluciones Dentales de Nivel Premium</h3>
                    <p className="text-slate-500 font-light text-base sm:text-lg">Ofrecemos una atención dental completa e integral combinando tecnología de vanguardia y un equipo médico de alto nivel.</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {services.map((service, index) => (
                        <div
                            key={index}
                            className="group bg-white p-8 rounded-3xl shadow-sm border border-slate-200/60 hover:border-blue-500/20 hover:shadow-2xl hover:shadow-slate-200/50 transition duration-300 transform hover:-translate-y-1.5 cursor-pointer"
                        >
                            <div className={`${service.bgColor} w-14 h-14 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                                <service.icon className={`${service.iconColor} w-7 h-7`} />
                            </div>
                            <h4 className="text-xl font-bold text-slate-800 mb-3 group-hover:text-blue-600 transition-colors duration-300">{service.title}</h4>
                            <p className="text-slate-500 leading-relaxed text-sm">
                                {service.description}
                            </p>
                            <div className="mt-6 flex items-center text-blue-600 font-bold text-xs uppercase tracking-wider opacity-0 group-hover:opacity-100 transition-all duration-300">
                                <span>Saber más</span>
                                <span className="ml-1.5 transform group-hover:translate-x-1 transition-transform">→</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Services;
