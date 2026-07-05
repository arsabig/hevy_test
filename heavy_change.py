import requests
import time
from datetime import datetime

# Configuración inicial
API_KEY = "2919c555-c965-4981-b57d-800ba236aca1"
BASE_URL = "https://api.hevyapp.com/v1"
HEADERS = {
    "accept": "application/json",
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

def get_all_workouts():
    """Recupera todos los entrenamientos usando paginación estándar de la API."""
    workouts = []
    page = 1
    page_size = 10
    
    while True:
        print(f"Buscando entrenamientos - Página {page}...")
        url = f"{BASE_URL}/workouts?page={page}&pageSize={page_size}"
        
        try:
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code in [404, 400] or "Page not found" in response.text:
                print(f"ℹ️ Final del historial alcanzado de forma segura.")
                break
                
            if response.status_code != 200:
                print(f"⚠️ Deteniendo en página {page}. Código de estado: {response.status_code}")
                break
                
            data = response.json()
            batch = data if isinstance(data, list) else data.get("workouts", [])
            
            if not batch:
                break
                
            workouts.extend(batch)
            page += 1
            time.sleep(0.4)
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            break
        
    return workouts

def clean_workout_for_put(workout):
    """Limpia el objeto y añade los campos obligatorios para cumplir con Hevy."""
    cleaned_exercises = []
    
    for exercise in workout.get("exercises", []):
        cleaned_sets = []
        for s in exercise.get("sets", []):
            cleaned_set = {
                "type": s.get("type", "normal"),
                "reps": s.get("reps"),
                "weight_kg": s.get("weight_kg") if s.get("weight_kg") is not None else s.get("weight")
            }
            if s.get("rpe") is not None: cleaned_set["rpe"] = s.get("rpe")
            if s.get("distance_km") is not None: cleaned_set["distance_km"] = s.get("distance_km")
            if s.get("duration_seconds") is not None: cleaned_set["duration_seconds"] = s.get("duration_seconds")
            
            cleaned_sets.append(cleaned_set)
            
        cleaned_exercise = {
            "exercise_template_id": exercise.get("exercise_template_id") or exercise.get("template_id"),
            "sets": cleaned_sets
        }
        
        exercise_notes = exercise.get("notes")
        if exercise_notes and str(exercise_notes).strip():
            cleaned_exercise["notes"] = str(exercise_notes).strip()
        
        cleaned_exercises.append(cleaned_exercise)

    workout_data = {
        "title": workout.get("title") or "Workout",
        "start_time": workout.get("start_time"),
        "end_time": workout.get("end_time"),
        "is_private": workout.get("is_private", False),
        "exercises": cleaned_exercises
    }
    
    description = workout.get("description")
    if description and str(description).strip():
        workout_data["description"] = str(description).strip()

    payload = {
        "workout": workout_data
    }
    return payload

def fix_dumbbell_weights():
    workouts = get_all_workouts()
    print(f"\nSe encontraron {len(workouts)} entrenamientos en total. Buscando los 4 ejercicios específicos...")
    
    updated_count = 0
    ignored_by_date_count = 0
    
    # 1. Definimos la fecha límite (1 de Junio de 2026)
    fecha_limite = datetime(2026, 6, 1)
    
    # 2. LISTA EXCLUSIVA: Solo se modificará lo que esté aquí dentro
    ejercicios_permitidos = [
        "seated palms up wrist curl",
        "reverse grip concentration curl",
        "cross body hammer curl",
        "concentration curl"
    ]
    
    for workout in workouts:
        workout_id = workout.get("id")
        start_time_str = workout.get("start_time")
        modified = False
        
        try:
            clean_time_str = start_time_str.replace("Z", "")
            workout_date = datetime.fromisoformat(clean_time_str).replace(tzinfo=None)
        except Exception:
            try:
                workout_date = datetime.strptime(start_time_str.strip(), "%d %b %Y, %H:%M").replace(tzinfo=None)
            except Exception:
                continue

        # Omitir entrenamientos de junio de 2026 en adelante
        if workout_date >= fecha_limite:
            ignored_by_date_count += 1
            continue
        
        # Recorrer los ejercicios del entrenamiento
        for exercise in workout.get("exercises", []):
            exercise_title = exercise.get("title") or exercise.get("exercise_title") or ""
            exercise_title_lower = exercise_title.strip().lower()
            
            # FILTRO INVERTIDO: Ahora evaluamos si el ejercicio pertenece a tu lista exacta
            if exercise_title_lower in ejercicios_permitidos:
                for index, s in enumerate(exercise.get("sets", [])):
                    old_weight = s.get("weight_kg") if s.get("weight_kg") is not None else s.get("weight")
                    
                    if old_weight is not None and old_weight > 0:
                        new_weight = float(old_weight) * 2
                        
                        if "weight_kg" in s:
                            exercise["sets"][index]["weight_kg"] = round(new_weight, 2)
                        if "weight" in s or "weight_kg" not in s:
                            exercise["sets"][index]["weight"] = round(new_weight, 2)
                            
                        modified = True
                        print(f"   ↳ Ejercicio detectado: '{exercise_title}' en [{workout_date.strftime('%Y-%m-%d')}]. Multiplicando peso...")
        
        # Guardar cambios si el entrenamiento contiene al menos uno de los 4 ejercicios
        if modified:
            put_url = f"{BASE_URL}/workouts/{workout_id}"
            clean_payload = clean_workout_for_put(workout)
            
            response = requests.put(put_url, headers=HEADERS, json=clean_payload)
            
            if response.status_code in [200, 204]:
                print(f"✅ [{workout_date.strftime('%Y-%m-%d')}] '{workout.get('title')}' actualizado con éxito.")
                updated_count += 1
            else:
                print(f"❌ Error al actualizar entrenamiento {workout_id}: Código {response.status_code} - {response.text}")
            
            time.sleep(0.5)

    print(f"\n¡Proceso finalizado!")
    print(f"--> Entrenamientos corregidos con éxito: {updated_count}")
    print(f"--> Entrenamientos omitidos por fecha (>= Jun 2026): {ignored_by_date_count}")

if __name__ == "__main__":
    fix_dumbbell_weights()