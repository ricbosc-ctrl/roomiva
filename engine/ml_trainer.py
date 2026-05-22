"""
Entrenamiento del modelo ML con feedback de usuarios.
Usa regresión logística para aprender los pesos óptimos de cada criterio.
Ejecutar: python3 engine/ml_trainer.py
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_all_feedback, get_feedback_count
from engine.recommender import DEFAULT_WEIGHTS

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "ml_weights.json")
MIN_SAMPLES = 10   # mínimo de feedbacks para entrenar


def train():
    count = get_feedback_count()
    print(f"Feedbacks disponibles: {count}")

    if count < MIN_SAMPLES:
        print(f"Se necesitan al menos {MIN_SAMPLES} feedbacks para entrenar. Usando pesos por defecto.")
        return False

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        import numpy as np
    except ImportError:
        print("Instala scikit-learn: pip3 install scikit-learn numpy")
        return False

    rows = get_all_feedback()
    features = ["score_estilo","score_ruido","score_horario","score_duracion","score_edad","score_ocupacion","score_genero"]
    keys = ["estilo_convivencia","tolerancia_ruido","horario","duracion","edad","ocupacion","genero"]

    X = np.array([[r[f] for f in features] for r in rows])
    y = np.array([r["valor"] for r in rows])

    if len(set(y)) < 2:
        print("No hay suficiente variedad en el feedback (necesitas likes Y dislikes).")
        return False

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=500, C=1.0)
    model.fit(X_scaled, y)

    # Extraer coeficientes y normalizarlos como pesos (suman 1)
    coefs = model.coef_[0]
    coefs_positive = coefs - coefs.min() + 0.01   # todo positivo
    total = coefs_positive.sum()
    weights = {k: round(float(v / total), 4) for k, v in zip(keys, coefs_positive)}

    # Guardar
    with open(WEIGHTS_PATH, "w") as f:
        json.dump(weights, f, indent=2)

    print("\nPesos aprendidos:")
    print(f"{'Criterio':<22} {'Peso base':>10} {'Peso ML':>10} {'Cambio':>10}")
    print("-" * 56)
    for k in keys:
        base = DEFAULT_WEIGHTS.get(k, 0)
        ml   = weights.get(k, 0)
        diff = ml - base
        sign = "+" if diff >= 0 else ""
        print(f"{k:<22} {base:>10.3f} {ml:>10.3f} {sign+f'{diff:.3f}':>10}")

    acc = model.score(X_scaled, y)
    print(f"\nPrecisión del modelo: {acc:.1%} ({count} muestras)")
    print(f"Pesos guardados en: {WEIGHTS_PATH}")
    return True


if __name__ == "__main__":
    train()
