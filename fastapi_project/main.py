from fastapi import FastAPI, Depends, HTTPException, Query, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import engine, create_db_and_tables, get_session
from models import Paciente, Doctor, Sucursal, Tratamiento, Atencion, AtencionDetalle, Pago, User, TratamientoEnCurso, Insumo, Receta, Proveedor, InventarioSucursal, InventarioDoctor, AuditoriaAtencion, Gasto, HistorialAbono
from sqlmodel import Field, Session, SQLModel, select, create_engine, Relationship
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin, ModelView, BaseView, expose
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.responses import RedirectResponse
import uvicorn
import os
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from wtforms import SelectField

import locale
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    pass # Fallback if system doesn't have it

app = FastAPI(title="Clinica HD API")

# --- CORS CONFIGURATION ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fix for HTTPS behind proxy (Railway)
@app.middleware("http")
async def fix_proxy_headers(request: Request, call_next):
    # If the request comes through a proxy with HTTPS, force the scheme to https
    # This ensures url_for and other helpers generate https links, fixing CSS/JS issues
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    response = await call_next(request)
    return response

# --- ROUTERS ---
from inventario_router import router as inventario_router
app.include_router(inventario_router)

# --- AUTH SECURITY ---
SECRET_KEY = "super_secret_key_change_this_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 Hours

# Switch to pbkdf2_sha256 to avoid bcrypt/passlib version conflict on Windows
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        sucursal_id_token: Optional[int] = payload.get("sucursal_id") # Read from JWT
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    
    # CRITICAL: Overwrite the DB sucursal_id with the one from the Token
    # This allows admins to have a 'sucursal_id' in memory during their session
    if sucursal_id_token:
        user.sucursal_id = sucursal_id_token
        
    return user

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # Create or Reset Default Admin User
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == "admin")).first()
        if not user:
            print("Creating default admin user...")
            hashed = pwd_context.hash("admin")
            admin_user = User(username="admin", hashed_password=hashed, role="admin")
            session.add(admin_user)
        else:
            print("Resetting admin password to 'admin'...")
            user.hashed_password = pwd_context.hash("admin")
            session.add(user)
        
        # Test User 'ana'
        ana = session.exec(select(User).where(User.username == "ana")).first()
        if not ana:
            print("Creating test user 'ana'...")
            s_id = session.exec(select(Sucursal.id)).first()
            ana_user = User(username="ana", hashed_password=pwd_context.hash("123"), role="recepcion", sucursal_id=s_id)
            session.add(ana_user)
            
        session.commit()

@app.get("/api/public/sucursales")
def list_public_sucursales(session: Session = Depends(get_session)):
    """Publicly list sucursales for the login screen."""
    return session.exec(select(Sucursal)).all()

@app.post("/token")
async def login_for_access_token(
    response: JSONResponse, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    sucursal_id: Optional[int] = Form(None), # Added for clinic selection
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate Sucursal selection if Provided
    final_sucursal_id = sucursal_id
    if user.role != "admin":
        if user.sucursal_id and sucursal_id and user.sucursal_id != sucursal_id:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta sucursal")
        # If user has a fixed sucursal and didn't provide one, use their fixed one
        if user.sucursal_id and not sucursal_id:
            final_sucursal_id = user.sucursal_id
    
    if not final_sucursal_id:
         # For admins or users without a fixed sucursal who didn't pick one, we might need a default or error
         # Let's say we require it if available
         pass

    # Set role cookie for Admin Panel seamless access
    response.set_cookie(key="user_role", value=user.role, httponly=False) 
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "doctor_id": user.doctor_id,
            "sucursal_id": final_sucursal_id
        }, 
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user.role,
        "doctor_id": user.doctor_id,
        "sucursal_id": final_sucursal_id
    }

# Main redirects
@app.get("/")
def root():
    # Serve landing page if built, otherwise redirect to reception
    # Use absolute paths relative to this file to be robust
    current_dir = os.path.dirname(os.path.abspath(__file__))
    landing_index = os.path.join(current_dir, "..", "landing_page", "dist", "index.html")
    
    if os.path.exists(landing_index):
        return FileResponse(landing_index)
    
    print(f"DEBUG: Landing page not found at {landing_index}")
    return RedirectResponse("/recepcion")

# Mount React Landing Page (Assets)
current_dir = os.path.dirname(os.path.abspath(__file__))
LANDING_DIR = os.path.join(current_dir, "..", "landing_page", "dist")
if os.path.exists(LANDING_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(LANDING_DIR, "assets")), name="assets")

# Protected Routes - Pages
@app.get("/login")
def login_page():
    return FileResponse("static/login.html")

@app.get("/recepcion", response_class=HTMLResponse)
def recepcion_page(): # Not strictly protecting the HTML serving, but the data inside will be protected. Ideally protect this too.
    # To protect HTML serving, we need to check cookie or token, but standard OAuth2 + Bearer is for API.
    # For simplicity, we serve the HTML publicly, but if you have no token, the API calls inside will fail and redirect you.
    return FileResponse("static/recepcion.html")

@app.get("/recepcion/editar/{atencion_id}", response_class=HTMLResponse)
def editar_atencion_page(atencion_id: int):
    return FileResponse("static/editar.html")

@app.get("/recepcion/imprimir/{atencion_id}", response_class=HTMLResponse)
def imprimir_atencion_page(atencion_id: int):
    return FileResponse("static/imprimir.html") 

@app.get("/gastos", response_class=HTMLResponse)
def gastos_page():
    return FileResponse("static/gastos.html")

@app.get("/admin/inventario", response_class=HTMLResponse)
def admin_inventario_page():
    return FileResponse("static/inventario.html") 

@app.get("/doctor/dashboard", response_class=HTMLResponse)
def doctor_dashboard_page():
     return FileResponse("static/doctor_dashboard.html") 


# --- ADMIN VIEWS ---
class PacienteAdmin(ModelView, model=Paciente):
    name = "Paciente"
    name_plural = "Pacientes"
    icon = "fa-solid fa-user"
    
    # List View configuration
    column_list = [Paciente.historia_clinica, Paciente.numero_identificacion, Paciente.nombres, Paciente.apellidos, Paciente.telefono]
    column_searchable_list = [Paciente.nombres, Paciente.apellidos, Paciente.numero_identificacion]
    
    # Form Configuration (Create/Edit)
    form_columns = [
        Paciente.tipo_identificacion,
        Paciente.numero_identificacion,
        Paciente.nombres,
        Paciente.apellidos,
        Paciente.razon_social,
        Paciente.historia_clinica,
        Paciente.telefono,
        Paciente.email
    ]
    
    # Restrict choices for Tipo Identificacion using WTForms SelectField
    form_overrides = {
        "tipo_identificacion": SelectField
    }
    form_args = {
        "tipo_identificacion": {
            "choices": [("CEDULA", "CEDULA"), ("RUC", "RUC")],
            "label": "Tipo Identificacion"
        }
    }

    # We explicitly exclude 'atenciones' and 'fecha_creacion' from the form

class DoctorAdmin(ModelView, model=Doctor):
    column_list = [Doctor.apellidos, Doctor.nombres, Doctor.cedula, Doctor.sucursal, Doctor.activo]
    form_columns = [Doctor.nombres, Doctor.apellidos, Doctor.cedula, Doctor.telefono, Doctor.email, Doctor.sucursal, Doctor.activo]

    def is_accessible(self, request: Request) -> bool:
        return request.cookies.get("user_role") == "admin"
    
    def is_visible(self, request: Request) -> bool:
        return request.cookies.get("user_role") == "admin"

class SucursalAdmin(ModelView, model=Sucursal):
    column_list = [Sucursal.nombre, Sucursal.direccion]
    form_columns = [Sucursal.nombre, Sucursal.direccion]
    icon = "fa-solid fa-building"

    def is_accessible(self, request: Request) -> bool:
        return request.cookies.get("user_role") == "admin"
    
    def is_visible(self, request: Request) -> bool:
        return request.cookies.get("user_role") == "admin"

class UserAdmin(ModelView, model=User):
    name = "Usuario"
    name_plural = "Usuarios"
    column_list = [User.username, User.role, User.doctor, User.sucursal]
    form_columns = [User.username, "hashed_password", User.role, User.doctor, User.sucursal]
    icon = "fa-solid fa-users-gear"
    
    form_args = {
        "hashed_password": {"label": "Contraseña / Password"}
    }

    def is_accessible(self, request: Request) -> bool:
        return request.cookies.get("user_role") == "admin"
    
    def is_visible(self, request: Request) -> bool:
        return request.cookies.get("user_role") == "admin"

    async def on_model_change(self, data, model, is_created, request: Request):
        # Si se envió una contraseña (en creación o edición), la hasheamos
        if "hashed_password" in data and data["hashed_password"]:
            # Solo hasheamos si no parece ser ya un hash (para evitar doble hash en ediciones sin cambio)
            # Aunque lo ideal es que el formulario no muestre el hash.
            # Por ahora, si el usuario escribe algo, lo hasheamos.
            data["hashed_password"] = pwd_context.hash(data["hashed_password"])

class TratamientoAdmin(ModelView, model=Tratamiento):
    column_list = [Tratamiento.codigo, Tratamiento.nombre, Tratamiento.precio_base, Tratamiento.activo]
    form_columns = [Tratamiento.codigo, Tratamiento.nombre, Tratamiento.precio_base, Tratamiento.activo]

class AtencionAdmin(ModelView, model=Atencion):
    column_list = [Atencion.id, Atencion.fecha, Atencion.paciente, Atencion.estado, Atencion.validado]
    can_create = False # Attentions are created via Reception, not Admin typically

class PagoAdmin(ModelView, model=Pago):
    column_list = [Pago.id, Pago.forma_pago, Pago.monto, Pago.atencion_id]

# --- ADMIN HELPERS ---
from markupsafe import Markup

class InsumoAdmin(ModelView, model=Insumo):
    column_list = [Insumo.nombre, Insumo.stock_actual, Insumo.unidad_medida, Insumo.proveedor]
    form_columns = [Insumo.nombre, Insumo.unidad_medida, Insumo.stock_actual, Insumo.stock_minimo, Insumo.proveedor]
    icon = "fa-solid fa-boxes-stacked"

    # Visual Alert for Low Stock (Temporarily Disabled)
    # def stock_formatter(view, context, model, name):
    #     try:
    #         val = model.stock_actual if model.stock_actual is not None else 0
    #         min_val = model.stock_minimo if model.stock_minimo is not None else 0
    #         
    #         if val <= min_val:
    #             return Markup(f'<span style="color: red; font-weight: bold;">{val} (Bajo)</span>')
    #         return str(val)
    #     except Exception:
    #         return str(model.stock_actual)

    # column_formatters = {
    #     "stock_actual": stock_formatter
    # }

class RecetaAdmin(ModelView, model=Receta):
    name = "Receta (Configuración)"
    name_plural = "Configuración de Recetas"
    column_list = [Receta.tratamiento, Receta.insumo, Receta.cantidad_requerida]
    icon = "fa-solid fa-prescription-bottle-medical"

class ProveedorAdmin(ModelView, model=Proveedor):
    column_list = [Proveedor.nombre, Proveedor.contacto, Proveedor.telefono, Proveedor.email, Proveedor.activo]
    form_columns = [Proveedor.nombre, Proveedor.contacto, Proveedor.telefono, Proveedor.email, Proveedor.activo]
    icon = "fa-solid fa-truck"

class InventarioSucursalAdmin(ModelView, model=InventarioSucursal):
    name = "Stock por Sucursal"
    name_plural = "Stock Sucursales"
    column_list = [InventarioSucursal.sucursal, InventarioSucursal.insumo, InventarioSucursal.stock_actual]
    form_columns = [InventarioSucursal.sucursal, InventarioSucursal.insumo, InventarioSucursal.stock_actual, InventarioSucursal.stock_minimo]
    icon = "fa-solid fa-store"

class InventarioDoctorAdmin(ModelView, model=InventarioDoctor):
    name = "Stock Personal (Doctor)"
    name_plural = "Stock Personal Doctores"
    column_list = ["doctor", "insumo", "stock_actual"]
    icon = "fa-solid fa-user-doctor"

class MovimientosLink(BaseView):
    name = "Movimientos de Inventario"
    icon = "fa-solid fa-truck-ramp-box"
    
    @expose("/movimientos", methods=["GET"])
    def movements_page(self, request):
        return RedirectResponse(url="/static/inventario.html")

# --- APP STARTUP & SEEDING ---
def seed_data(session: Session):
    # Seed Sucursales (Clinics) - CRITICAL for first login
    if not session.exec(select(Sucursal)).first():
        sucursales = [
            Sucursal(nombre="Clínica Central", direccion="Av. Principal 123"),
            Sucursal(nombre="Sucursal Norte", direccion="Calle Norte 456"),
        ]
        for s in sucursales:
            session.add(s)
        session.commit()
        print("SEED: Sucursales agregadas.")

    # Seed Treatments
    if not session.exec(select(Tratamiento)).first():
        tratamientos = [
            Tratamiento(codigo="LDC", nombre="Lente de contacto", precio_base=150.00),
            Tratamiento(codigo="CAR", nombre="Carilla", precio_base=80.00),
            Tratamiento(codigo="BLA", nombre="Blanqueamiento", precio_base=120.00),
            Tratamiento(codigo="LIM", nombre="Limpieza", precio_base=30.00),
            Tratamiento(codigo="CAL", nombre="Calza", precio_base=40.00),
            Tratamiento(codigo="COR", nombre="Corona", precio_base=200.00),
            Tratamiento(codigo="EXT", nombre="Extraccion", precio_base=25.00),
            Tratamiento(codigo="END", nombre="Endodoncia", precio_base=180.00),
            Tratamiento(codigo="PRO", nombre="Protesis", precio_base=350.00),
        ]
        for t in tratamientos:
            session.add(t)
        print("SEED: Tratamientos agregados.")

    # Seed Doctors
    if not session.exec(select(Doctor)).first():
        doctores = [
            Doctor(nombres="Juan", apellidos="Perez", cedula="0900000001", telefono="0991234567"),
            Doctor(nombres="Ana", apellidos="Gomez", cedula="0900000002", telefono="0997654321"),
        ]
        for d in doctores:
            session.add(d)
        print("SEED: Doctores agregados.")

    # Seed Patients
    if not session.exec(select(Paciente)).first():
        pacientes = [
            Paciente(nombres="Carlos", apellidos="Ruiz", numero_identificacion="0999999999", tipo_identificacion="CEDULA", telefono="0987654321", email="carlos@example.com", historia_clinica="HC-1001"),
            Paciente(nombres="Maria", apellidos="Lopez", numero_identificacion="0988888888", tipo_identificacion="CEDULA", telefono="0911223344", email="maria@example.com", historia_clinica="HC-1002"),
            Paciente(nombres="Jose", apellidos="Vera", numero_identificacion="0977777777", tipo_identificacion="CEDULA", telefono="0955667788", email="jose@example.com", historia_clinica="HC-1003"),
        ]
        for p in pacientes:
            session.add(p)
        print("SEED: Pacientes agregados.")
    
    session.commit()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    with Session(engine) as session:
        seed_data(session)

# --- ADMIN SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(current_dir, "templates")

admin = Admin(app, engine, title="Admin - Clínica HD", templates_dir=templates_path)
# admin.add_view(BackToReception) # Custom view removed in favor of template override
admin.add_view(PacienteAdmin)
admin.add_view(DoctorAdmin)
admin.add_view(TratamientoAdmin)
admin.add_view(AtencionAdmin)
admin.add_view(PagoAdmin)
admin.add_view(SucursalAdmin) 
admin.add_view(InsumoAdmin)
admin.add_view(ProveedorAdmin)
admin.add_view(InventarioSucursalAdmin)
admin.add_view(InventarioDoctorAdmin)
admin.add_view(UserAdmin)
admin.add_view(MovimientosLink)
admin.add_view(RecetaAdmin)

# --- USER LIST FOR DROPDOWNS ---
@app.get("/api/usuarios")
def list_usuarios(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """Returns a list of active users to be used in dropdowns (e.g. Responsable de Gasto)"""
    usuarios = session.exec(select(User).order_by(User.username.asc())).all()
    # Return minimal data for security
    return [{"id": u.id, "username": u.username} for u in usuarios]

# --- STATIC FILES ---
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- HELPER FUNCTIONS ---
def process_stock_deduction(atencion: Atencion, session: Session, sucursal_id: int):
    """
    Deducts stock based on treatments in the attention.
    Should be called ONLY when validating an attention.
    Now supports Multi-Clinic logic: Deducts from InventarioSucursal.
    """
    if not sucursal_id:
        print("WARNING: No sucursal_id provided for stock deduction. Skipping.")
        return

    deductions_made = []
    
    for detalle in atencion.detalles:
        if detalle.tratamiento and detalle.tratamiento.insumos_requeridos:
            # Use the doctor from the detail (or the main doctor of the attention)
            current_doctor_id = detalle.doctor_id if detalle.doctor_id else atencion.doctor_id
            
            for receta in detalle.tratamiento.insumos_requeridos:
                cantidad_a_descontar = receta.cantidad_requerida * detalle.cantidad
                
                # 1. ATTEMPT PRIORITY: Personal Doctor stock (Level 3)
                inv_doctor = None
                if current_doctor_id:
                    inv_doctor = session.exec(select(InventarioDoctor).where(
                        InventarioDoctor.doctor_id == current_doctor_id,
                        InventarioDoctor.insumo_id == receta.insumo_id
                    )).first()

                if inv_doctor and inv_doctor.stock_actual >= cantidad_a_descontar:
                    # Deduct from Doctor personal stock
                    inv_doctor.stock_actual -= cantidad_a_descontar
                    session.add(inv_doctor)
                    deductions_made.append(f"{receta.insumo.nombre} (-{cantidad_a_descontar}) @ Doctor {current_doctor_id}")
                else:
                    # 2. FALLBACK: Sucursal Inventory (Level 2)
                    inv_suc = session.exec(select(InventarioSucursal).where(
                        InventarioSucursal.sucursal_id == sucursal_id,
                        InventarioSucursal.insumo_id == receta.insumo_id
                    )).first()
                    
                    if inv_suc:
                        inv_suc.stock_actual -= cantidad_a_descontar
                        session.add(inv_suc)
                        deductions_made.append(f"{receta.insumo.nombre} (-{cantidad_a_descontar}) @ Sucursal {sucursal_id}")
                    else:
                        # Fallback Create negative record if not exists in sucursal
                        new_inv = InventarioSucursal(
                            sucursal_id=sucursal_id,
                            insumo_id=receta.insumo_id,
                            stock_actual=-cantidad_a_descontar,
                            stock_minimo=0
                        )
                        session.add(new_inv)
                        deductions_made.append(f"{receta.insumo.nombre} (CREATED -{cantidad_a_descontar}) @ Sucursal {sucursal_id}")
    
    if deductions_made:
        print(f"STOCK UPDATE: Atencion {atencion.id} consumed: {', '.join(deductions_made)}")

# --- API ROUTES ---

@app.get("/api/pacientes")
def search_pacientes(q: str = "", session: Session = Depends(get_session)):
    if not q:
        return []
    
    terms = q.strip().split()
    statement = select(Paciente)
    
    for term in terms:
        statement = statement.where(
            (Paciente.nombres.contains(term)) | 
            (Paciente.apellidos.contains(term)) | 
            (Paciente.numero_identificacion.contains(term))
        )
        
    statement = statement.limit(10)
    pacientes = session.exec(statement).all()
    
    # Calculate financial status for each patient
    results_data = []
    for p in pacientes:
        total_consumido = sum([sum([d.total_calculado for d in a.detalles]) for a in p.atenciones])
        total_pagado = sum([sum([pay.monto for pay in a.pagos]) for a in p.atenciones])
        balance = total_pagado - total_consumido
        
        status = "AL_DIA"
        if balance < -0.01:
            status = "DEUDA"
        elif balance > 0.01:
            status = "FAVOR"
            
        results_data.append({
            "id": p.id,
            "nombres": p.nombres,
            "apellidos": p.apellidos,
            "numero_identificacion": p.numero_identificacion,
            "historia_clinica": p.historia_clinica,
            "telefono": p.telefono,
            "email": p.email,
            "fecha_creacion": p.fecha_creacion,
            "total_pagado": total_pagado,
            "balance": balance,
            "estado_financiero": status,
            "saldo_favor": p.saldo_favor
        })
        
    return results_data

@app.get("/api/doctores")
def list_doctores(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """List active doctors, filtered by the user's sucursal if they are not an admin."""
    query = select(Doctor).where(Doctor.activo == True)
    if user.role != "admin" and user.sucursal_id:
        query = query.where(Doctor.sucursal_id == user.sucursal_id)
    return session.exec(query).all()

@app.get("/api/tratamientos")
def list_tratamientos(session: Session = Depends(get_session)):
    return session.exec(select(Tratamiento).where(Tratamiento.activo == True)).all()

@app.post("/api/atenciones")
def create_atencion(paciente_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Create new attention for patient, linked to creator's branch
    # If creator is a Doctor, link it to them immediately
    doc_id = user.doctor_id if user.role == "doctor" else None
    
    atencion = Atencion(
        paciente_id=paciente_id, 
        sucursal_id=user.sucursal_id,
        doctor_id=doc_id
    )
    session.add(atencion)
    session.commit()
    session.refresh(atencion)
    session.refresh(atencion)
    return atencion

@app.post("/api/atenciones/{atencion_id}/terminar")
def terminar_atencion_clinica(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Doctor finishes clinical part. Status -> REALIZADO.
    Does NOT deduct stock yet (Reconciliation does that).
    Does NOT process payments.
    """
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    
    if atencion.validado:
        raise HTTPException(status_code=400, detail="Atención ya validada")

    atencion.estado = "REALIZADO"
    session.add(atencion)
    session.commit()
    return {"status": "ok", "estado": "REALIZADO"}

@app.get("/api/doctores")
def get_doctores(session: Session = Depends(get_session)):
    return session.exec(select(Doctor).where(Doctor.activo == True)).all()

# ... (omitted get_dashboard_atenciones, get_atencion_detail, add_detalle, delete_detalle, update_detalle, sync_pagos, delete_atencion) ...

@app.post("/api/atenciones/{atencion_id}/validar")
def validar_atencion(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Eager load relationships for inventory and payment logic
    atencion = session.exec(
        select(Atencion)
        .where(Atencion.id == atencion_id)
        .options(
            selectinload(Atencion.detalles).selectinload(AtencionDetalle.tratamiento).selectinload(Tratamiento.insumos_requeridos).selectinload(Receta.insumo),
            selectinload(Atencion.paciente),
            selectinload(Atencion.pagos) # REQUIRED for Wallet deduction
        )
    ).first()
    
    if atencion:
        if atencion.validado:
             return {"message": "Ya estaba validado"}
             
        atencion.validado = True
        atencion.estado = "FINALIZADO"
        
        # --- INVENTORY DEDUCTION (Multi-Clinic) ---
        # Prefer atencion.sucursal_id (where it was created), fallback to validator's sucursal
        sucursal_target = atencion.sucursal_id if atencion.sucursal_id else user.sucursal_id
        process_stock_deduction(atencion, session, sucursal_target)

        session.add(atencion)
        session.commit()
    return {"message": "Validado con éxito"}

@app.post("/api/atenciones/{atencion_id}/solicitar-revision")
def solicitar_revision_atencion(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Doctor marks attention as needing review from receptionist.
    Status -> POR_REVISAR.
    """
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    
    if atencion.validado:
        raise HTTPException(status_code=400, detail="Atención ya validada")

    atencion.estado = "POR_REVISAR"
    
    # Audit trail
    log = AuditoriaAtencion(
        atencion_id=atencion.id,
        usuario_id=user.id,
        accion="SOLICITAR_REVISION",
        detalles="El doctor solicitó revisión a recepción"
    )
    session.add(log)
    
    session.add(atencion)
    session.commit()
    return {"status": "ok", "estado": "POR_REVISAR"}

@app.post("/api/atenciones/{atencion_id}/terminar")
def terminar_atencion_clinica(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Doctor finishes clinical part. Status -> REALIZADO.
    Does NOT deduct stock yet (Reconciliation does that).
    Does NOT process payments.
    """
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    
    if atencion.validado:
        raise HTTPException(status_code=400, detail="Atención ya validada")

    atencion.estado = "REALIZADO"
    session.add(atencion)
    session.commit()
    return {"status": "ok", "estado": "REALIZADO"}

@app.post("/api/atenciones/{atencion_id}/solicitar-revision")
def solicitar_revision_atencion(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    
    if atencion.validado:
        raise HTTPException(status_code=400, detail="La atención ya ha sido validada")

    atencion.estado = "POR_REVISAR"
    
    # Optional: Log to Auditoria
    auditoria = AuditoriaAtencion(
        atencion_id=atencion.id,
        usuario_id=user.id,
        accion="SOLICITUD_REVISION",
        detalles=f"Doctor {user.username} solicitó revisión para la atención #{atencion_id}"
    )
    session.add(auditoria)
    session.add(atencion)
    session.commit()
    return {"message": "Solicitud de revisión enviada", "estado": atencion.estado}

@app.get("/api/doctores")
def get_doctores(session: Session = Depends(get_session)):
    return session.exec(select(Doctor).where(Doctor.activo == True)).all()

@app.get("/api/atenciones/global")
def get_global_atenciones(
    search: str = None, 
    status: str = "all", 
    start_date: str = None,
    end_date: str = None,
    page: int = 1,
    size: int = 50,
    session: Session = Depends(get_session), 
    user: User = Depends(get_current_user)
):
    """
    Returns all attentions with search, payment status, and date range filtering.
    For Pagos Management (Secretary).
    """
    try:
        skip = (page - 1) * size
        query = select(Atencion).order_by(Atencion.fecha.desc()).options(
            selectinload(Atencion.paciente),
            selectinload(Atencion.detalles).selectinload(AtencionDetalle.tratamiento),
            selectinload(Atencion.pagos)
        )
        
        # Apply Date Filters at DB level for efficiency
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.where(Atencion.fecha >= start_dt)
            except ValueError:
                pass # Or raise error
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.where(Atencion.fecha < end_dt)
            except ValueError:
                pass
        
        # Executes query first to handle complex filtering/aggregation in Python
        # (Safer for calculated totals)
        # Apply pagination after potentially joining (if needed) but here it's simple results
        atenciones = session.exec(query.offset(skip).limit(size)).all()
        
        results = []
        for a in atenciones:
            total_atencion = sum([d.total_calculado for d in a.detalles])
            total_pagado = sum([p.monto for p in a.pagos])
            saldo_pendiente = total_atencion - total_pagado
            
            # Simple Search Filter
            if search:
                s = search.lower()
                full_name = (a.paciente.nombres + " " + a.paciente.apellidos).lower()
                if s not in full_name and s not in (a.paciente.numero_identificacion or ""):
                    continue
            
            # Status Filter
            # status: 'all', 'pending' (saldo > 0), 'paid' (saldo <= 0)
            if status == "pending" and saldo_pendiente <= 0.01:
                continue
            if status == "paid" and saldo_pendiente > 0.01:
                continue
                
            results.append({
                "id": a.id,
                "fecha": a.fecha,
                "paciente_nombre": f"{a.paciente.nombres} {a.paciente.apellidos}",
                "paciente_id": a.paciente.numero_identificacion,
                "total_atencion": total_atencion,
                "total_pagado": total_pagado,
                "saldo_pendiente": saldo_pendiente,
                "validado": a.validado,
                "estado": a.estado
            })
            
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/atenciones/dashboard")
def get_dashboard_atenciones(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time()) # Midnight today
        
        # 1. Lazy Auto-Validation: Validate everything strictly before today
        # Using SQLModel select/exec/commit pattern
        past_unvalidated = session.exec(select(Atencion).where(Atencion.fecha < today_start).where(Atencion.validado == False)).all()
        for att in past_unvalidated:
            att.validado = True
            att.estado = "FINALIZADO"
            
            # --- INVENTORY DEDUCTION (Auto) ---
            # Use attention's sucursal or fallback to current user's (who acts as trigger)
            target_sucursal = att.sucursal_id if att.sucursal_id else user.sucursal_id
            process_stock_deduction(att, session, target_sucursal)
            
            session.add(att)
        if past_unvalidated:
            session.commit()
        
        # 2. Filter Dashboard: Only return attentions from today onwards AND current branch
        query = (
            select(Atencion)
            .where(Atencion.fecha >= today_start)
            .where(Atencion.sucursal_id == user.sucursal_id) # REQUIRED for Multi-Clinic separation
            .order_by(Atencion.fecha.desc())
            .options(
                selectinload(Atencion.detalles).selectinload(AtencionDetalle.tratamiento),
                selectinload(Atencion.detalles).selectinload(AtencionDetalle.doctor),
                selectinload(Atencion.paciente),
                selectinload(Atencion.pagos)
            )
        )
        
        if user.role == "doctor" and user.doctor_id:
            # Filter by MAIN doctor OR if they have any treatment in the details
            query = query.join(Atencion.detalles, isouter=True).where(
                (Atencion.doctor_id == user.doctor_id) | 
                (AtencionDetalle.doctor_id == user.doctor_id)
            ).distinct()
            
        atenciones = session.exec(query).all()
        
        results = []
        for a in atenciones:
            # Aggregate treatments and doctors for the summary row
            tratamientos_names = [d.tratamiento.nombre for d in a.detalles if d.tratamiento]
            doctors_names = list(set([d.doctor.nombres + " " + d.doctor.apellidos for d in a.detalles if d.doctor]))
            
            # Calculate commission percentages
            comisiones = []
            for d in a.detalles:
                if d.porcentaje_comision > 0:
                    comisiones.append(f"{d.porcentaje_comision:.0f}%")
            
            # Calculate payment breakdown
            pagos_map = {"EF": 0, "TR": 0, "TC": 0, "AB": 0}
            for p in a.pagos:
                if p.forma_pago in pagos_map:
                    pagos_map[p.forma_pago] += p.monto

            # Calculate Global Financial Status for the Patient
            try:
                p = a.paciente
                total_consumido = sum([sum([d.total_calculado for d in at.detalles]) for at in p.atenciones])
                total_pagado_global = sum([sum([pay.monto for pay in at.pagos]) for at in p.atenciones])
                patient_balance = total_pagado_global - total_consumido
                
                patient_status = "AL_DIA"
                if patient_balance < -0.01:
                    patient_status = "DEUDA"
                elif patient_balance > 0.01:
                    patient_status = "FAVOR"
            except Exception as e_inner:
                print(f"Error calculating balance for atencion {a.id}: {e_inner}")
                patient_balance = 0
                patient_status = "ERROR"
            
            results.append({
                "id": a.id,
                "fecha": a.fecha, # datetime
                "hora": a.fecha.strftime("%H:%M"),
                "fecha_dia": a.fecha.strftime("%d de %B de %Y"), # Grouping key
                "paciente": {
                    "nombres": a.paciente.nombres,
                    "apellidos": a.paciente.apellidos,
                    "historia_clinica": a.paciente.historia_clinica
                },
                "resumen_tratamientos": ", ".join(tratamientos_names) if tratamientos_names else "-",
                "resumen_doctores": ", ".join(doctors_names) if doctors_names else "-",
                "resumen_comisiones": ", ".join(comisiones) if comisiones else "-",
                # Note: Continue mapping
                "total": a.total_atencion_valor,
                "pagos": pagos_map,
                "pagado": sum(pagos_map.values()),
                "saldo_pendiente": a.total_atencion_valor - sum(pagos_map.values()), # Re-calc locally
                "validado": a.validado,
                "estado": a.estado,
                "patient_balance": patient_balance,
                "patient_financial_status": patient_status
            })
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/api/atenciones/historial")
def get_historial_atenciones(
    q: Optional[str] = None, 
    page: int = 1,
    size: int = 50,
    session: Session = Depends(get_session), 
    user: User = Depends(get_current_user)
):
    try:
        skip = (page - 1) * size
        query = (
            select(Atencion)
            .where(Atencion.sucursal_id == user.sucursal_id)
            .options(
                selectinload(Atencion.detalles).selectinload(AtencionDetalle.tratamiento),
                selectinload(Atencion.detalles).selectinload(AtencionDetalle.doctor),
                selectinload(Atencion.paciente),
                selectinload(Atencion.pagos)
            )
        )
        
        # 1. Filter by Doctor if applicable
        if user.role == "doctor" and user.doctor_id:
            query = query.join(Atencion.detalles, isouter=True).where(
                (Atencion.doctor_id == user.doctor_id) | 
                (AtencionDetalle.doctor_id == user.doctor_id)
            ).distinct()
            
        # 2. Search by Patient Name
        if q:
            query = query.join(Atencion.paciente).where(
                (Paciente.nombres.contains(q)) | (Paciente.apellidos.contains(q))
            )
            
        # 3. Execution (With Pagination)
        atenciones = session.exec(query.order_by(Atencion.fecha.desc()).offset(skip).limit(size)).all()
        
        results = []
        for a in atenciones:
            tratamientos_names = [d.tratamiento.nombre for d in a.detalles if d.tratamiento]
            doctors_names = list(set([d.doctor.nombres + " " + d.doctor.apellidos for d in a.detalles if d.doctor]))
            
            comisiones = []
            for d in a.detalles:
                if d.porcentaje_comision > 0:
                    comisiones.append(f"{d.porcentaje_comision:.0f}%")
            
            pagos_map = {"EF": 0, "TR": 0, "TC": 0, "AB": 0}
            for p in a.pagos:
                if p.forma_pago in pagos_map:
                    pagos_map[p.forma_pago] += p.monto

            # Patient status
            patient_balance = 0.0
            patient_status = "AL_DIA"
            if a.paciente:
                # Use saldo_favor as the base for the patient's balance status
                patient_balance = float(a.paciente.saldo_favor)
                if patient_balance < -0.01:
                    patient_status = "DEUDA"
                elif patient_balance > 0.01:
                    patient_status = "FAVOR"
            
            results.append({
                "id": a.id,
                "fecha": a.fecha,
                "hora": a.fecha.strftime("%H:%M"),
                "fecha_dia": a.fecha.strftime("%d de %B de %Y"),
                "paciente": {
                    "nombres": a.paciente.nombres if a.paciente else "N/A",
                    "apellidos": a.paciente.apellidos if a.paciente else "",
                    "historia_clinica": a.paciente.historia_clinica if a.paciente else ""
                },
                "resumen_tratamientos": ", ".join(tratamientos_names) if tratamientos_names else "-",
                "resumen_doctores": ", ".join(doctors_names) if doctors_names else "-",
                "resumen_comisiones": ", ".join(comisiones) if comisiones else "-",
                "total": float(a.total_atencion_valor),
                "pagos": pagos_map,
                "pagado": sum(pagos_map.values()),
                "saldo_pendiente": float(a.total_atencion_valor - sum(pagos_map.values())),
                "validado": a.validado,
                "estado": a.estado,
                "patient_balance": patient_balance,
                "patient_financial_status": patient_status
            })
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/atenciones/{atencion_id}")
def get_atencion_detail(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Use eager loading to avoid lazy-load issues in serialization
    atencion = session.exec(
        select(Atencion)
        .where(Atencion.id == atencion_id)
        .options(
            selectinload(Atencion.paciente),
            selectinload(Atencion.pagos),
            selectinload(Atencion.detalles).selectinload(AtencionDetalle.tratamiento),
            selectinload(Atencion.detalles).selectinload(AtencionDetalle.doctor)
        )
    ).first()

    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    
    # Calculate Global Financial Status for the Patient
    p = atencion.paciente
    total_consumido_global = sum([sum([d.total_calculado for d in at.detalles]) for at in p.atenciones])
    total_pagado_global = sum([sum([pay.monto for pay in at.pagos]) for at in p.atenciones])
    patient_balance = total_pagado_global - total_consumido_global
    
    patient_status = "AL_DIA"
    if patient_balance < -0.01:
        patient_status = "DEUDA"
    elif patient_balance > 0.01:
        patient_status = "FAVOR"

    # Custom serialization ensuring clean data and unified property names
    return {
        "id": atencion.id,
        "fecha": atencion.fecha,
        "estado": atencion.estado,
        "validado": atencion.validado,
        "observaciones": atencion.observaciones,
        # Unified total names for FE consistency
        "total_atencion": atencion.total_atencion_valor,
        "total_pagado": atencion.total_pagado,
        "saldo_pendiente": atencion.saldo_pendiente,
        "paciente": {
            "id": atencion.paciente.id,
            "nombres": atencion.paciente.nombres,
            "apellidos": atencion.paciente.apellidos,
            "numero_identificacion": atencion.paciente.numero_identificacion,
            "historia_clinica": atencion.paciente.historia_clinica,
            "balance": patient_balance,
            "saldo_favor": atencion.paciente.saldo_favor,
            "financial_status": patient_status
        },
        "detalles": [
            {
                "id": d.id,
                "tratamiento_id": d.tratamiento_id,
                "doctor_id": d.doctor_id,
                "tratamiento_nombre": d.tratamiento.nombre if d.tratamiento else "Desconocido", 
                "get_doctor": f"{d.doctor.nombres} {d.doctor.apellidos}" if d.doctor else "Sin Doctor",
                "doctor_nombre": f"{d.doctor.nombres} {d.doctor.apellidos}" if d.doctor else "Sin Doctor",
                "nombre_tratamiento": d.tratamiento.nombre if d.tratamiento else "Desconocido", 
                "precio_unitario": d.precio_unitario,
                "cantidad": d.cantidad,
                "porcentaje_comision": d.porcentaje_comision,
                "total": d.total_calculado
            } for d in atencion.detalles
        ],
        "pagos": [
            {
                "id": p.id,
                "fecha": p.fecha,
                "forma_pago": p.forma_pago,
                "monto": p.monto
            } for p in atencion.pagos
        ],
        "totales": {
            "total_atencion": atencion.total_atencion_valor,
            "total_pagado": atencion.total_pagado,
            "saldo_pendiente": atencion.saldo_pendiente
        }
    }

@app.post("/api/atenciones/{atencion_id}/detalles")
def add_detalle(
    atencion_id: int, 
    tratamiento_id: int, 
    precio: float, 
    doctor_id: Optional[int] = None, 
    vendedor_id: Optional[int] = None, 
    comision: float = 0, 
    session: Session = Depends(get_session), 
    user: User = Depends(get_current_user)
):
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    if atencion.validado:
        raise HTTPException(status_code=400, detail="No se puede modificar una atención validada")
        
    detalle = AtencionDetalle(
        atencion_id=atencion_id,
        tratamiento_id=tratamiento_id,
        precio_unitario=precio,
        cantidad=1,
        porcentaje_comision=comision,
        doctor_id=doctor_id,
        vendedor_id=vendedor_id
    )
    session.add(detalle)
    
    # LOG
    t_nombre = session.get(Tratamiento, tratamiento_id).nombre
    registrar_log(atencion_id, "Tratamiento Añadido", f"Se agregó '{t_nombre}' por ${precio}", session, user)
    
    session.commit()
    return {"message": "Detalle agregado"}

@app.delete("/api/detalles/{detalle_id}")
def delete_detalle(detalle_id: int, session: Session = Depends(get_session)):
    detalle = session.get(AtencionDetalle, detalle_id)
    if detalle:
        atencion = session.get(Atencion, detalle.atencion_id)
        if atencion and atencion.validado:
            raise HTTPException(status_code=400, detail="No se puede modificar una atención validada")
            
        # LOG
        registrar_log(detalle.atencion_id, "Tratamiento Eliminado", f"Se eliminó '{detalle.tratamiento.nombre}'", session)
            
        session.delete(detalle)
        session.commit()
    return {"message": "Detalle eliminado"}

from pydantic import BaseModel

class UpdateDetail(BaseModel):
    tratamiento_id: int
    doctor_id: Optional[int] = None
    vendedor_id: Optional[int] = None
    precio: float
    comision: float

@app.put("/api/detalles/{detalle_id}")

def update_detalle(detalle_id: int, data: UpdateDetail, session: Session = Depends(get_session)):
    detalle = session.get(AtencionDetalle, detalle_id)
    if not detalle:
        raise HTTPException(status_code=404, detail="Detalle no encontrado")
        
    atencion = session.get(Atencion, detalle.atencion_id)
    if atencion and atencion.validado:
        raise HTTPException(status_code=400, detail="No se puede modificar una atención validada")

    detalle.tratamiento_id = data.tratamiento_id
    detalle.doctor_id = data.doctor_id
    
    # If the user sets a doctor, wipe the vendedor_id.
    # Otherwise, preserve the existing vendedor_id or assign it to the updater if it's a new 'reception sale' assignment.
    if data.doctor_id:
         detalle.vendedor_id = None
    elif data.vendedor_id is not None:
         detalle.vendedor_id = data.vendedor_id
    elif detalle.vendedor_id is None and not data.doctor_id:
         # If they explicitly chose 'recepcion' (doctor_id is None) and it had NO vendedor before, give it to them
         user = session.exec(select(User).where(User.username == "admin")).first() # Can't get current user easily here without dependency, but let's just leave it as is if they just updated price.
         
    detalle.precio_unitario = data.precio
    detalle.porcentaje_comision = data.comision

    
    session.add(detalle)
    session.commit()
    return {"message": "Detalle actualizado"}

class UpdateAtencion(BaseModel):
    observaciones: str | None = None

@app.put("/api/atenciones/{atencion_id}")
def update_atencion(atencion_id: int, data: UpdateAtencion, session: Session = Depends(get_session)):
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
        
    if atencion.validado:
        raise HTTPException(status_code=400, detail="No se puede modificar una atención validada")

    if data.observaciones is not None:
        atencion.observaciones = data.observaciones
        registrar_log(atencion_id, "Notas Actualizadas", "Se actualizaron las notas clínicas/evolución", session)
    
    session.add(atencion)
    session.commit()
    return {"message": "Atención actualizada"}

from pydantic import BaseModel
class PaymentSync(BaseModel):
    efectivo: float
    transferencia: float
    tarjeta: float
    abono: float
    metodo_excedente: Optional[str] = None

@app.post("/api/atenciones/{atencion_id}/pagos/sync")
def sync_pagos(atencion_id: int, data: PaymentSync, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    if atencion.validado:
        raise HTTPException(status_code=400, detail="No se puede modificar una atención validada")

    # --- WALLET ADJUSTMENT (Inmediata) ---
    # Calculamos la diferencia entre el abono anterior y el nuevo
    old_abono = Decimal(sum([p.monto for p in atencion.pagos if p.forma_pago == "AB"]))
    # Usar str() para evitar problemas de precisión de float a Decimal
    new_abono = Decimal(str(data.abono)) 
    diff = new_abono - old_abono

    if diff != 0:
        if diff > 0 and atencion.paciente.saldo_favor < diff:
             raise HTTPException(status_code=400, detail=f"Saldo insuficiente en billetera. Disponible: ${atencion.paciente.saldo_favor}, Requerido adicional: ${diff}")
        
        atencion.paciente.saldo_favor -= diff
        session.add(atencion.paciente)
        registrar_log(atencion_id, "Billetera Ajustada", f"Uso de billetera cambiado de ${old_abono} a ${new_abono}", session, user)

    # --- OVERPAYMENT LOGIC (Automatic Recharge) ---
    new_efectivo = Decimal(str(data.efectivo))
    new_transferencia = Decimal(str(data.transferencia))
    new_tarjeta = Decimal(str(data.tarjeta))
    
    total_received = new_efectivo + new_transferencia + new_tarjeta + new_abono
    total_due = atencion.total_atencion_valor

    if total_received > total_due:
        surplus = total_received - total_due
        
        # 1. Credit surplus to Wallet
        atencion.paciente.saldo_favor += surplus
        session.add(atencion.paciente)

        # NEW: Create explicit HistorialAbono record with user-provided method
        metodo_final = data.metodo_excedente if data.metodo_excedente else "Desconocido"

        historial = HistorialAbono(
            paciente_id=atencion.paciente.id,
            usuario_id=user.id if user else None,
            monto=surplus,
            metodo_pago=metodo_final,
            fecha=datetime.now()
        )
        session.add(historial)

        registrar_log(atencion_id, "Recarga Automática", f"Sobrepago de ${surplus} acreditado a Billetera", session, user)

        # 2. Adjust payments to not exceed total_due for accounting purposes
        remaining_reduction = surplus
        
        # Helper to safely reduce a money metric and the remaining reduction
        def reduce_amount(current_amount, target_reduction):
             deduct = min(current_amount, target_reduction)
             return current_amount - deduct, target_reduction - deduct

        # Prioritize deducting from the method the user explicitly declared as the surplus source
        if metodo_final == "Efectivo" and remaining_reduction > 0 and new_efectivo > 0:
             new_efectivo, remaining_reduction = reduce_amount(new_efectivo, remaining_reduction)
             
        if metodo_final == "Transferencia" and remaining_reduction > 0 and new_transferencia > 0:
             new_transferencia, remaining_reduction = reduce_amount(new_transferencia, remaining_reduction)
             
        if metodo_final == "Tarjeta" and remaining_reduction > 0 and new_tarjeta > 0:
             new_tarjeta, remaining_reduction = reduce_amount(new_tarjeta, remaining_reduction)
             
        # If there is STILL remaining reduction (e.g. they typed TR: 10, EF: 120 and chose TR as source),
        # fallback to waterfall reduction to guarantee exact total_due matches.
        if remaining_reduction > 0 and new_efectivo > 0:
             new_efectivo, remaining_reduction = reduce_amount(new_efectivo, remaining_reduction)
             
        if remaining_reduction > 0 and new_transferencia > 0:
             new_transferencia, remaining_reduction = reduce_amount(new_transferencia, remaining_reduction)
             
        if remaining_reduction > 0 and new_tarjeta > 0:
             new_tarjeta, remaining_reduction = reduce_amount(new_tarjeta, remaining_reduction)

    # Informative log about final payments (adjusted)
    registrar_log(atencion_id, "Pagos Sincronizados", f"Finales - Ef: ${new_efectivo}, Tr: ${new_transferencia}, Tc: ${new_tarjeta}", session, user)

    # Wipe existing payments
    for p in atencion.pagos:
        session.delete(p)
    
    # Add new payments (using adjusted values)
    if new_efectivo > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="EF", monto=new_efectivo))
    if new_transferencia > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="TR", monto=new_transferencia))
    if new_tarjeta > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="TC", monto=new_tarjeta))
    if new_abono > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="AB", monto=new_abono))
        
    session.commit()
    return {"message": "Pagos actualizados"}

@app.put("/api/atenciones/{atencion_id}/pagos")
def update_atencion_pagos(atencion_id: int, data: dict, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Specifically for Secretary to adjust payments after attention is finished.
    Expects data: {"efectivo": X, "transferencia": Y, "tarjeta": Z, "abono": W}
    """
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    
    # Validation: Only secretary/admin can use this specific post-closure edit
    if user.role not in ["admin", "recepcion"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para editar pagos")

    # --- WALLET ADJUSTMENT (Inmediata) ---
    old_abono = sum([p.monto for p in atencion.pagos if p.forma_pago == "AB"])
    new_abono = Decimal(data.get("abono", 0))
    diff = new_abono - Decimal(old_abono)

    if diff != 0:
        if diff > 0 and atencion.paciente.saldo_favor < diff:
             raise HTTPException(status_code=400, detail=f"Saldo insuficiente en billetera.")
        
        atencion.paciente.saldo_favor -= diff
        session.add(atencion.paciente)
        registrar_log(atencion_id, "Billetera Ajustada (Manual)", f"Abono cambiado de ${old_abono} a ${new_abono}", session, user)

    # --- OVERPAYMENT LOGIC (Automatic Recharge) ---
    new_efectivo = Decimal(data.get("efectivo", 0))
    new_transferencia = Decimal(data.get("transferencia", 0))
    new_tarjeta = Decimal(data.get("tarjeta", 0))
    
    total_received = new_efectivo + new_transferencia + new_tarjeta + new_abono
    total_due = atencion.total_atencion_valor

    if total_received > total_due:
        surplus = total_received - total_due
        
        # 1. Credit surplus to Wallet
        atencion.paciente.saldo_favor += surplus
        session.add(atencion.paciente)
        registrar_log(atencion_id, "Recarga Automática", f"Sobrepago de ${surplus} acreditado a Billetera", session, user)

        # 2. Adjust payments to not exceed total_due for accounting purposes
        # Strategy: Reduce from Cash first, then Transfer, then Card
        remaining_reduction = surplus
        
        if remaining_reduction > 0 and new_efectivo > 0:
            deduct = min(new_efectivo, remaining_reduction)
            new_efectivo -= deduct
            remaining_reduction -= deduct
            
        if remaining_reduction > 0 and new_transferencia > 0:
            deduct = min(new_transferencia, remaining_reduction)
            new_transferencia -= deduct
            remaining_reduction -= deduct
            
        if remaining_reduction > 0 and new_tarjeta > 0:
            deduct = min(new_tarjeta, remaining_reduction)
            new_tarjeta -= deduct
            remaining_reduction -= deduct

    # Informative log
    registrar_log(atencion_id, "Pagos Editados (Manual)", f"Nuevos montos - Ef: {new_efectivo}, Tr: {new_transferencia}, Tc: {new_tarjeta}", session, user)

    # Wipe old payments for this attention
    for p in atencion.pagos:
        session.delete(p)
    session.flush() # Ensure deletions are processed before adding new ones
    
    # Add new payments (use adjusted values)
    if new_efectivo > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="EF", monto=new_efectivo))
    if new_transferencia > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="TR", monto=new_transferencia))
    if new_tarjeta > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="TC", monto=new_tarjeta))
    if new_abono > 0:
        session.add(Pago(atencion_id=atencion_id, forma_pago="AB", monto=new_abono))
        
    session.commit()
    return {"message": "Pagos actualizados correctamente"}


@app.post("/api/atenciones/{atencion_id}/pagos/add")
def add_atencion_pago(atencion_id: int, data: dict, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Transactional Add Payment.
    Expects data: {"forma_pago": "EF"|"TR"|"TC"|"AB", "monto": 10.00}
    """
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    
    if user.role not in ["admin", "recepcion"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para agregar pagos")

    forma_pago = data.get("forma_pago")
    if forma_pago not in ["EF", "TR", "TC", "AB"]:
        raise HTTPException(status_code=400, detail="Forma de pago inválida")

    try:
        monto = Decimal(data.get("monto", 0))
    except:
         raise HTTPException(status_code=400, detail="Monto inválido")
         
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")

    # --- ABONO LOGIC (Wallet Deduction) ---
    if forma_pago == "AB":
        if atencion.paciente.saldo_favor < monto:
             raise HTTPException(status_code=400, detail=f"Saldo insuficiente en billetera (${atencion.paciente.saldo_favor})")
        
        # Deduct from wallet immediately
        atencion.paciente.saldo_favor -= monto
        session.add(atencion.paciente)
        registrar_log(atencion_id, "Pago con Billetera", f"Se descontaron ${monto} de la billetera", session, user)

    # --- REGULAR PAYMENTS & SURPLUS LOGIC ---
    else:
        # Check for overpayment against the TOTAL DUE vs (TOTAL PAID + CURRENT AMT)
        total_due = atencion.total_atencion_valor
        total_paid = atencion.total_pagado # Logic in model sums existing payments
        
        if total_paid + monto > total_due:
            surplus = (total_paid + monto) - total_due
            
            # If the surplus is the ENTIRE amount (already paid in full), credit all to wallet
            # If partial, credit only the excess
            
            credit_to_wallet = surplus
            payment_record = monto - surplus # This ensures the attention balances exactly to 0 pending
            
            if credit_to_wallet > 0:
                atencion.paciente.saldo_favor += credit_to_wallet
                session.add(atencion.paciente)

                # NEW: Record the overpayment as a proper Wallet Recharge in HistorialAbono
                metodo_excedente = data.get("metodo_excedente", forma_pago)
                
                historial = HistorialAbono(
                    paciente_id=atencion.paciente.id,
                    usuario_id=user.id if user else None,
                    monto=Decimal(credit_to_wallet),
                    metodo_pago=metodo_excedente,
                    fecha=datetime.now()
                )
                session.add(historial)

                registrar_log(atencion_id, "Sobrepago a Billetera", f"Excedente de ${credit_to_wallet} acreditado a billetera", session, user)
            
            # If there is a remaining valid payment part, update 'monto' to that
            # BUT: Transactions normally record the actual event. 
            # If I hand you $100 bill for a $50 debt. You record "Paid $50, changed $50".
            # The system wants to record payments attached to the attention. 
            # If we record $100 payment, the balance becomes -$50.
            # To strictly balance the attention, we record $50 payment. 
            
            monto = payment_record 
            
            if monto <= 0 and credit_to_wallet > 0:
                 # Fully covered by overpayment logic (e.g. debt was 0)
                 # We just return success as we moved money to wallet
                 session.commit()
                 return {"message": "Monto acreditado totalmente a billetera"}

    # Record the payment
    if monto > 0:
        pago = Pago(atencion_id=atencion_id, forma_pago=forma_pago, monto=monto)
        session.add(pago)
        registrar_log(atencion_id, "Pago Agregado", f"Pago de ${monto} vía {forma_pago}", session, user)
    
    session.commit()
    return {"message": "Pago registrado correctamente", "pagos": atencion.pagos}

@app.delete("/api/atenciones/{atencion_id}")
def delete_atencion(atencion_id: int, session: Session = Depends(get_session)):
    atencion = session.get(Atencion, atencion_id)
    if not atencion:
        raise HTTPException(status_code=404, detail="Atención no encontrada")
    if atencion.validado:
        raise HTTPException(status_code=400, detail="No se puede eliminar una atención validada")
    
    # Devolvemos el monto de billetera al saldo del paciente
    total_abono = sum([p.monto for p in atencion.pagos if p.forma_pago == "AB"])
    if total_abono > 0:
        atencion.paciente.saldo_favor += total_abono
        registrar_log(atencion_id, "Reembolso Billetera", f"Atención eliminada. Se devolvieron ${total_abono} a la billetera.", session)

    session.delete(atencion)
    session.commit()
    return {"message": "Atención eliminada"}

@app.get("/api/pagos/bonos")
def get_bonos_report(
    start_date: str = None, 
    end_date: str = None, 
    search: str = None, 
    page: int = 1,
    size: int = 50,
    session: Session = Depends(get_session), 
    user: User = Depends(get_current_user)
):
    # Basic security check
    if user.role not in ["admin", "recepcion"]:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver reportes de pagos")

    skip = (page - 1) * size
    query = (
        select(HistorialAbono)
        .join(Paciente) # Ensure connection to Paciente
    )

    if search:
        search_val = f"%{search}%"
        query = query.where(
            (Paciente.nombres.ilike(search_val)) | 
            (Paciente.apellidos.ilike(search_val)) | 
            (Paciente.numero_identificacion.ilike(search_val))
        )

    query = query.order_by(HistorialAbono.fecha.desc()).offset(skip).limit(size)

    # Date filters (optional)
    if start_date:
        query = query.where(HistorialAbono.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        # End date inclusive
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.where(HistorialAbono.fecha < end_dt)

    bonos = session.exec(query).all()
    
    results = []
    for b in bonos:
        results.append({
            "id": b.id,
            "fecha": b.fecha,
            "paciente": f"{b.paciente.nombres} {b.paciente.apellidos}",
            "monto": b.monto,
            "metodo_pago": b.metodo_pago,
            "usuario": b.usuario.username if b.usuario else "Desconocido"
        })
        
    return results


@app.get("/api/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/atenciones/{atencion_id}/validar")
def validar_atencion(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Eager load relationships for inventory logic
    atencion = session.exec(
        select(Atencion)
        .where(Atencion.id == atencion_id)
        .options(
            selectinload(Atencion.detalles).selectinload(AtencionDetalle.tratamiento).selectinload(Tratamiento.insumos_requeridos).selectinload(Receta.insumo)
        )
    ).first()
    
    if atencion:
        if atencion.validado:
             return {"message": "Ya estaba validado"}
             
        atencion.validado = True
        atencion.estado = "FINALIZADO"
        
        # --- INVENTORY DEDUCTION (Manual) ---
        process_stock_deduction(atencion, session)

        # --- WALLET DEDUCTION ---
        # Removido: Ahora el descuento ocurre en tiempo real durante la edición (sync_pagos)

        session.add(atencion)
        session.commit()
    return {"message": "Validado con éxito"}

@app.get("/api/reportes/pacientes-por-tratamiento")
def reporte_pacientes_tratamiento(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Reporte Real: Pacientes Activos en Tratamiento
    results = session.exec(
        select(Tratamiento.nombre, func.count(TratamientoEnCurso.id))
        .join(TratamientoEnCurso, Tratamiento.id == TratamientoEnCurso.tratamiento_id)
        .where(TratamientoEnCurso.activo == True)
        .group_by(Tratamiento.id)
    ).all()
    
    data = [{"nombre": r[0], "total_pacientes": r[1]} for r in results]
    return data

@app.get("/api/reportes/ingresos-mensuales")
def reporte_ingresos_mensuales(start_date: str = None, end_date: str = None, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if user.role not in ["admin", "recepcion"]:
        raise HTTPException(status_code=403, detail="No tiene permisos")
        
    query_pagos = select(Pago)
    if user.sucursal_id:
        query_pagos = query_pagos.join(Atencion).where(Atencion.sucursal_id == user.sucursal_id)
        
    if start_date:
        query_pagos = query_pagos.where(Pago.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query_pagos = query_pagos.where(Pago.fecha < end_dt)
        
    pagos = session.exec(query_pagos).all()

    query_auditoria = select(AuditoriaAtencion).where(AuditoriaAtencion.accion == "RECARGA_BILLETERA")
    if start_date:
        query_auditoria = query_auditoria.where(AuditoriaAtencion.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query_auditoria = query_auditoria.where(AuditoriaAtencion.fecha < end_dt)
        
    recargas_logs = session.exec(query_auditoria).all()

    ingresos_por_mes = {}
    
    for p in pagos:
        mes_key = p.fecha.strftime("%Y-%m")
        if mes_key not in ingresos_por_mes:
            ingresos_por_mes[mes_key] = 0.0
        ingresos_por_mes[mes_key] += float(p.monto)
        
    import re
    for log in recargas_logs:
        mes_key = log.fecha.strftime("%Y-%m")
        match = re.search(r"\$(\d+(\.\d+)?)", log.descripcion)
        if match:
            if mes_key not in ingresos_por_mes:
                ingresos_por_mes[mes_key] = 0.0
            ingresos_por_mes[mes_key] += float(match.group(1))

    ingresos_list = [{"mes": k, "total": round(v, 2)} for k, v in sorted(ingresos_por_mes.items())]

    # Part 2: Produccion por doctor
    query_detalles = select(AtencionDetalle).join(Atencion).where(Atencion.validado == True).where(AtencionDetalle.doctor_id != None)
    if user.sucursal_id:
        query_detalles = query_detalles.where(Atencion.sucursal_id == user.sucursal_id)
        
    if start_date:
        query_detalles = query_detalles.where(Atencion.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query_detalles = query_detalles.where(Atencion.fecha < end_dt)
        
    query_detalles = query_detalles.options(selectinload(AtencionDetalle.doctor), selectinload(AtencionDetalle.tratamiento))
    detalles = session.exec(query_detalles).all()

    doctores_prod = {}
    for d in detalles:
        doc_id = d.doctor_id
        if doc_id not in doctores_prod:
            doctores_prod[doc_id] = {
                "doctor_id": doc_id,
                "nombre": f"{d.doctor.nombres} {d.doctor.apellidos}" if d.doctor else "Desconocido",
                "total_producido": 0.0,
                "tratamientos": {}
            }
        
        val = float(d.total_calculado)
        doctores_prod[doc_id]["total_producido"] += val
        
        t_nombre = d.tratamiento.nombre if d.tratamiento else "Otro"
        if t_nombre not in doctores_prod[doc_id]["tratamientos"]:
             doctores_prod[doc_id]["tratamientos"][t_nombre] = 0.0
        doctores_prod[doc_id]["tratamientos"][t_nombre] += val

    for doc_id, prod in doctores_prod.items():
        trats = []
        for t_k, t_v in prod["tratamientos"].items():
            trats.append({"nombre": t_k, "monto": round(t_v, 2)})
        trats.sort(key=lambda x: x["monto"], reverse=True)
        prod["tratamientos"] = trats
        prod["total_producido"] = round(prod["total_producido"], 2)

    doctores_list = list(doctores_prod.values())
    doctores_list.sort(key=lambda x: x["total_producido"], reverse=True)

    return {
        "ingresos_mensuales": ingresos_list,
        "produccion_doctores": doctores_list
    }

@app.get("/api/reportes/flujo-caja-global")
def reporte_flujo_caja_global(start_date: str = None, end_date: str = None, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Returns total income (excluding 'AB' payments) and total expenses.
    """
    if user.role == "doctor":
        raise HTTPException(status_code=403, detail="No autorizado")

    # 1. Ingresos: Pagos (forma_pago != 'AB')
    query_pagos = select(Pago).where(Pago.sucursal_id == user.sucursal_id).where(Pago.forma_pago != 'AB')
    if start_date:
        query_pagos = query_pagos.where(Pago.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query_pagos = query_pagos.where(Pago.fecha < end_dt)
        
    pagos = session.exec(query_pagos).all()
    total_ingresos = sum(float(p.monto) for p in pagos)
    
    # 2. Egresos: Gastos
    query_gastos = select(Gasto).where(Gasto.sucursal_id == user.sucursal_id)
    if start_date:
        query_gastos = query_gastos.where(Gasto.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query_gastos = query_gastos.where(Gasto.fecha < end_dt)
        
    gastos = session.exec(query_gastos).all()
    total_egresos = sum(float(g.monto) for g in gastos)
    
    saldo_neto = total_ingresos - total_egresos
    
    return {
        "ingresos": total_ingresos,
        "egresos": total_egresos,
        "saldo_neto": saldo_neto
    }

@app.get("/api/reportes/financiero-completo")
def reporte_financiero_completo(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Returns a comprehensive JSON with all attentions, details, and payments
    for Excel export.
    """
    if user.role not in ["admin", "recepcion"]:
        raise HTTPException(status_code=403, detail="No tiene permisos")

    # Load everything needed
    atenciones = session.exec(
        select(Atencion)
        .options(
            selectinload(Atencion.paciente),
            selectinload(Atencion.doctor),
            selectinload(Atencion.sucursal),
            selectinload(Atencion.detalles).selectinload(AtencionDetalle.tratamiento),
            selectinload(Atencion.detalles).selectinload(AtencionDetalle.doctor),
            selectinload(Atencion.pagos)
        )
        .order_by(Atencion.fecha.desc())
    ).all()

    report_results = []
    for at in atenciones:
        report_results.append({
            "id": at.id,
            "fecha": at.fecha.isoformat(),
            "estado": at.estado,
            "paciente": f"{at.paciente.nombres} {at.paciente.apellidos}" if at.paciente else "N/A",
            "paciente_id": at.paciente.numero_identificacion if at.paciente else "N/A",
            "doctor_principal": f"{at.doctor.nombres} {at.doctor.apellidos}" if at.doctor else "N/A",
            "sucursal": at.sucursal.nombre if at.sucursal else "N/A",
            "observaciones": at.observaciones,
            "detalles": [
                {
                    "tratamiento": d.tratamiento.nombre if d.tratamiento else "Desconocido",
                    "doctor_procedimiento": f"{d.doctor.nombres} {d.doctor.apellidos}" if d.doctor else "N/A",
                    "cantidad": d.cantidad,
                    "precio_unitario": float(d.precio_unitario),
                    "total": float(d.total_calculado)
                } for d in at.detalles
            ],
            "pagos": [
                {
                    "fecha": p.fecha.isoformat(),
                    "forma_pago": p.forma_pago,
                    "monto": float(p.monto),
                    "referencia": p.referencia
                } for p in at.pagos
            ]
        })

    return report_results

@app.post("/api/pacientes/{paciente_id}/tratamientos")
def iniciar_tratamiento(paciente_id: int, tratamiento_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    # Check if already active
    existing = session.exec(select(TratamientoEnCurso).where(
        TratamientoEnCurso.paciente_id == paciente_id,
        TratamientoEnCurso.tratamiento_id == tratamiento_id,
        TratamientoEnCurso.activo == True
    )).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="El paciente ya tiene este tratamiento activo")
        
    nuevo = TratamientoEnCurso(
        paciente_id=paciente_id,
        tratamiento_id=tratamiento_id,
        fecha_inicio=datetime.now(),
        activo=True
    )
    session.add(nuevo)
    session.commit()
    return {"message": "Tratamiento iniciado"}

@app.put("/api/pacientes/{paciente_id}/tratamientos/{tratamiento_id}/finalizar")
def finalizar_tratamiento(paciente_id: int, tratamiento_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    registro = session.exec(select(TratamientoEnCurso).where(
        TratamientoEnCurso.paciente_id == paciente_id,
        TratamientoEnCurso.tratamiento_id == tratamiento_id,
        TratamientoEnCurso.activo == True
    )).first()
    
    if not registro:
        raise HTTPException(status_code=404, detail="No hay tratamiento activo para finalizar")
        
    registro.activo = False
    registro.fecha_fin = datetime.now()
    session.add(registro)
    session.commit()
    return {"message": "Tratamiento finalizado"}

@app.get("/api/pacientes/{paciente_id}/tratamientos-activos")
def get_tratamientos_activos(paciente_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    registros = session.exec(select(TratamientoEnCurso).where(
        TratamientoEnCurso.paciente_id == paciente_id,
        TratamientoEnCurso.activo == True
    )).all()
    
    data = []
    for r in registros:
        data.append({
            "id": r.id,
            "tratamiento_id": r.tratamiento_id,
            "nombre": r.tratamiento.nombre if r.tratamiento else "Desconocido",
            "fecha_inicio": r.fecha_inicio
        })
    return data

class RecargaSchema(BaseModel):
    monto: float
    metodo_pago: str = "EFECTIVO" # EFECTIVO, TRANSFERENCIA, TARJETA

@app.post("/api/pacientes/{paciente_id}/recargar")
def recargar_billetera(paciente_id: int, data: RecargaSchema, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    paciente = session.get(Paciente, paciente_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    if data.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")
        
    paciente.saldo_favor += Decimal(data.monto)
    
    # Save the recharge in the specific HistorialAbono table
    historial = HistorialAbono(
        paciente_id=paciente.id,
        usuario_id=user.id if user else None,
        monto=Decimal(data.monto),
        metodo_pago=data.metodo_pago,
        fecha=datetime.now()
    )
    session.add(historial)

    session.add(paciente)
    session.commit()
    return {"message": "Recarga exitosa", "nuevo_saldo": paciente.saldo_favor}

@app.get("/recepcion/imprimir/{atencion_id}", response_class=HTMLResponse)
def view_imprimir_atencion(atencion_id: int):
    with open("static/imprimir.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/recepcion/editar/{atencion_id}", response_class=HTMLResponse)
def view_editar_atencion(atencion_id: int):
    with open("static/editar.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/recepcion", response_class=HTMLResponse)
def view_recepcion():
    with open("static/recepcion.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/")
def read_root():
    return {"message": "Sistema Clínica HD - FastAPI Backend Operativo", "docs": "/docs", "frontend": "/recepcion"}



# --- AUDITORIA HELPERS ---
def registrar_log(atencion_id: int, accion: str, descripcion: str, session: Session, user: User = None):
    log = AuditoriaAtencion(
        atencion_id=atencion_id,
        usuario_id=user.id if user else None,
        accion=accion,
        descripcion=descripcion,
        fecha=datetime.now()
    )
    session.add(log)

@app.get("/api/atenciones/{atencion_id}/historial")
def get_atencion_historial(atencion_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    logs = session.exec(
        select(AuditoriaAtencion)
        .where(AuditoriaAtencion.atencion_id == atencion_id)
        .order_by(AuditoriaAtencion.fecha.desc())
    ).all()
    
    return [
        {
            "id": l.id,
            "fecha": l.fecha,
            "accion": l.accion,
            "descripcion": l.descripcion,
            "usuario": l.usuario.username if l.usuario else "Sistema"
        } for l in logs
    ]

@app.get("/api/reportes/diario-sumario")
def get_daily_summary(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Returns total of direct wallet recharges for today.
    """
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    # Sum recharges from AuditoriaAtencion
    logs = session.exec(
        select(AuditoriaAtencion)
        .where(AuditoriaAtencion.accion == "RECARGA_BILLETERA")
        .where(AuditoriaAtencion.fecha >= today_start)
    ).all()
    
    total_directo = 0
    for l in logs:
        try:
            # Extract amount from description "Recarga directa de $X to..."
            import re
            match = re.search(r"\$(\d+(\.\d+)?)", l.descripcion)
            if match:
                total_directo += float(match.group(1))
        except:
            pass
            
    return {"recargas_directas": total_directo}

# --- GESTIÓN DE GASTOS (Módulo 30) ---

@app.post("/api/gastos")
def create_gasto(
    descripcion: str = Form(...),
    monto: Decimal = Form(...),
    metodo_pago: str = Form(...), # EFECTIVO, TRANSFERENCIA
    categoria: str = Form("GENERAL"),
    responsable: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    if not user.sucursal_id:
        raise HTTPException(status_code=400, detail="El usuario no tiene una sucursal asignada")
    
    gasto = Gasto(
        descripcion=descripcion,
        monto=monto,
        metodo_pago=metodo_pago,
        categoria=categoria,
        responsable=responsable,
        sucursal_id=user.sucursal_id,
        usuario_id=user.id
    )
    session.add(gasto)
    session.commit()
    session.refresh(gasto)
    return gasto

@app.get("/api/gastos")
def list_gastos(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    categoria: Optional[str] = None,
    metodo_pago: Optional[str] = None,
    usuario_id: Optional[int] = None,
    page: int = 1,
    size: int = 50,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user)
):
    skip = (page - 1) * size
    if not user.sucursal_id:
        return []
    
    # Eager load 'usuario' to show who registered the expense
    query = (
        select(Gasto)
        .where(Gasto.sucursal_id == user.sucursal_id)
        .options(selectinload(Gasto.usuario))
        .order_by(Gasto.fecha.desc())
    )
    
    if start_date:
        query = query.where(Gasto.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.where(Gasto.fecha < end_dt)
    
    if search:
        query = query.where(Gasto.descripcion.ilike(f"%{search}%"))
        
    if categoria:
        query = query.where(Gasto.categoria == categoria)
        
    if metodo_pago:
        query = query.where(Gasto.metodo_pago == metodo_pago)
        
    if usuario_id:
        query = query.where(Gasto.usuario_id == usuario_id)
        
    return session.exec(query.offset(skip).limit(size)).all()

@app.get("/api/gastos/balances")
def get_gastos_balances(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Calculates Strict Financial Balances:
    Caja Fija = Pagos(EF) + Recargas(EFECTIVO) - Gastos(EFECTIVO)
    Banco = Pagos(TR) + Recargas(TRANSFERENCIA) - Gastos(TRANSFERENCIA)
    Tarjeta = Pagos(TC) + Recargas(TARJETA)
    Billetera Aplicada = Pagos(AB)
    """
    if not user.sucursal_id:
         return {"efectivo": 0, "transferencia": 0, "tarjeta": 0, "abono_aplicado": 0}
    
    # --- 1. INCOME FROM PAYMENTS (Atenciones) ---
    ingresos_query = session.exec(
        select(Pago.forma_pago, func.sum(Pago.monto))
        .join(Atencion)
        .where(Atencion.sucursal_id == user.sucursal_id)
        .group_by(Pago.forma_pago)
    ).all()
    
    ingresos_crudos = {row[0]: float(row[1]) for row in ingresos_query}
    
    # Map to standard concepts
    ingresos = {
        "EFECTIVO": ingresos_crudos.get("EF", 0),
        "TRANSFERENCIA": ingresos_crudos.get("TR", 0),
        "TARJETA": ingresos_crudos.get("TC", 0),
        "ABONO_APLICADO": ingresos_crudos.get("AB", 0) # Internal movement
    }
    
    # --- 2. INCOME FROM WALLET RECHARGES (Recargas Directas) ---
    recargas_query = session.exec(
        select(HistorialAbono.metodo_pago, func.sum(HistorialAbono.monto))
        .join(User, HistorialAbono.usuario_id == User.id)
        .where(User.sucursal_id == user.sucursal_id)
        .group_by(HistorialAbono.metodo_pago)
    ).all()
    
    recargas = {row[0]: float(row[1]) for row in recargas_query}

    # Add Recharges to gross income
    ingresos["EFECTIVO"] += recargas.get("EFECTIVO", 0)
    ingresos["TRANSFERENCIA"] += recargas.get("TRANSFERENCIA", 0)
    ingresos["TARJETA"] += recargas.get("TARJETA", 0)

    # --- 3. EXPENSES (Gastos) ---
    egresos_query = session.exec(
        select(Gasto.metodo_pago, func.sum(Gasto.monto))
        .where(Gasto.sucursal_id == user.sucursal_id)
        .group_by(Gasto.metodo_pago)
    ).all()
    
    egresos = {row[0]: float(row[1]) for row in egresos_query}
    
    # --- 4. CALCULATE STRICT BALANCES ---
    balance_efectivo = ingresos["EFECTIVO"] - egresos.get("EFECTIVO", 0)
    balance_transferencia = ingresos["TRANSFERENCIA"] - egresos.get("TRANSFERENCIA", 0)
    balance_tarjeta = ingresos["TARJETA"] # No expenses in card currently
    
    return {
        "efectivo": balance_efectivo,
        "transferencia": balance_transferencia,
        "tarjeta": balance_tarjeta,
        "abono_aplicado": ingresos["ABONO_APLICADO"],
        "desglose_ingresos": ingresos,
        "desglose_egresos": egresos,
        "desglose_recargas": recargas
    }

# --- SISTEMA DE NÓMINA Y COMISIONES (Módulo 35) ---

@app.get("/api/nomina/pendientes")
def get_nomina_pendientes(start_date: str = None, end_date: str = None, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """
    Returns pending commissions for Doctors and Secretaries in the current branch.
    """
    if not user.sucursal_id:
        raise HTTPException(status_code=400, detail="El usuario no tiene una sucursal asignada")
    
    # 1. DOCTORS pending commissions
    # A commission is owed if the treatment is finished/validated AND it hasn't been paid to the doctor yet.
    
    doctores_pendientes = {}
    
    # Initialize with all active doctors of the sucursal
    all_docs = session.exec(select(Doctor).where(Doctor.sucursal_id == user.sucursal_id).where(Doctor.activo == True)).all()
    for doc in all_docs:
        doctores_pendientes[doc.id] = {
            "id": doc.id,
            "nombre": f"{doc.nombres} {doc.apellidos}",
            "tipo": "Doctor",
            "comisiones_acumuladas": 0.0,
            "detalles": []
        }
    
    query_docs = (
        select(AtencionDetalle)
        .join(Atencion)
        .where(Atencion.sucursal_id == user.sucursal_id)
        .where(Atencion.validado == True)
        .where(AtencionDetalle.comision_pagada == False)
        .where(AtencionDetalle.doctor_id != None)
        .options(
            selectinload(AtencionDetalle.doctor), 
            selectinload(AtencionDetalle.tratamiento),
            selectinload(AtencionDetalle.atencion).selectinload(Atencion.pagos)
        )
    )
    if start_date:
        query_docs = query_docs.where(Atencion.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query_docs = query_docs.where(Atencion.fecha < end_dt)
        
    detalles_docs = session.exec(query_docs).all()
    
    for d in detalles_docs:
        doc_id = d.doctor_id
        if doc_id in doctores_pendientes:
            atencion = d.atencion
            total_atn = float(atencion.total_atencion) if getattr(atencion, 'total_atencion', 0) else 0.0
            pagado = sum(float(p.monto) for p in atencion.pagos) if getattr(atencion, 'pagos', []) else 0.0
            porcentaje_pagado = min(pagado / total_atn, 1.0) if total_atn > 0 else 1.0
            
            comision_teorica = float(d.comision_valor)
            comision_real_total = comision_teorica * porcentaje_pagado
            comision_ya_pagada = float(d.comision_pagada_monto) if getattr(d, 'comision_pagada_monto', 0.0) else 0.0
            comision_pendiente = comision_real_total - comision_ya_pagada
            
            if comision_pendiente > 0.01:
                doctores_pendientes[doc_id]["comisiones_acumuladas"] += comision_pendiente
                doctores_pendientes[doc_id]["detalles"].append({
                    "tratamiento": d.tratamiento.nombre if d.tratamiento else "Desconocido",
                    "valor_tratamiento": float(d.total_calculado),
                    "porcentaje": float(d.porcentaje_comision),
                    "comision": round(comision_pendiente, 2),
                    "fecha": d.atencion.fecha.isoformat()
                })
        
    # 2. SECRETARIES / USERS pending commissions (Kit Sales)
    vendedores_pendientes = {}
    
    # Initialize all non-admin users removed so we only return secretaries WITH commissions
    
    query_ventas = (
        select(AtencionDetalle)
        .join(Atencion)
        .where(Atencion.sucursal_id == user.sucursal_id)
        .where(Atencion.validado == True)
        .where(AtencionDetalle.comision_pagada == False)
        .where(AtencionDetalle.vendedor_id != None)
        .options(
            selectinload(AtencionDetalle.vendedor), 
            selectinload(AtencionDetalle.tratamiento),
            selectinload(AtencionDetalle.atencion).selectinload(Atencion.pagos)
        )
    )
    if start_date:
        query_ventas = query_ventas.where(Atencion.fecha >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query_ventas = query_ventas.where(Atencion.fecha < end_dt)
        
    detalles_ventas = session.exec(query_ventas).all()
    
    for d in detalles_ventas:
        vend_id = d.vendedor_id
        if vend_id not in vendedores_pendientes:
            vendedores_pendientes[vend_id] = {
                "id": vend_id,
                "nombre": d.vendedor.username if d.vendedor else "Usuario",
                "tipo": "Secretaria/Ventas",
                "comisiones_acumuladas": 0.0,
                "detalles": []
            }
            
        atencion = d.atencion
        total_atn = float(atencion.total_atencion) if getattr(atencion, 'total_atencion', 0) else 0.0
        pagado = sum(float(p.monto) for p in atencion.pagos) if getattr(atencion, 'pagos', []) else 0.0
        porcentaje_pagado = min(pagado / total_atn, 1.0) if total_atn > 0 else 1.0
        
        comision_teorica = float(d.comision_valor)
        comision_real_total = comision_teorica * porcentaje_pagado
        comision_ya_pagada = float(d.comision_pagada_monto) if getattr(d, 'comision_pagada_monto', 0.0) else 0.0
        comision_pendiente = comision_real_total - comision_ya_pagada
        
        if comision_pendiente > 0.01:
            vendedores_pendientes[vend_id]["comisiones_acumuladas"] += comision_pendiente
            vendedores_pendientes[vend_id]["detalles"].append({
                "tratamiento": d.tratamiento.nombre if d.tratamiento else "Venta",
                "valor_tratamiento": float(d.total_calculado),
                "porcentaje": float(d.porcentaje_comision),
                "comision": round(comision_pendiente, 2),
                "fecha": d.atencion.fecha.isoformat()
            })
    return {
        "doctores": list(doctores_pendientes.values()),
        "vendedores": list(vendedores_pendientes.values())
    }

class PagoNominaSchema(BaseModel):
    empleado_id: int
    tipo_empleado: str # 'Doctor' or 'Secretaria'
    sueldo_base: float = 0.0
    comisiones: float = 0.0
    efectivo: float = 0.0
    transferencia: float = 0.0
    tarjeta: float = 0.0
    responsable: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
@app.post("/api/nomina/pagar")
def pagar_nomina(data: PagoNominaSchema, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if not user.sucursal_id:
        raise HTTPException(status_code=400, detail="El usuario no tiene una sucursal asignada")
        
    efectivo_val = Decimal(str(data.efectivo))
    transferencia_val = Decimal(str(data.transferencia))
    tarjeta_val = Decimal(str(data.tarjeta))
    total_entregado = efectivo_val + transferencia_val + tarjeta_val
    total_a_pagar = Decimal(str(data.sueldo_base)) + Decimal(str(data.comisiones))
    
    if total_a_pagar <= 0:
        raise HTTPException(status_code=400, detail="El total a pagar debe ser mayor a 0")
        
    if abs(total_entregado - total_a_pagar) > Decimal("0.02"):
        raise HTTPException(status_code=400, detail=f"La suma de métodos de pago debe ser igual al Total a Pagar (${total_a_pagar})")
        
    sucursal = session.get(Sucursal, user.sucursal_id)
    if not sucursal:
        raise HTTPException(status_code=400, detail="Sucursal no encontrada")
        
    balances = get_gastos_balances(session=session, user=user)
        
    if Decimal(str(balances["efectivo"])) < efectivo_val:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes en Efectivo. Disponible: ${balances['efectivo']}")
        
    if Decimal(str(balances["transferencia"])) < transferencia_val:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes en Bancos. Disponible: ${balances['transferencia']}")
        
    if Decimal(str(balances["tarjeta"])) < tarjeta_val:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes en Tarjeta. Disponible: ${balances['tarjeta']}")
        
    now = datetime.now()
    empleado_nombre = "Empleado"
    
    # Marcar comisiones como pagadas
    if data.tipo_empleado == 'Doctor':
        doctor = session.get(Doctor, data.empleado_id)
        if doctor: empleado_nombre = f"Dr(a). {doctor.nombres} {doctor.apellidos}"
        
        query_pendientes = (
            select(AtencionDetalle)
            .join(Atencion)
            .where(Atencion.sucursal_id == user.sucursal_id)
            .where(Atencion.validado == True)
            .where(AtencionDetalle.comision_pagada == False)
            .where(AtencionDetalle.doctor_id == data.empleado_id)
            .options(selectinload(AtencionDetalle.atencion).selectinload(Atencion.pagos))
        )
        if data.start_date:
            query_pendientes = query_pendientes.where(Atencion.fecha >= datetime.strptime(data.start_date, "%Y-%m-%d"))
        if data.end_date:
            end_dt = datetime.strptime(data.end_date, "%Y-%m-%d") + timedelta(days=1)
            query_pendientes = query_pendientes.where(Atencion.fecha < end_dt)
            
        detalles_pendientes = session.exec(query_pendientes).all()
        
        for d in detalles_pendientes:
            atencion = d.atencion
            total_atn = float(atencion.total_atencion) if getattr(atencion, 'total_atencion', 0) else 0.0
            pagado = sum(float(p.monto) for p in atencion.pagos) if getattr(atencion, 'pagos', []) else 0.0
            porcentaje_pagado = min(pagado / total_atn, 1.0) if total_atn > 0 else 1.0
            
            comision_teorica = float(d.comision_valor)
            comision_real_total = comision_teorica * porcentaje_pagado
            comision_ya_pagada = float(d.comision_pagada_monto) if getattr(d, 'comision_pagada_monto', 0.0) else 0.0
            comision_pendiente = comision_real_total - comision_ya_pagada
            
            if comision_pendiente > 0.01:
                d.comision_pagada_monto = comision_ya_pagada + comision_pendiente
                d.fecha_pago_comision = now
                
                if porcentaje_pagado >= 0.99 and abs(float(d.comision_pagada_monto) - comision_teorica) < 0.02:
                    d.comision_pagada = True
                    
            session.add(d)
            
    elif data.tipo_empleado == 'Secretaria':
        secretaria = session.get(User, data.empleado_id)
        if secretaria: empleado_nombre = f"Sec. {secretaria.username}"
        
        query_pendientes = (
            select(AtencionDetalle)
            .join(Atencion)
            .where(Atencion.sucursal_id == user.sucursal_id)
            .where(Atencion.validado == True)
            .where(AtencionDetalle.comision_pagada == False)
            .where(AtencionDetalle.vendedor_id == data.empleado_id)
            .options(selectinload(AtencionDetalle.atencion).selectinload(Atencion.pagos))
        )
        if data.start_date:
            query_pendientes = query_pendientes.where(Atencion.fecha >= datetime.strptime(data.start_date, "%Y-%m-%d"))
        if data.end_date:
            end_dt = datetime.strptime(data.end_date, "%Y-%m-%d") + timedelta(days=1)
            query_pendientes = query_pendientes.where(Atencion.fecha < end_dt)
            
        detalles_pendientes = session.exec(query_pendientes).all()
        
        for d in detalles_pendientes:
            atencion = d.atencion
            total_atn = float(atencion.total_atencion) if getattr(atencion, 'total_atencion', 0) else 0.0
            pagado = sum(float(p.monto) for p in atencion.pagos) if getattr(atencion, 'pagos', []) else 0.0
            porcentaje_pagado = min(pagado / total_atn, 1.0) if total_atn > 0 else 1.0
            
            comision_teorica = float(d.comision_valor)
            comision_real_total = comision_teorica * porcentaje_pagado
            comision_ya_pagada = float(d.comision_pagada_monto) if getattr(d, 'comision_pagada_monto', 0.0) else 0.0
            comision_pendiente = comision_real_total - comision_ya_pagada
            
            if comision_pendiente > 0.01:
                d.comision_pagada_monto = comision_ya_pagada + comision_pendiente
                d.fecha_pago_comision = now
                
                if porcentaje_pagado >= 0.99 and abs(float(d.comision_pagada_monto) - comision_teorica) < 0.02:
                    d.comision_pagada = True
                    
            session.add(d)
    
    # Create Gasto dynamically based on amounts
    desc_base = f"Liquidación de Nómina: {empleado_nombre} (Base: ${data.sueldo_base}, Comisiones: ${data.comisiones})"
    
    if efectivo_val > 0:
        gasto_efectivo = Gasto(
            fecha=now,
            descripcion=desc_base,
            monto=efectivo_val,
            metodo_pago="EFECTIVO",
            categoria="NÓMINA",
            responsable=data.responsable or user.username,
            sucursal_id=user.sucursal_id,
            usuario_id=user.id
        )
        session.add(gasto_efectivo)
        
    if transferencia_val > 0:
        gasto_transf = Gasto(
            fecha=now,
            descripcion=desc_base,
            monto=transferencia_val,
            metodo_pago="TRANSFERENCIA",
            categoria="NÓMINA",
            responsable=data.responsable or user.username,
            sucursal_id=user.sucursal_id,
            usuario_id=user.id
        )
        session.add(gasto_transf)
        
    if tarjeta_val > 0:
        gasto_tarjeta = Gasto(
            fecha=now,
            descripcion=desc_base,
            monto=tarjeta_val,
            metodo_pago="TARJETA",
            categoria="NÓMINA",
            responsable=data.responsable or user.username,
            sucursal_id=user.sucursal_id,
            usuario_id=user.id
        )
        session.add(gasto_tarjeta)
        
    session.commit()
    
    return {"message": f"Nómina pagada exitosamente a {empleado_nombre}", "total_pagado": float(total_entregado)}

class RetiroSociosSchema(BaseModel):
    monto: float
    metodo_pago: str # 'EFECTIVO' or 'TRANSFERENCIA'
    descripcion: str
    responsable: Optional[str] = None

@app.post("/api/nomina/retiro-socios")
def retiro_socios(data: RetiroSociosSchema, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """ Endpoint for admins to withdraw net profits """
    if user.role != "admin":
         raise HTTPException(status_code=403, detail="Solo los administradores pueden registrar retiros de socios")
         
    if not user.sucursal_id:
         raise HTTPException(status_code=400, detail="Sin sucursal asignada")
         
    if data.monto <= 0:
         raise HTTPException(status_code=400, detail="El monto debe ser positivo")
         
    sucursal = session.get(Sucursal, user.sucursal_id)
    if not sucursal:
        raise HTTPException(status_code=400, detail="Sucursal no encontrada")
        
    balances = get_gastos_balances(session=session, user=user)
    monto_dec = Decimal(str(data.monto))
    
    if data.metodo_pago == "EFECTIVO" and Decimal(str(balances["efectivo"])) < monto_dec:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes en Efectivo. Disponible: ${balances['efectivo']}")
        
    if data.metodo_pago == "TRANSFERENCIA" and Decimal(str(balances["transferencia"])) < monto_dec:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes en Bancos. Disponible: ${balances['transferencia']}")
        
    if data.metodo_pago == "TARJETA" and Decimal(str(balances["tarjeta"])) < monto_dec:
        raise HTTPException(status_code=400, detail=f"Fondos insuficientes en Tarjeta. Disponible: ${balances['tarjeta']}")
         
    gasto = Gasto(
        fecha=datetime.now(),
        descripcion=f"Retiro de Socios / Utilidades: {data.descripcion}",
        monto=Decimal(data.monto),
        metodo_pago=data.metodo_pago,
        categoria="RETIRO SOCIOS",
        responsable=data.responsable or user.username,
        sucursal_id=user.sucursal_id,
        usuario_id=user.id
    )
    session.add(gasto)
    session.commit()
    return {"message": "Retiro registrado exitosamente como Gasto"}
    
class TransferenciaInternaSchema(BaseModel):
    desde: str
    hacia: str
    monto: float
    descripcion: str
    responsable: str

@app.post("/api/gastos/transferencia")
def internal_transfer(data: TransferenciaInternaSchema, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    """ Moves funds between methods by creating two mirrored expense entries """
    if not user.sucursal_id:
        raise HTTPException(status_code=400, detail="Sin sucursal asignada")
    
    if data.desde == data.hacia:
        raise HTTPException(status_code=400, detail="Origen y destino no pueden ser iguales")
    
    if data.monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser positivo")

    # 1. Negative entry (Income for the destination)
    # Since balances = Income - Expenses, a negative expense is an Income.
    entry_to = Gasto(
        fecha=datetime.now(),
        descripcion=f"RECEPCIÓN TRANSFERENCIA: {data.descripcion}",
        monto=Decimal(-data.monto),
        metodo_pago=data.hacia,
        categoria="TRANSFERENCIA INTERNA",
        responsable=data.responsable,
        sucursal_id=user.sucursal_id,
        usuario_id=user.id
    )
    
    # 2. Positive entry (Expense for the origin)
    entry_from = Gasto(
        fecha=datetime.now(),
        descripcion=f"SALIDA TRANSFERENCIA: {data.descripcion}",
        monto=Decimal(data.monto),
        metodo_pago=data.desde,
        categoria="TRANSFERENCIA INTERNA",
        responsable=data.responsable,
        sucursal_id=user.sucursal_id,
        usuario_id=user.id
    )

    session.add(entry_to)
    session.add(entry_from)
    session.commit()
    
    return {"message": "Transferencia realizada con éxito"}

# --- FIN SISTEMA DE NÓMINA ---

@app.get("/api/atenciones/historial/global")
def get_global_historial(page: int = 1, size: int = 50, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    try:
        skip = (page - 1) * size
        # Join with Atencion and Paciente to provide more context in the global list
        logs = session.exec(
            select(AuditoriaAtencion)
            .order_by(AuditoriaAtencion.fecha.desc())
            .offset(skip).limit(size)
        ).all()
        
        return [
            {
                "id": l.id,
                "fecha": l.fecha,
                "atencion_id": l.atencion_id,
                "paciente_nombre": f"{l.atencion.paciente.nombres} {l.atencion.paciente.apellidos}" if l.atencion and l.atencion.paciente else "N/A",
                "accion": l.accion,
                "descripcion": l.descripcion,
                "usuario": l.usuario.username if l.usuario else "Sistema"
            } for l in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recepcion/historial", response_class=HTMLResponse)
def view_historial():
    with open("static/historial.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
