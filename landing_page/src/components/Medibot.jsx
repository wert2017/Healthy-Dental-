import React, { useState } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';

const Medibot = () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end">
            {/* CHAT WINDOW */}
            {isOpen && (
                <div className="mb-4 w-[350px] max-w-[calc(100vw-48px)] bg-white rounded-3xl shadow-2xl overflow-hidden border border-gray-100 animate-in slide-in-from-bottom-5 duration-300">
                    {/* HEADER */}
                    <div className="bg-dentist-blue p-4 text-white flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                                <MessageCircle className="w-6 h-6" />
                            </div>
                            <div>
                                <h4 className="font-bold text-sm">Medibot</h4>
                                <p className="text-xs text-white/80">Asistente Virtual 24/7</p>
                            </div>
                        </div>
                        <button onClick={() => setIsOpen(false)} className="hover:bg-white/10 p-1.5 rounded-lg transition-colors">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* MESSAGES AREA (MOCK) */}
                    <div className="h-80 p-4 bg-gray-50 overflow-y-auto space-y-4">
                        <div className="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm max-w-[85%] border border-gray-100">
                            <p className="text-sm text-gray-800 italic">"¡Hola! Soy Medibot de Healthy Dental. 👋 ¿En qué puedo ayudarte hoy?"</p>
                        </div>
                    </div>

                    {/* INPUT AREA */}
                    <div className="p-4 bg-white border-t border-gray-100 flex items-center space-x-2">
                        <input
                            type="text"
                            placeholder="Escribe tu mensaje..."
                            className="flex-1 bg-gray-100 border-none rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-dentist-blue/20 outline-none"
                            readOnly
                        />
                        <button className="bg-dentist-blue p-2 rounded-xl text-white">
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            {/* FLOAT BUTTON */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`w-16 h-16 rounded-full flex items-center justify-center text-white shadow-2xl transition-all duration-500 hover:scale-110 active:scale-95 ${isOpen ? 'bg-gray-800 rotate-90' : 'bg-dentist-blue hover:bg-dentist-dark animate-float'}`}
            >
                {isOpen ? <X className="w-8 h-8" /> : <MessageCircle className="w-8 h-8" />}
                {!isOpen && (
                    <span className="absolute -top-1 -right-1 flex h-5 w-5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-dentist-turquoise opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-5 w-5 bg-dentist-turquoise border-2 border-white"></span>
                    </span>
                )}
            </button>
        </div>
    );
};

export default Medibot;
