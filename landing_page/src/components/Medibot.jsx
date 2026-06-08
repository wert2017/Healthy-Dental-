import React, { useState } from 'react';
import { MessageCircle, X, Send } from 'lucide-react';

const Medibot = () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end">
            {/* CHAT WINDOW */}
            {isOpen && (
                <div className="mb-4 w-[350px] max-w-[calc(100vw-48px)] bg-white rounded-[28px] shadow-2xl shadow-slate-900/15 overflow-hidden border border-slate-100 animate-in slide-in-from-bottom-5 duration-300">
                    {/* HEADER */}
                    <div className="bg-gradient-to-r from-indigo-600 to-indigo-700 p-4 text-white flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-white/15 rounded-full flex items-center justify-center">
                                <MessageCircle className="w-5.5 h-5.5 text-white" />
                            </div>
                            <div>
                                <h4 className="font-extrabold text-sm tracking-tight">Medibot</h4>
                                <p className="text-[10px] text-white/80 font-medium">Asistente Virtual 24/7</p>
                            </div>
                        </div>
                        <button onClick={() => setIsOpen(false)} className="hover:bg-white/10 p-1.5 rounded-lg transition-colors">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* MESSAGES AREA (MOCK) */}
                    <div className="h-80 p-4 bg-slate-50 overflow-y-auto space-y-4">
                        <div className="bg-white p-3.5 rounded-2xl rounded-tl-none shadow-sm max-w-[85%] border border-slate-100">
                            <p className="text-sm text-slate-700 leading-relaxed">
                                ¡Hola! Soy Medibot de Healthy Dental. 👋 ¿En qué puedo ayudarte hoy?
                            </p>
                        </div>
                    </div>

                    {/* INPUT AREA */}
                    <div className="p-4 bg-white border-t border-slate-100 flex items-center space-x-2">
                        <input
                            type="text"
                            placeholder="Escribe tu mensaje..."
                            className="flex-1 bg-slate-100 border-none rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-600/20 outline-none placeholder-slate-400 text-slate-700"
                            readOnly
                        />
                        <button className="bg-indigo-600 hover:bg-indigo-700 p-2.5 rounded-xl text-white shadow-md shadow-indigo-600/10 transition">
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            {/* FLOAT BUTTON */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`w-16 h-16 rounded-full flex items-center justify-center text-white shadow-2xl transition-all duration-500 hover:scale-110 active:scale-95 ${isOpen ? 'bg-slate-800 rotate-90' : 'bg-gradient-to-tr from-indigo-600 to-indigo-700 hover:shadow-indigo-600/20 animate-float'}`}
            >
                {isOpen ? <X className="w-7 h-7" /> : <MessageCircle className="w-7 h-7" />}
                {!isOpen && (
                    <span className="absolute -top-0.5 -right-0.5 flex h-4.5 w-4.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-4.5 w-4.5 bg-emerald-400 border-2 border-white"></span>
                    </span>
                )}
            </button>
        </div>
    );
};

export default Medibot;
