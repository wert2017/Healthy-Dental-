from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, Relationship, SQLModel

# --- Enums (Simulated with CONSTANTS or just Strings for simplicity) ---

class Sucursal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True)
    direccion: Optional[str] = None

    doctores: List["Doctor"] = Relationship(back_populates="sucursal")

    def __str__(self):
        return self.nombre


class Doctor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombres: str
    apellidos: str
    cedula: str = Field(unique=True)
    telefono: Optional[str] = None
    email: Optional[str] = None
    activo: bool = True
    
    sucursal_id: Optional[int] = Field(default=None, foreign_key="sucursal.id")
    sucursal: Optional[Sucursal] = Relationship(back_populates="doctores")

    atenciones: List["Atencion"] = Relationship(back_populates="doctor")

    def __str__(self):
        return f"Dr. {self.nombres} {self.apellidos}"


class Paciente(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tipo_identificacion: Optional[str] = Field(default="S/N")
    numero_identificacion: Optional[str] = Field(default=None, unique=True)
    nombres: str
    apellidos: Optional[str] = Field(default="")
    razon_social: Optional[str] = None
    historia_clinica: str = Field(unique=True)
    telefono: Optional[str] = Field(default="")
    email: Optional[str] = None
    sexo: Optional[str] = None
    edad: Optional[int] = None
    ciudad: Optional[str] = None
    activo: bool = True
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    
    sucursal_id: Optional[int] = Field(default=None, foreign_key="sucursal.id")
    sucursal: Optional["Sucursal"] = Relationship()
    
    # Billetera Virtual
    saldo_favor: Decimal = Field(default=0, max_digits=10, decimal_places=2)

    atenciones: List["Atencion"] = Relationship(back_populates="paciente", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    tratamientos_en_curso: List["TratamientoEnCurso"] = Relationship(back_populates="paciente", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    historial_abonos: List["HistorialAbono"] = Relationship(back_populates="paciente", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    
    @property
    def nombre_mostrar(self):
        if self.tipo_identificacion == 'RUC' and self.razon_social:
            return self.razon_social
        return f"{self.nombres or ''} {self.apellidos or ''}".strip()

    def __str__(self):
        return self.nombre_mostrar


class Tratamiento(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str
    nombre: str
    precio_base: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    activo: bool = True

    # Link to Recetas (Inventory)
    insumos_requeridos: List["Receta"] = Relationship(back_populates="tratamiento")

    def __str__(self):
        return self.nombre

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="admin")
    
    # Links for Roles
    doctor_id: Optional[int] = Field(default=None, foreign_key="doctor.id")
    sucursal_id: Optional[int] = Field(default=None, foreign_key="sucursal.id")
    
    doctor: Optional["Doctor"] = Relationship()
    sucursal: Optional["Sucursal"] = Relationship()

class TratamientoEnCurso(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paciente_id: int = Field(foreign_key="paciente.id")
    tratamiento_id: int = Field(foreign_key="tratamiento.id")
    fecha_inicio: datetime = Field(default_factory=datetime.now)
    fecha_fin: Optional[datetime] = None
    activo: bool = True
    
    paciente: Optional["Paciente"] = Relationship(back_populates="tratamientos_en_curso")
    tratamiento: Optional["Tratamiento"] = Relationship()

class Atencion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=datetime.now)
    observaciones: Optional[str] = None
    estado: str = "EN_PROCESO"
    validado: bool = False
    
    paciente_id: int = Field(foreign_key="paciente.id")
    paciente: Optional[Paciente] = Relationship(back_populates="atenciones")
    
    doctor_id: Optional[int] = Field(default=None, foreign_key="doctor.id")
    doctor: Optional[Doctor] = Relationship(back_populates="atenciones")
    
    sucursal_id: Optional[int] = Field(default=None, foreign_key="sucursal.id")
    sucursal: Optional[Sucursal] = Relationship()
    
    detalles: List["AtencionDetalle"] = Relationship(back_populates="atencion", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    pagos: List["Pago"] = Relationship(back_populates="atencion", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    auditoria_atenciones: List["AuditoriaAtencion"] = Relationship(back_populates="atencion", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    @property
    def total_pagado(self) -> Decimal:
        return sum([p.monto for p in self.pagos])
    
    @property
    def total_atencion_valor(self) -> Decimal:
        return sum([d.total_calculado for d in self.detalles])

    @property
    def saldo_pendiente(self) -> Decimal:
        return self.total_atencion_valor - self.total_pagado

    def __str__(self):
        paciente = self.paciente.nombre_mostrar if self.paciente else f"Paciente #{self.paciente_id}"
        return f"Atención #{self.id} — {paciente}"

class AtencionDetalle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    atencion_id: int = Field(foreign_key="atencion.id")
    tratamiento_id: int = Field(foreign_key="tratamiento.id") # Optional link if needed
    doctor_id: Optional[int] = Field(default=None, foreign_key="doctor.id")
    

    cantidad: int = 1
    precio_unitario: Decimal = Field(max_digits=10, decimal_places=2)
    porcentaje_comision: Decimal = Field(default=0, max_digits=5, decimal_places=2)
    
    # Payroll / Commissions Tracking
    comision_pagada: bool = Field(default=False)
    comision_pagada_monto: float = Field(default=0.0)
    fecha_pago_comision: Optional[datetime] = None
    vendedor_id: Optional[int] = Field(default=None, foreign_key="user.id") # Usually for secretaries selling kits
    
    # Relationships
    atencion: Optional[Atencion] = Relationship(back_populates="detalles")
    tratamiento: Optional[Tratamiento] = Relationship()
    doctor: Optional[Doctor] = Relationship()
    vendedor: Optional[User] = Relationship()
    
    @property
    def total_calculado(self) -> Decimal:
        return self.precio_unitario * self.cantidad
    
    @property
    def comision_valor(self) -> Decimal:
        return self.total_calculado * (self.porcentaje_comision / 100)

    def __str__(self):
        nombre = self.tratamiento.nombre if self.tratamiento else f"Tratamiento #{self.tratamiento_id}"
        return f"{nombre} x{self.cantidad} — ${self.precio_unitario}"

class Pago(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    atencion_id: int = Field(foreign_key="atencion.id")
    
    fecha: datetime = Field(default_factory=datetime.now)
    forma_pago: str # EFECTIVO, TRANSFERENCIA, TARJETA
    monto: Decimal = Field(max_digits=10, decimal_places=2)
    referencia: Optional[str] = None # Transaction ID for transfers

    atencion: Optional[Atencion] = Relationship(back_populates="pagos")

    def __str__(self):
        return f"{self.forma_pago} — ${self.monto}"

class AuditoriaAtencion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    atencion_id: Optional[int] = Field(default=None, foreign_key="atencion.id")
    usuario_id: Optional[int] = Field(default=None, foreign_key="user.id")
    fecha: datetime = Field(default_factory=datetime.now)
    accion: str
    descripcion: str
    
    atencion: Optional["Atencion"] = Relationship(back_populates="auditoria_atenciones")
    usuario: Optional["User"] = Relationship()

class HistorialAbono(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paciente_id: int = Field(foreign_key="paciente.id")
    usuario_id: Optional[int] = Field(default=None, foreign_key="user.id")
    fecha: datetime = Field(default_factory=datetime.now)
    monto: Decimal = Field(max_digits=10, decimal_places=2)
    metodo_pago: str # EFECTIVO, TRANSFERENCIA, TARJETA
    
    paciente: Optional["Paciente"] = Relationship(back_populates="historial_abonos")
    usuario: Optional["User"] = Relationship()

# --- INVENTORY MODELS (Level 3) ---

class Proveedor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    activo: bool = True
    
    insumos: List["Insumo"] = Relationship(back_populates="proveedor")

class InventarioSucursal(SQLModel, table=True):
    """Tracks stock level of an Insumo at a specific Sucursal"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    sucursal_id: int = Field(foreign_key="sucursal.id")
    insumo_id: int = Field(foreign_key="insumo.id")
    
    stock_actual: int = Field(default=0)
    stock_minimo: int = Field(default=5)
    
    sucursal: Optional[Sucursal] = Relationship()
    insumo: Optional["Insumo"] = Relationship(back_populates="inventarios_sucursal")

class InventarioDoctor(SQLModel, table=True):
    """Level 3: Personal stock assigned to a Doctor (The 'Maletin')"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    doctor_id: int = Field(foreign_key="doctor.id")
    insumo_id: int = Field(foreign_key="insumo.id")
    
    stock_actual: int = Field(default=0)
    
    doctor: Optional[Doctor] = Relationship()
    insumo: Optional["Insumo"] = Relationship(back_populates="inventarios_doctor")

class Insumo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    unidad_medida: str # e.g. "Unidad", "Caja", "ml"
    
    # Bodega Central Stock
    stock_actual: int = Field(default=0) 
    stock_minimo: int = Field(default=5)
    
    # Proveedor Link
    proveedor_id: Optional[int] = Field(default=None, foreign_key="proveedor.id")
    proveedor: Optional[Proveedor] = Relationship(back_populates="insumos")
    
    recetas: List["Receta"] = Relationship(back_populates="insumo")
    inventarios_sucursal: List["InventarioSucursal"] = Relationship(back_populates="insumo")
    inventarios_doctor: List["InventarioDoctor"] = Relationship(back_populates="insumo")

    def __str__(self):
        return self.nombre

class Receta(SQLModel, table=True):
    """Links a Tratamiento to an Insumo (The Recipe)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    tratamiento_id: int = Field(foreign_key="tratamiento.id")
    insumo_id: int = Field(foreign_key="insumo.id")
    
    cantidad_requerida: int = Field(default=1, description="Quantity consumed per treatment")
    
    tratamiento: Optional[Tratamiento] = Relationship(back_populates="insumos_requeridos")
    insumo: Optional[Insumo] = Relationship(back_populates="recetas")

class CategoriaGasto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
    activo: bool = True

    def __str__(self):
        return self.nombre


class Gasto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=datetime.now)
    descripcion: str
    monto: Decimal = Field(max_digits=10, decimal_places=2)
    metodo_pago: str # EFECTIVO, TRANSFERENCIA
    categoria: Optional[str] = "GENERAL"
    responsable: Optional[str] = None # Name of the person who made the expense
    
    sucursal_id: int = Field(foreign_key="sucursal.id")
    usuario_id: int = Field(foreign_key="user.id")
    
    sucursal: Optional[Sucursal] = Relationship()
    usuario: Optional[User] = Relationship()
