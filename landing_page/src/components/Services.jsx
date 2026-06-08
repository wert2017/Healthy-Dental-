import React from 'react';
import { Shield, Sparkles, Smile, HeartHandshake } from 'lucide-react';

const services = [
    {
        title: 'Odontología General',
        description: 'Diagnóstico integral, prevención, limpiezas y calzas de alta estética para mantener tu sonrisa sana y libre de dolor.',
        icon: Shield,
        iconColor: 'text-indigo-600',
        bgColor: 'bg-indigo-50/80',
        hoverColor: 'group-hover:text-indigo-600',
        borderColor: 'hover:border-indigo-500/20',
        glowColor: 'hover:shadow-indigo-500/5',
    },
    {
        title: 'Ortodoncia Avanzada',
        description: 'Alineación de piezas y corrección de mordida usando brackets estéticos o alineadores invisibles de última tecnología.',
        icon: Smile,
        iconColor: 'text-purple-600',
        bgColor: 'bg-purple-50/80',
        hoverColor: 'group-hover:text-purple-600',
        borderColor: 'hover:border-purple-500/20',
        glowColor: 'hover:shadow-purple-500/5',
    },
    {
        title: 'Estética Dental',
        description: 'Diseño de sonrisa personalizado, carillas dentales de porcelana y blanqueamiento para lograr la sonrisa de tus sueños.',
        icon: Sparkles,
        iconColor: 'text-emerald-600',
        bgColor: 'bg-emerald-50/80',
        hoverColor: 'group-hover:text-emerald-600',
        borderColor: 'hover:border-emerald-500/20',
        glowColor: 'hover:shadow-emerald-500/5',
    },
    {
        title: 'Calidez y Cuidado',
        description: 'Tratamientos especializados con un enfoque humano, sin dolor y adaptado a pacientes con ansiedad o niños.',
        icon: HeartHandshake,
        iconColor: 'text-pink-600',
        bgColor: 'bg-pink-50/80',
        hoverColor: 'group-hover:text-pink-600',
        borderColor: 'hover:border-pink-500/20',
        glowColor: 'hover:shadow-pink-500/5',
    },
];

const Services = () => {
    return (
        <section id="servicios" className="py-24 bg-transparent border-t border-indigo-100/30 relative">
            {/* Background design elements */}
            <div className="absolute top-1/2 left-10 w-72 h-72 bg-purple-100/30 blur-[130px] rounded-full -z-10"></div>
            <div className="absolute bottom-10 right-10 w-72 h-72 bg-indigo-100/30 blur-[130px] rounded-full -z-10"></div>

            <div className="container mx-auto px-4 md:px-6">
                <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
                    <h2 className="text-indigo-600 font-extrabold tracking-widest uppercase text-xs sm:text-sm">Nuestros Servicios</h2>
                    <h3 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">Soluciones Dentales de Nivel Premium</h3>
                    <p className="text-slate-500 font-light text-base sm:text-lg">Ofrecemos una atención dental completa e integral combinando tecnología de vanguardia y un equipo médico de alto nivel.</p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {services.map((service, index) => (
                        <div
                            key={index}
                            className={`group bg-white p-8 rounded-[32px] shadow-sm border border-slate-200/50 ${service.borderColor} ${service.glowColor} hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 cursor-pointer`}
                        >
                            <div className={`${service.bgColor} w-14 h-14 rounded-2xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300`}>
                                <service.icon className={`${service.iconColor} w-7 h-7`} />
                            </div>
                            <h4 className={`text-xl font-bold text-slate-800 mb-3.5 ${service.hoverColor} transition-colors duration-300`}>{service.title}</h4>
                            <p className="text-slate-500 leading-relaxed text-sm font-light">
                                {service.description}
                            </p>
                            <div className={`mt-8 flex items-center ${service.iconColor} font-bold text-xs uppercase tracking-wider opacity-0 group-hover:opacity-100 transition-all duration-300`}>
                                <span>Saber más</span>
                                <span className="ml-1.5 transform group-hover:translate-x-1.5 transition-transform">→</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Services;
