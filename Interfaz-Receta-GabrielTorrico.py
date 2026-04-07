import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2 # Cambiamos sqlite3 por psycopg2

class AppRecetasSupabase:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Recetas - Conectado a Supabase")
        self.root.geometry("750x600")
        self.root.configure(padx=20, pady=20)

        # Configuración de conexión (Basado en tus datos)
        self.db_params = {
            "host": "aws-1-us-west-2.pooler.supabase.com",
            "port": "5432",
            "database": "postgres",
            "user": "postgres.axshypwvvpouadoxcqkx",
            "password": "47E%+qsJTuq.XB!)"
        }

        self.init_db()
        self.id_seleccionado = None 

        # --- Interfaz (Entradas) ---
        frame_input = tk.LabelFrame(root, text=" Datos de la Receta ", padx=10, pady=10)
        frame_input.pack(fill="x", pady=5)

        tk.Label(frame_input, text="Nombre:").grid(row=0, column=0, sticky="w")
        self.ent_nombre = tk.Entry(frame_input)
        self.ent_nombre.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        tk.Label(frame_input, text="Tiempo (min):").grid(row=0, column=2, sticky="w")
        self.ent_tiempo = tk.Entry(frame_input)
        self.ent_tiempo.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

        # --- Botones ---
        frame_botones = tk.Frame(root)
        frame_botones.pack(pady=10)

        tk.Button(frame_botones, text="Agregar Nueva", command=self.agregar_receta, bg="#4CAF50", fg="white", width=15).grid(row=0, column=0, padx=5)
        tk.Button(frame_botones, text="Guardar Cambios", command=self.modificar_receta, bg="#2196F3", fg="white", width=15).grid(row=0, column=1, padx=5)
        tk.Button(frame_botones, text="Eliminar", command=self.eliminar_receta, bg="#F44336", fg="white", width=15).grid(row=0, column=2, padx=5)

        # --- Tabla ---
        columnas = ("id", "pos", "nombre", "tiempo", "base")
        self.tabla = ttk.Treeview(root, columns=columnas, show="headings")
        self.tabla.heading("id", text="ID")
        self.tabla.heading("pos", text="#")
        self.tabla.heading("nombre", text="Nombre del Item")
        self.tabla.heading("tiempo", text="Minutos")
        self.tabla.heading("base", text="Conversión Base")

        self.tabla.column("id", width=0, stretch=tk.NO) 
        self.tabla.column("pos", width=40, anchor="center")
        
        self.tabla.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.cargar_en_campos)

        self.actualizar_tabla()

    def conectar(self):
        """Crea una conexión rápida a PostgreSQL."""
        return psycopg2.connect(**self.db_params)

    def init_db(self):
        """Crea la tabla en Supabase si no existe."""
        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS recetas 
                        (id SERIAL PRIMARY KEY, 
                         nombre TEXT UNIQUE, 
                         tiempo REAL, 
                         es_base INTEGER DEFAULT 0)''')
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la DB: {e}")

    def hay_receta_base(self):
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM recetas WHERE es_base = 1")
        existe = cur.fetchone()[0] > 0
        cur.close()
        conn.close()
        return existe

    def agregar_receta(self):
        nombre = self.ent_nombre.get().strip()
        tiempo_s = self.ent_tiempo.get().strip()
        if not nombre or not tiempo_s: return

        try:
            tiempo = float(tiempo_s)
            es_base = 0
            if not self.hay_receta_base():
                if messagebox.askyesno("Receta Base", f"¿Quieres que '{nombre}' sea la receta base?"):
                    es_base = 1
            
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute("INSERT INTO recetas (nombre, tiempo, es_base) VALUES (%s, %s, %s)", (nombre, tiempo, es_base))
            conn.commit()
            cur.close()
            conn.close()
            self.limpiar_campos()
            self.actualizar_tabla()
        except psycopg2.IntegrityError:
            messagebox.showerror("Error", "Ese nombre ya existe.")
        except ValueError:
            messagebox.showerror("Error", "Tiempo inválido.")

    def modificar_receta(self):
        if not self.id_seleccionado: return
        nombre = self.ent_nombre.get().strip()
        tiempo = self.ent_tiempo.get().strip()
        try:
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute("UPDATE recetas SET nombre = %s, tiempo = %s WHERE id = %s", (nombre, float(tiempo), self.id_seleccionado))
            conn.commit()
            cur.close()
            conn.close()
            self.limpiar_campos()
            self.actualizar_tabla()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_receta(self):
        if not self.id_seleccionado: return
        if messagebox.askyesno("Confirmar", "¿Eliminar receta?"):
            conn = self.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM recetas WHERE id = %s", (self.id_seleccionado,))
            conn.commit()
            cur.close()
            conn.close()
            self.limpiar_campos()
            self.actualizar_tabla()

    def cargar_en_campos(self, event):
        seleccion = self.tabla.selection()
        if seleccion:
            valores = self.tabla.item(seleccion)['values']
            self.id_seleccionado = valores[0]
            self.ent_nombre.delete(0, tk.END)
            self.ent_nombre.insert(0, valores[2].replace(" (BASE)", "")) # Limpiar el texto visual
            self.ent_tiempo.delete(0, tk.END)
            self.ent_tiempo.insert(0, valores[3])

    def limpiar_campos(self):
        self.ent_nombre.delete(0, tk.END)
        self.ent_tiempo.delete(0, tk.END)
        self.id_seleccionado = None

    def actualizar_tabla(self):
        for i in self.tabla.get_children(): self.tabla.delete(i)
        
        try:
            conn = self.conectar()
            cur = conn.cursor()
            
            # Obtener base
            cur.execute("SELECT nombre, tiempo FROM recetas WHERE es_base = 1 LIMIT 1")
            base = cur.fetchone()
            
            # Actualizar encabezado dinámico
            if base:
                self.tabla.heading("base", text=f"Tiempo en '{base[0]}'")
            else:
                self.tabla.heading("base", text="Conversión Base")

            # Obtener todas
            cur.execute("SELECT id, nombre, tiempo, es_base FROM recetas ORDER BY id ASC")
            for idx, (id_db, nombre, tiempo, es_base_db) in enumerate(cur.fetchall(), 1):
                conv = f"{(tiempo / base[1]):g}" if base else "N/A"
                mostrar_nombre = f"{nombre} (BASE)" if es_base_db == 1 else nombre
                self.tabla.insert("", tk.END, values=(id_db, idx, mostrar_nombre, tiempo, conv))
            
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error al actualizar tabla: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppRecetasSupabase(root)
    root.mainloop()