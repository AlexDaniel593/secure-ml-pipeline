# ESPE - Universidad de las Fuerzas Armadas
### Departamento de Ciencias de la Computación
### Carrera de Ingeniería en Software

---

* **Asignatura:** Desarrollo de Software Seguro
* **Actividad:** Proyecto Integrador Parcial II
* **Profesor:** Geovanny Cudco
* **Fecha de Publicación:** 28 de mayo de 2026

---

## 1. Tema
**Desarrollo e Implementación de un Pipeline CI/CD Seguro con integración de IA para la Detección Automática de Vulnerabilidades en código fuente mediante un Modelo de Minería de Datos.**

## 2. Tipo de actividad
Proyecto práctico individual o en equipo (máximo 3 personas).

## 3. Objetivo
Diseñar, implementar y demostrar un pipeline CI/CD completamente automatizado y seguro que integre un modelo de inteligencia artificial basado en técnicas de minería de datos capaz de clasificar código fuente como seguro o vulnerable, permitiendo que únicamente el código considerado seguro llegue a producción, garantizando así la aplicación de los principios de *Secure DevOps* y *Shift-Left Security*.

> ⚠️ **IMPORTANTE:** Está estrictamente prohibido la incorporación de tecnologías de Large Language Models (LLM) como GPT, Claude, Llama, CodeLlama, etc. El modelo de IA debe ser obligatoriamente un clasificador de minería de datos tradicional (`scikit-learn`, `XGBoost`, `Random Forest`, `SVM`, etc.) entrenado por usted, usando datasets públicos (o propios) de código vulnerable/seguro.

---

## 4. Descripción
El proyecto consiste en crear una infraestructura CI/CD segura y automatizada que procese código fuente presentado por un usuario en una rama de testing de un repositorio Git (usando GitHub o GitLab).

### 4.1. Flujo de trabajo requerido

#### 4.1.1. Ramas obligatorias
* `dev`: Rama de desarrollo (donde el desarrollador hace push).
* `test`: Rama de staging/pruebas.
* `main`: Rama de producción.

#### 4.1.2. Trigger (Disparador)
* El pipeline se activa automáticamente al crear un **Pull Request** de `dev` $\rightarrow$ `test`.

#### 4.1.3. Etapas del Pipeline (Todas obligatorias y automatizadas)

##### 🛠️ Etapa 1: Revisión de Seguridad con Modelo de Minería de Datos
* Se ejecuta un job que descarga el `diff` del PR.
* Se procesa el código modificado (extrayendo features como tokens, AST simplificado, patrones de llamadas a funciones peligrosas, uso de sanitización, etc.).
* Se clasifica el código como **SEGURO** o **VULNERABLE** utilizando exclusivamente un modelo de machine learning clásico (`scikit-learn`, `XGBoost`, etc.).
* **Si el modelo devuelve "VULNERABLE":**
  * El PR se marca automáticamente como *rejected* o se bloquea el merge.
  * Se crea un comentario detallado en el PR con la probabilidad y el tipo de vulnerabilidad detectada.
  * Se envía una notificación inmediata vía **Telegram** al desarrollador con el detalle.
  * Se aplica la etiqueta `"fixing-required"` y se crea una *issue* automática vinculada.
* **Si el modelo devuelve "SEGURO":** Continúa el pipeline.

##### 🧪 Etapa 2: Merge Automático a rama test + Pruebas
* Merge automático a la rama `test`.
* Ejecución de pruebas unitarias y de integración (`pytest`, `Jest`, `JUnit`, etc.).
* **Si alguna prueba falla:** Bloqueo, notificación por Telegram y asignación de la etiqueta `"tests-failed"`.

##### 🚀 Etapa 3: Merge a main y Despliegue en Producción
* Solo si todo lo anterior pasó, se realiza un merge automático a `main`.
* Build de la imagen Docker y despliegue automático en un proveedor gratuito. Opciones permitidas:
  * Render, Railway, Fly.io, Vercel (solo para frontend), Northflank, o Docker Hub + Play with Docker (para la demo).
  * Heroku (si aún tiene plan gratuito disponible).
  * Otro proveedor que considere el estudiante.
* Notificación final de éxito vía Telegram y/o email.

#### 4.1.4. Notificaciones obligatorias en todas las fases
Deben enviarse mensajes vía **Telegram** (mediante un bot propio) o correo electrónico en los siguientes eventos:
1. Inicio de revisión de seguridad.
2. Resultado de la clasificación del modelo (seguro/vulnerable + probabilidad).
3. Merge a `test` realizado.
4. Resultado de pruebas unitarias/integración.
5. Despliegue en producción exitoso o fallido.
6. Rechazo por vulnerabilidad (con el debido detalle).

---

## 5. Requisitos
* **a.** Modelo de minería de datos entrenado por el estudiante (deben entregar el archivo `.pkl` o `.joblib`).
* **b.** Dataset utilizado debe ser público (Recomendados: Kaggle, Big-Vul, Diverse Vul, CVEFixes, o sintético con Juliet Test Suite).
* **c.** *Features* mínimas: tokens, AST depth, llamadas a funciones peligrosas (`eval`, `exec`, `subprocess`, SQL raw, etc.), presencia de sanitización/escapes.
* **d.** Accuracy mínima demostrada: **82%** en validación cruzada (debe mostrarse y detallarse en el `README.md`).
* **e.** Telegram Bot propio (con el token almacenado de forma segura en GitHub Secrets).
* **f.** Despliegue real y funcional (debe estar online y accesible).
* **g.** *Branch protection rules* (reglas de protección de ramas) activadas en `test` y `main` (requerir revisión de seguridad aprobada).

---

## 6. Formato de entrega
* **a. Repositorio:** GitHub o GitLab público (o con acceso otorgado al profesor).
* **b. Archivo README.md completo con:**
  * Instrucciones de setup del pipeline.
  * Cómo entrenaron el modelo (incluyendo el Notebook de Jupyter).
  * Capturas de pantalla y enlace al bot de Telegram.
  * Enlace al despliegue en producción.
* **c. Informe técnico:** En formato LaTeX (se adjunta el formato de informe correspondiente).
* **d. Exposición:** De 8 a 12 minutos mostrando:
  * Código vulnerable: rechazo automático del flujo.
  * Código seguro: flujo completo y exitoso hasta producción.

---

## 7. Fecha de entrega
📅 **Fecha límite:** 18 de junio de 2026, 23:59 horas.

> 🔴 **Nota importante:** Bajo ningún concepto se recibirán actividades fuera del plazo establecido. No se otorgarán prórrogas individuales ni se aceptarán entregas tardías por ningún medio. Es responsabilidad del estudiante gestionar oportunamente su trabajo y asegurar el cumplimiento del cronograma.

---

## 8. Criterios de Evaluación

| Criterio | Puntaje Máximo |
| :--- | :---: |
| Funcionalidad completa del pipeline (automatización total) | 6 puntos |
| Modelo de minería de datos propio y efectivo (prohibido LLM) | 6 puntos |
| Notificaciones Telegram/correo electrónico en todas las fases + issues automáticas | 3 puntos |
| Despliegue automático en proveedor gratuito y funcional | 3 puntos |
| Calidad del informe y documentación (README + notebook) | 2 puntos |
| **Total** | **20 puntos** |

### 🚨 Penalizaciones
* **a. Uso de LLM (incluso parcial):** -20 puntos (**Nota 0 automática**).
* **b. Pipeline no completamente automático:** -4 a -6 puntos.
* **c. Sin despliegue real:** -3 puntos.
* **d. Otras omisiones:** Penalización variable según el caso.
