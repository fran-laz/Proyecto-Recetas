import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2


class AppRecetasSupabase:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Recetas - Supabase")
        self.root.geometry("750x600")
        self.root.configure(padx=20, pady=20)

        # Datos de conexión
        self.db_params = {
            "host": "aws-1-us-west-2.pooler.supabase.com",
            "port": 5432,
            "database": "postgres",
            "user": "postgres.axshypwvvpouadoxcqkx",
            "password": "47E%+qsJTuq.XB!"
        }

        self.id_seleccionado = None

        # Crear tabla
        self.init_db()

        frame_input = tk.LabelFrame(
            self.root,
            text="Datos de la Receta",
            padx=10,
            pady=10
        )
        frame_input.pack(fill="x", pady=10)

        tk.Label(frame_input, text="Nombre:").grid(row=0, column=0, sticky="w")

        self.ent_nombre = tk.Entry(frame_input, width=30)
        self.ent_nombre.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(frame_input, text="Tiempo (min):").grid(row=0, column=2, sticky="w")

        self.ent_tiempo = tk.Entry(frame_input, width=10)
        self.ent_tiempo.grid(row=0, column=3, padx=10, pady=5)

        # Botones
        frame_botones = tk.Frame(self.root)
        frame_botones.pack(pady=10)

        tk.Button(
            frame_botones,
            text="Agregar",
            command=self.agregar_receta,
            bg="#4CAF50",
            fg="white",
            width=15
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            frame_botones,
            text="Modificar",
            command=self.modificar_receta,
            bg="#2196F3",
            fg="white",
            width=15
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            frame_botones,
            text="Eliminar",
            command=self.eliminar_receta,
            bg="#F44336",
            fg="white",
            width=15
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            frame_botones,
            text="Limpiar",
            command=self.limpiar_campos,
            width=15
        ).grid(row=0, column=3, padx=5)

        # Tabla
        columnas = ("id", "nombre", "tiempo", "base")

        self.tabla = ttk.Treeview(
            self.root,
            columns=columnas,
            show="headings"
        )

        self.tabla.heading("id", text="ID")
        self.tabla.heading("nombre", text="Nombre")
        self.tabla.heading("tiempo", text="Tiempo")
        self.tabla.heading("base", text="Relación Base")

        self.tabla.column("id", width=50, anchor="center")
        self.tabla.column("nombre", width=250)
        self.tabla.column("tiempo", width=100, anchor="center")
        self.tabla.column("base", width=150, anchor="center")

        self.tabla.pack(fill="both", expand=True)

        self.tabla.bind("<<TreeviewSelect>>", self.cargar_en_campos)

        self.actualizar_tabla()


    def conectar(self):
        try:
            return psycopg2.connect(**self.db_params)
        except Exception as e:
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar a la base de datos:\n\n{e}"
            )
            return None

    def init_db(self):
        conn = self.conectar()
        if not conn:
            return

        try:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS recetas (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT UNIQUE NOT NULL,
                    tiempo REAL NOT NULL,
                    es_base INTEGER DEFAULT 0
                )
            """)

            conn.commit()

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            conn.close()

    def obtener_base(self):
        conn = self.conectar()
        if not conn:
            return None

        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT nombre, tiempo
                FROM recetas
                WHERE es_base = 1
                LIMIT 1
            """)
            return cur.fetchone()

        finally:
            conn.close()


    def agregar_receta(self):
        nombre = self.ent_nombre.get().strip()
        tiempo_texto = self.ent_tiempo.get().strip()

        if not nombre:
            messagebox.showwarning("Aviso", "Ingresa un nombre.")
            return

        try:
            tiempo = float(tiempo_texto)
        except ValueError:
            messagebox.showwarning("Aviso", "El tiempo debe ser un número.")
            return

        conn = self.conectar()
        if not conn:
            return

        try:
            cur = conn.cursor()

            # Verificar si ya existe receta base
            cur.execute("SELECT COUNT(*) FROM recetas WHERE es_base = 1")
            hay_base = cur.fetchone()[0] > 0

            es_base = 0

            if not hay_base:
                respuesta = messagebox.askyesno(
                    "Receta Base",
                    f"¿Quieres que '{nombre}' sea la receta base?"
                )
                if respuesta:
                    es_base = 1

            cur.execute("""
                INSERT INTO recetas (nombre, tiempo, es_base)
                VALUES (%s, %s, %s)
            """, (nombre, tiempo, es_base))

            conn.commit()

            messagebox.showinfo("Éxito", "Receta agregada correctamente.")
            self.limpiar_campos()
            self.actualizar_tabla()

        except psycopg2.IntegrityError:
            conn.rollback()
            messagebox.showerror("Error", "Ya existe una receta con ese nombre.")

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", str(e))

        finally:
            conn.close()

    def modificar_receta(self):
        if self.id_seleccionado is None:
            messagebox.showwarning("Aviso", "Selecciona una receta.")
            return

        nombre = self.ent_nombre.get().strip()
        tiempo_texto = self.ent_tiempo.get().strip()

        try:
            tiempo = float(tiempo_texto)
        except ValueError:
            messagebox.showerror("Error", "Tiempo inválido.")
            return

        conn = self.conectar()
        if not conn:
            return

        try:
            cur = conn.cursor()

            cur.execute("""
                UPDATE recetas
                SET nombre = %s, tiempo = %s
                WHERE id = %s
            """, (nombre, tiempo, self.id_seleccionado))

            conn.commit()

            messagebox.showinfo("Éxito", "Receta modificada.")
            self.limpiar_campos()
            self.actualizar_tabla()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", str(e))

        finally:
            conn.close()

    def eliminar_receta(self):
        if self.id_seleccionado is None:
            messagebox.showwarning("Aviso", "Selecciona una receta.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar",
            "¿Seguro que quieres eliminar la receta?"
        )

        if not confirmar:
            return

        conn = self.conectar()
        if not conn:
            return

        try:
            cur = conn.cursor()

            cur.execute(
                "DELETE FROM recetas WHERE id = %s",
                (self.id_seleccionado,)
            )

            conn.commit()

            messagebox.showinfo("Éxito", "Receta eliminada.")
            self.limpiar_campos()
            self.actualizar_tabla()

        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error", str(e))

        finally:
            conn.close()


    def actualizar_tabla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        conn = self.conectar()
        if not conn:
            return

        try:
            cur = conn.cursor()

            cur.execute("""
                SELECT nombre, tiempo
                FROM recetas
                WHERE es_base = 1
                LIMIT 1
            """)
            base = cur.fetchone()

            cur.execute("""
                SELECT id, nombre, tiempo, es_base
                FROM recetas
                ORDER BY id
            """)

            recetas = cur.fetchall()

            for id_db, nombre, tiempo, es_base in recetas:
                if es_base == 1:
                    nombre_mostrar = f"{nombre} (BASE)"
                else:
                    nombre_mostrar = nombre

                if base:
                    relacion = f"{tiempo / base[1]:.2f}x"
                else:
                    relacion = "N/A"

                self.tabla.insert(
                    "",
                    tk.END,
                    values=(id_db, nombre_mostrar, tiempo, relacion)
                )

        except Exception as e:
            messagebox.showerror("Error", str(e))

        finally:
            conn.close()


    def cargar_en_campos(self, event):
        seleccion = self.tabla.selection()

        if not seleccion:
            return

        valores = self.tabla.item(seleccion[0], "values")

        self.id_seleccionado = valores[0]

        self.ent_nombre.delete(0, tk.END)
        self.ent_nombre.insert(0, valores[1].replace(" (BASE)", ""))

        self.ent_tiempo.delete(0, tk.END)
        self.ent_tiempo.insert(0, valores[2])

    def limpiar_campos(self):
        self.ent_nombre.delete(0, tk.END)
        self.ent_tiempo.delete(0, tk.END)
        self.id_seleccionado = None



if __name__ == "__main__":
    root = tk.Tk()
    app = AppRecetasSupabase(root)
    root.mainloop()