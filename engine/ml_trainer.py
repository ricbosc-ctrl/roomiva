"""
Entrenador ML v2 — aprende la función de agregación grupal óptima.
En lugar de aprender pesos de criterios, aprende qué combinación de
mean/min/weighted predice mejor si un match gustará o no.

Ejecutar: python3 engine/ml_trainer.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database.db import get_all_feedback, get_feedback_count, save_ml_weights, get_ml_weights

MIN_SAMPLES = 10


def train():
    count = get_feedback_count()
    print(f"Feedbacks disponibles: {count}")

    if count < MIN_SAMPLES:
        print(f"Se necesitan al menos {MIN_SAMPLES} feedbacks. Usando pesos por defecto.")
        return False

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        import numpy as np
    except ImportError:
        print("Instala scikit-learn: pip3 install scikit-learn numpy --break-system-packages")
        return False

    rows = get_all_feedback()

    # Features: los tres métodos de agregación grupal
    X = np.array([[r["score_mean"], r["score_min"], r["score_weighted"]] for r in rows])
    y = np.array([r["valor"] for r in rows])

    if len(set(y)) < 2:
        print("Necesitas feedbacks positivos Y negativos.")
        return False

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=500, C=1.0)
    model.fit(X_scaled, y)

    coefs = model.coef_[0]
    coefs_pos = coefs - coefs.min() + 0.01
    total = coefs_pos.sum()
    alpha_mean     = round(float(coefs_pos[0] / total), 4)
    alpha_min      = round(float(coefs_pos[1] / total), 4)
    alpha_weighted = round(float(coefs_pos[2] / total), 4)

    acc = model.score(X_scaled, y)
    save_ml_weights(alpha_mean, alpha_min, alpha_weighted, count, acc)

    current = get_ml_weights()
    print("\n── Función de agregación aprendida ──────────────────")
    print(f"{'Método':<20} {'Antes':>10} {'Después':>10} {'Interpretación'}")
    print("-" * 70)
    methods = [
        ("Media (mean)",     0.40, alpha_mean,     "Todos los convivientes pesan igual"),
        ("Mínimo (min)",     0.30, alpha_min,       "El más difícil de convencer marca el score"),
        ("Ponderada",        0.30, alpha_weighted,  "El propietario pesa el doble"),
    ]
    for name, before, after, interp in methods:
        diff = after - before
        sign = "+" if diff >= 0 else ""
        print(f"{name:<20} {before:>10.3f} {after:>10.3f}   {sign}{diff:.3f}  — {interp}")

    print(f"\nPrecisión del modelo: {acc:.1%} ({count} muestras)")

    dominant = max(methods, key=lambda x: x[2])
    print(f"\nConclusión: el método dominante es '{dominant[0]}' (alpha={dominant[2]:.3f})")
    if dominant[0] == "Media (mean)":
        print("  → Los usuarios valoran la compatibilidad media con todos los convivientes por igual.")
    elif dominant[0] == "Mínimo (min)":
        print("  → Los usuarios necesitan encajar bien con TODOS los convivientes para interesarse.")
    else:
        print("  → La opinión del propietario pesa más en la decisión final.")

    return True


if __name__ == "__main__":
    train()
