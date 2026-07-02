import pandas as pd
from datetime import datetime

# 1. Cargar el archivo original exportado
df = pd.read_csv("workout_data_fixed.csv")

# 2. Convertir y formatear las fechas a 'YYYY-MM-DD HH:MM:SS'
def format_date(dt_str):
    try:
        # Se adapta al formato del CSV original "12 Jan 2026, 16:51"
        dt = datetime.strptime(str(dt_str).strip(), "%d %b %Y, %H:%M")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt_str

df['Date'] = df['start_time'].apply(format_date)

# 3. Calcular la duración del entrenamiento (Workout Duration) en formato 'Xh Ym'
def calculate_duration(row):
    try:
        start = datetime.strptime(str(row['start_time']).strip(), "%d %b %Y, %H:%M")
        end = datetime.strptime(str(row['end_time']).strip(), "%d %b %Y, %H:%M")
        diff = end - start
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception:
        return ""

df['Workout Duration'] = df.apply(calculate_duration, axis=1)

# 4. Asignar las columnas directas y calcular el Set Order (sumando 1 para empezar en 1)
df['Workout Name'] = df['title']
df['Exercise Name'] = df['exercise_title']
df['Set Order'] = pd.to_numeric(df['set_index'], errors='coerce').fillna(0).astype(int) + 1
df['Weight'] = df['weight_kg']
df['Weight Unit'] = 'kg'
df['Reps'] = df['reps']
df['RPE'] = df['rpe']

# 5. Manejar ejercicios de cardio/distancia y segundos
df['Distance'] = df['distance_km']
df['Distance Unit'] = df['distance_km'].apply(lambda x: 'km' if pd.notna(x) and x != "" else "")
df['Seconds'] = df['duration_seconds'].fillna(0).astype(int)

# 6. Notas de ejercicio y de la rutina
df['Notes'] = df['exercise_notes']
df['Workout Notes'] = df['description']

# 7. Reordenar las columnas de manera exacta a tu plantilla
columns_order = [
    'Date', 'Workout Name', 'Exercise Name', 'Set Order', 'Weight', 'Weight Unit', 
    'Reps', 'RPE', 'Distance', 'Distance Unit', 'Seconds', 'Notes', 'Workout Notes', 'Workout Duration'
]

df_final = df[columns_order]

# 8. Exportar al formato CSV separado por punto y coma (;) requerido
output_filename = "hevy_import_ready.csv"
df_final.to_csv(output_filename, index=False, sep=';')

print(f"¡Proceso completado! Archivo listo guardado como: {output_filename}")