"""Inferencia del modelo de miner├¡a de datos sobre diffs de un PR.

Responsabilidad ├║nica (SRP): dado un diff unificado o un snippet de
c├│digo, cargar el ``.joblib`` y devolver un veredicto JSON con la
clasificaci├│n por archivo y agregada.

Uso:
    python -m ml.predict --diff path/al/diff.patch
    python -m ml.predict --code "eval(request.args['x'])"
    cat diff.patch | python -m ml.predict --diff -

Codigos de salida:
    0  SEGURO
    2  VULNERABLE
    3  Error de procesamiento
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")
warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")
warnings.filterwarnings("ignore", category=FutureWarning, module="xgboost")

import __main__  # noqa: E402

from ml.feature_extractors import (  # noqa: E402
    ASTFeatureExtractor,
    CodeTokenizer,
    SecurityPatternExtractor,
)

__main__.CodeTokenizer = CodeTokenizer
__main__.ASTFeatureExtractor = ASTFeatureExtractor
__main__.SecurityPatternExtractor = SecurityPatternExtractor

import joblib  # noqa: E402
from lime.lime_text import LimeTextExplainer  # noqa: E402

MODEL_PATH = Path(__file__).parent / "modelo_seguridad.joblib"
SUPPORTED_EXTS = {".py"}
EXIT_OK = 0
EXIT_VULNERABLE = 2
EXIT_ERROR = 3


@dataclass
class FileVerdict:
    path: str
    label: str
    proba: float
    added_lines: int
    lime_explanation: list[dict[str, str]] | None = None


@dataclass
class OverallVerdict:
    label: str
    proba: float


@dataclass
class Prediction:
    overall: OverallVerdict
    files: list[FileVerdict]
    supported_files: int
    skipped_files: int
    summary: str


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modelo no encontrado: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


def parse_diff(diff_text: str) -> list[tuple[str, list[str]]]:
    """Divide un diff unificado en ``[(path, [lineas_anadidas, ...]), ...]``."""
    files: list[tuple[str, list[str]]] = []
    current_path: str | None = None
    current_lines: list[str] = []

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            if current_path is not None:
                files.append((current_path, current_lines))
            current_path = None
            current_lines = []
            match = re.match(r"diff --git a/(.+?) b/(.+?)$", raw_line)
            if match:
                current_path = match.group(2)
            continue

        if raw_line.startswith("+++ "):
            path = raw_line[4:].strip().split("\t", 1)[0]
            if path.startswith("b/"):
                path = path[2:]
            if path != "/dev/null":
                current_path = path
            continue

        if raw_line.startswith("--- "):
            continue

        if raw_line.startswith("@@"):
            continue

        if current_path is None:
            continue

        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            current_lines.append(raw_line[1:])

    if current_path is not None:
        files.append((current_path, current_lines))

    return files


def filter_supported(files: list[tuple[str, list[str]]]) -> tuple[list[tuple[str, list[str]]], int]:
    supported: list[tuple[str, list[str]]] = []
    skipped = 0
    for path, lines in files:
        ext = os.path.splitext(path)[1].lower()
        if ext in SUPPORTED_EXTS and lines:
            supported.append((path, lines))
        else:
            skipped += 1
    return supported, skipped


def predict_file(model, path: str, lines: list[str]) -> FileVerdict:
    code = "\n".join(lines)
    proba_vec = model.predict_proba([code])[0]
    vuln_idx = list(model.classes_).index(1) if 1 in model.classes_ else int(probable_vuln_index(model))
    vuln_proba = float(proba_vec[vuln_idx])
    label = "VULNERABLE" if vuln_proba >= 0.5 else "SEGURO"
    return FileVerdict(path=path, label=label, proba=round(vuln_proba, 4), added_lines=len(lines))


def probable_vuln_index(model) -> int:
    classes = list(model.classes_)
    return int(max(range(len(classes)), key=lambda i: classes[i]))


def generate_lime_explanation(model, code: str, num_features: int = 10) -> list[dict[str, str]]:
    """Genera una explicación LIME para el código dado."""
    try:
        explainer = LimeTextExplainer(class_names=["SEGURO", "VULNERABLE"])
        explanation = explainer.explain_instance(
            code,
            model.predict_proba,
            num_features=num_features,
            labels=[1],
        )
        return [
            {"token": token, "weight": f"{weight:.4f}"}
            for token, weight in explanation.as_list(label=1)
        ]
    except Exception:
        return []


def predict_file(model, path: str, lines: list[str]) -> FileVerdict:
    code = "\n".join(lines)
    proba_vec = model.predict_proba([code])[0]
    vuln_idx = list(model.classes_).index(1) if 1 in model.classes_ else int(probable_vuln_index(model))
    vuln_proba = float(proba_vec[vuln_idx])
    label = "VULNERABLE" if vuln_proba >= 0.5 else "SEGURO"
    
    lime_explanation = None
    if label == "VULNERABLE":
        lime_explanation = generate_lime_explanation(model, code)
    
    return FileVerdict(
        path=path,
        label=label,
        proba=round(vuln_proba, 4),
        added_lines=len(lines),
        lime_explanation=lime_explanation,
    )


def aggregate(file_verdicts: list[FileVerdict]) -> OverallVerdict:
    if not file_verdicts:
        return OverallVerdict(label="SEGURO", proba=0.0)
    vuln_probas = [f.proba for f in file_verdicts if f.label == "VULNERABLE"]
    max_proba = max(vuln_probas, default=0.0)
    label = "VULNERABLE" if vuln_probas else "SEGURO"
    return OverallVerdict(label=label, proba=round(max_proba, 4))


def predict_diff(model, diff_text: str) -> Prediction:
    all_files = parse_diff(diff_text)
    supported, skipped = filter_supported(all_files)

    file_verdicts = [predict_file(model, path, lines) for path, lines in supported]
    overall = aggregate(file_verdicts)
    summary = (
        f"{sum(1 for f in file_verdicts if f.label == 'VULNERABLE')}/"
        f"{len(file_verdicts)} archivos vulnerables"
    )
    return Prediction(
        overall=overall,
        files=file_verdicts,
        supported_files=len(supported),
        skipped_files=skipped,
        summary=summary,
    )


def predict_code(model, code: str) -> Prediction:
    verdict = predict_file(model, "<ad-hoc>", code.splitlines() or [""])
    overall = OverallVerdict(label=verdict.label, proba=verdict.proba)
    return Prediction(
        overall=overall,
        files=[verdict],
        supported_files=1,
        skipped_files=0,
        summary=f"1/1 archivos vulnerables" if verdict.label == "VULNERABLE" else "0/1 archivos vulnerables",
    )


def to_json(payload: Prediction) -> str:
    return json.dumps(asdict(payload), indent=2, ensure_ascii=False)


def read_input(args: argparse.Namespace) -> tuple[str, bool]:
    if args.diff == "-":
        return sys.stdin.read(), True
    if args.diff:
        return Path(args.diff).read_text(encoding="utf-8"), True
    if args.code:
        return args.code, False
    raise SystemExit("Debe proporcionar --diff o --code")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clasificador de c├│digo seguro/vulnerable")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--diff", help="Ruta a un diff unificado, o '-' para stdin")
    group.add_argument("--code", help="Snippet de c├│digo a clasificar directamente")
    parser.add_argument("--model", default=str(MODEL_PATH), help="Ruta al .joblib (opcional)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    text, is_diff = read_input(args)
    model = load_model() if args.model == str(MODEL_PATH) else joblib.load(args.model)

    try:
        result = predict_diff(model, text) if is_diff else predict_code(model, text)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return EXIT_ERROR

    print(to_json(result))
    return EXIT_VULNERABLE if result.overall.label == "VULNERABLE" else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
