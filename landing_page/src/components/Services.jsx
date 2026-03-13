import React from 'react';
import { Shield, Sparkles, Smile, Wrench } from 'lucide-react';

const services = [
    {
        title: 'Odontología General',
        description: 'Diagnóstico, prevención y tratamiento de los problemas dentales habituales para mantener una óptima salud bucal.',
        icon: Shield,
        color: 'bg-dentist-blue',
    },
    {
        title: 'Ortodoncia',
        description: 'Alineación de dientes y corrección de problemas de mordida mediante brackets o alineadores transparentes de última generación.',
        icon: Smile,
        color: 'bg-dentist-turquoise',
    },
    {
        title: 'Implantes Dentales',
        description: 'Restauración de piezas faltantes con prótesis fijas de alta calidad que se sienten y lucen totalmente naturales.',
        icon: Wrench,
        color: 'bg-dentist-dark',
    },
    {
        title: 'Estética Dental',
        description: 'Diseño de sonrisa, carillas y blanqueamiento dental para que luzcas la sonrisa que siempre has deseado.',
        icon: Sparkles,
        color: 'bg-dentist-accent',
    },
];

const Services = () => {
    return (
        <section id="servicios" className="py-24 bg-dentist-light/30">
            <div className="container mx-auto px-4 md:px-6">
                <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
                    <h2 className="text-blue-600 font-bold tracking-widest uppercase text-sm">Nuestra Experiencia</h2>
                    <h3 className="text-3xl md:text-4xl font-bold text-gray-900">Servicios Especializados para tu Bienestar</h3>
                    <p className="text-gray-600">Ofrecemos soluciones integrales con tecnología de punta y un equipo de profesionales comprometidos con tu salud dental.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {services.map((service, index) => (
                        <div
                            key={index}
                            className="group bg-white p-8 rounded-[32px] shadow-sm hover:shadow-xl hover:shadow-dentist-blue/10 transition-all border border-gray-100 hover:-translate-y-2 cursor-pointer"
                        >
                            <div className={`${service.color} w-16 h-16 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                                <service.icon className="text-white w-8 h-8" />
                            </div>
                            <h4 className="text-xl font-bold text-gray-900 mb-4">{service.title}</h4>
                            <p className="text-gray-600 leading-relaxed text-sm">
                                {service.description}
                            </p>
                            <div className="mt-6 flex items-center text-dentist-blue font-semibold text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                                <span>Saber más</span>
                                <span className="ml-2">→</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Services;
