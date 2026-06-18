# secure-ml-pipeline

> Pipeline CI/CD seguro con detección automática de vulnerabilidades en código fuente mediante un modelo de minería de datos (XGBoost + TF-IDF + AST + patrones de seguridad).

[![Python](https://img.shields.io/badge/python-3.12-blue)]()

Proyecto Integrador — **Desarrollo de Software Seguro** · ESPE · Parcial II · 2026

---

## 1. Objetivo

Diseñar, implementar y demostrar un pipeline CI/CD completamente automatizado y seguro que integre un modelo de IA (minería de datos clásico — **sin LLMs**) capaz de clasificar código fuente como **SEGURO** o **VULNERABLE**, de forma que solo el código seguro llegue a producción.

Esto aplica los principios de **Secure DevOps** y **Shift-Left Security**.

---

## 2. Arquitectura del flujo

```
        Push
         │
         ▼
  ┌──────────────┐
  │  rama  dev   │  ← el desarrollador hace push aquí
  └──────┬───────┘
         │ Pull Request  dev → test
         ▼
  ╔══════════════════════════════════════════════════════╗
  ║  Job 1 · security-review                             ║
  ║  • Descarga el diff del PR                            ║
  ║  • Filtra archivos .py / .ts / .js                    ║
  ║  • Ejecuta ml/predict.py con el modelo .joblib        ║
  ║  • Si VULNERABLE → etiqueta "fixing-required",       ║
  ║    crea issue, comenta el PR, notifica Telegram       ║
  ║  • Si SEGURO    → etiqueta "security-approved"        ║
  ╚══════════════════════════════════════════════════════╝
         │ (solo si SEGURO)
         ▼
  ╔══════════════════════════════════════════════════════╗
  ║  Job 2 · test-and-merge                              ║
  ║  • Auto-merge a rama test (squash)                    ║
  ║  • Ejecuta pytest                                     ║
  ║  • Si falla → etiqueta "tests-failed"                ║
  ╚══════════════════════════════════════════════════════╝
         │ (solo si tests pasan)
         ▼
  ╔══════════════════════════════════════════════════════╗
  ║  Job 3 · deploy                                      ║
  ║  • Auto-merge a main                                  ║
  ║  • Build imagen Docker                                ║
  ║  • Despliegue automático en Render                    ║
  ╚══════════════════════════════════════════════════════╝
         │
         ▼
   🚀 Producción (Render)
```

Notificaciones vía **Telegram Bot** en cada evento (inicio, clasificación, merge, tests, deploy, rechazo).

---

## 3. Ramas

- **`main`** — producción. Protegida, solo recibe merges desde `test` ya verificados.
- **`test`** — staging. Aquí se ejecutan las pruebas automatizadas tras la revisión de seguridad.
- **`dev`** — desarrollo. El dev hace push aquí y abre PR hacia `test`.

---

## 4. Estructura del repositorio

```
secure-ml-pipeline/
├── .github/
│   └── workflows/
│       └── security-pipeline.yml      # workflow CI/CD
├── ml/
│   ├── modelo_seguridad.joblib        # modelo entrenado (XGBoost)
│   ├── predict.py                     # inferencia (próxima fase)
│   ├── requirements.txt               # dependencias de inferencia
│   └── Entrenamiento_Modelo_Seguridad_SEMMA_FINAL.ipynb
├── app/                               # FastAPI demo (próxima fase)
│   ├── main.py
│   ├── routers/
│   ├── tests/
│   ├── requirements.txt
│   └── pytest.ini
├── scripts/
│   └── telegram_notify.py             # notificaciones (próxima fase)
├── docs/
│   └── PROY_PARCIAL_II_DesSeguro.md   # enunciado de la actividad
├── Dockerfile
├── render.yaml
├── postman_collection.json      # colección Postman (endpoints API)
├── .gitignore
└── README.md
```

---

## 6. Modelo de minería de datos

- **Algoritmo:** `XGBClassifier` con `GridSearchCV` + validación cruzada estratificada 5-fold.
- **Features (4 ramas en `FeatureUnion`):**
  1. TF-IDF char n-grams (3–6, max 25 000 features)
  2. TF-IDF word n-grams (1–2, max 15 000 features)
  3. AST features (22 nodos — `ast.FeatureExtractor` sobre Python AST)
  4. Patrones de seguridad: 30 DANGER + 15 SAFE + ratios derivados
- **Accuracy objetivo:** ≥ 82 % (mostrada en la sección 7 del informe).
- **Prohibido:** cualquier LLM (GPT, Claude, Llama, CodeLlama, etc.) — solo clasificadores clásicos.

Detalles completos en el notebook: [`ml/Entrenamiento_Modelo_Seguridad_SEMMA_FINAL.ipynb`](ml/Entrenamiento_Modelo_Seguridad_SEMMA_FINAL.ipynb).

---

## 7. Despliegue

Proveedor: **Render**

URL de producción: https://secure-ml-pipeline.onrender.com/health

---

## 8. Documentación relacionada

- 📄 [Enunciado de la actividad](docs/PROY_PARCIAL_II_DesSeguro.md)
- 📓 [Notebook de entrenamiento](ml/Entrenamiento_Modelo_Seguridad_SEMMA_FINAL.ipynb)

---
