import os
import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2
from dotenv import load_dotenv

# 1. CONFIGURACIÓN DE BASE DE DATOS
load_dotenv()

def obtener_conexion():
    """Establece la conexión con la base de datos PostgreSQL en Supabase."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except Exception as e:
        messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {e}")
        return None

def inicializar_db():
    """Crea la tabla si no existe al iniciar la app."""
    conn = obtener_conexion()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recetas (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT NOT NULL UNIQUE,
                    tiempo REAL NOT NULL
                )
            """)
            conn.commit()
        conn.close()

# 2. LÓGICA DE NEGOCIO (DB)
def db_guardar_receta(nombre, tiempo):
    conn = obtener_conexion()
    if not conn: return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO recetas (nombre, tiempo) VALUES (%s, %s)", (nombre, tiempo))
            conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        messagebox.showwarning("Duplicado", "Ya existe una receta con ese nombre.")
        return False
    except Exception as e:
        messagebox.showerror("Error SQL", f"Ocurrió un error: {e}")
        return False
    finally:
        conn.close()

def db_obtener_recetas():
    conn = obtener_conexion()
    if not conn: return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre, tiempo FROM recetas ORDER BY tiempo ASC")
            return cursor.fetchall()
    finally:
        conn.close()

# 3. INTERFAZ GRÁFICA (GUI)
class AppRecetas:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Recetas - Edición PostgreSQL")
        self.root.geometry("700x500")
        self.root.configure(padx=20, pady=20)

        # Variables de control
        self.var_nombre = tk.StringVar()
        self.var_tiempo = tk.StringVar()

        self.crear_widgets()
        self.actualizar_lista()

    def crear_widgets(self):
        # --- Formulario ---
        frame_form = tk.LabelFrame(self.root, text="Nueva Receta", padx=10, pady=10)
        frame_form.pack(fill="x", pady=10)

        tk.Label(frame_form, text="Nombre:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame_form, textvariable=self.var_nombre, width=30).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_form, text="Tiempo (min):").grid(row=0, column=2, sticky="w")
        tk.Entry(frame_form, textvariable=self.var_tiempo, width=10).grid(row=0, column=3, padx=5, pady=5)

        # --- Botonera ---
        frame_btns = tk.Frame(self.root)
        frame_btns.pack(fill="x", pady=5)

        tk.Button(frame_btns, text="Guardar Receta", command=self.guardar, bg="#4CAF50", fg="white").pack(side="left", padx=2)
        tk.Button(frame_btns, text="Limpiar Campos", command=self.limpiar_campos).pack(side="left", padx=2)
        tk.Button(frame_btns, text="Cargar Prueba", command=self.cargar_prueba).pack(side="left", padx=2)
        tk.Button(frame_btns, text="Refrescar Lista", command=self.actualizar_lista).pack(side="left", padx=2)

        # --- Tabla (Treeview) ---
        self.tabla = ttk.Treeview(self.root, columns=("Nombre", "Tiempo", "Comparación"), show='headings')
        self.tabla.heading("Nombre", text="Nombre del Plato")
        self.tabla.heading("Tiempo", text="Tiempo (min)")
        self.tabla.heading("Comparación", text="Relación vs Base")
        self.tabla.column("Nombre", width=200)
        self.tabla.column("Tiempo", width=100, anchor="center")
        self.tabla.pack(fill="both", expand=True, pady=10)

    def guardar(self):
        nombre = self.var_nombre.get().strip()
        tiempo_str = self.var_tiempo.get().strip()

        # Validaciones
        if not nombre:
            messagebox.showwarning("Validación", "El nombre no puede estar vacío.")
            return

        try:
            tiempo = float(tiempo_str)
            if tiempo <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validación", "El tiempo debe ser un número mayor a cero.")
            return

        # Proceso de guardado
        if db_guardar_receta(nombre, tiempo):
            messagebox.showinfo("Éxito", f"Receta '{nombre}' guardada.")
            self.limpiar_campos()
            self.actualizar_lista()

    def actualizar_lista(self):
        # Limpiar tabla actual
        for i in self.tabla.get_children():
            self.tabla.delete(i)

        recetas = db_obtener_recetas()
        if not recetas:
            return

        # La receta base es la de menor tiempo (primera por el ORDER BY ASC)
        nombre_base, tiempo_base = recetas[0]

        for nombre, tiempo in recetas:
            # Lógica de comparación
            equiv = tiempo / tiempo_base
            relacion = f"{int(equiv) if equiv.is_integer() else equiv:.2f}x {nombre_base}"
            
            self.tabla.insert("", "end", values=(nombre, f"{tiempo:.2f}", relacion))

    def cargar_prueba(self):
        datos = [
            ("Hervir agua", 10), ("Freir huevo", 12), ("Salsa", 15), ("Arroz", 30)
        ]
        agregados = 0
        for n, t in datos:
            if db_guardar_receta(n, t):
                agregados += 1
        
        if agregados > 0:
            messagebox.showinfo("Prueba", f"Se agregaron {agregados} nuevas recetas.")
            self.actualizar_lista()

    def limpiar_campos(self):
        self.var_nombre.set("")
        self.var_tiempo.set("")

if __name__ == "__main__":
    inicializar_db()
    root = tk.Tk()
    app = AppRecetas(root)
    root.mainloop()