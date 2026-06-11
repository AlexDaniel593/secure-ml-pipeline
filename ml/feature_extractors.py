"""Transformers personalizados del modelo de miner├¡a de datos.

Responsabilidad unica (SRP): definir las clases de feature extraction
usadas durante el entrenamiento y necesarias para deserializar el
``.joblib``. Cualquier l├│gica de predicci├│n vive en ``ml/predict.py``.

Estas clases son referenciadas por el pickle como ``__main__.CodeTokenizer``
(porque fueron definidas en el notebook). Para que ``joblib.load`` las
encuentre, ``ml/predict.py`` las importa y las inyecta en ``sys.modules['__main__']``.
"""

import ast
import io
import re
import tokenize as py_tokenize
from collections import Counter

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin


class CodeTokenizer(BaseEstimator, TransformerMixin):
    """Extrae tokens reales de Python usando el m├│dulo ``tokenize`` del stdlib."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [self._tokenize(c) for c in X]

    @staticmethod
    def _tokenize(code):
        tokens: list[str] = []
        try:
            gen = py_tokenize.generate_tokens(io.StringIO(str(code)).readline)
            for toknum, tokval, _, _, _ in gen:
                if toknum in (py_tokenize.NAME, py_tokenize.OP, py_tokenize.STRING, py_tokenize.NUMBER):
                    tokens.append(tokval.lower())
        except Exception:
            tokens = re.findall(r"[\w\.]+", str(code).lower())
        return " ".join(tokens)


class ASTFeatureExtractor(BaseEstimator, TransformerMixin):
    """22 features estructurales del AST de Python + log-profundidad."""

    NODES = [
        "Call", "Attribute", "Name", "Str", "Num", "FunctionDef", "ClassDef",
        "Import", "ImportFrom", "If", "For", "While", "Try", "ExceptHandler",
        "Return", "Assign", "AugAssign", "Compare", "BoolOp", "BinOp", "UnaryOp",
    ]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for code in X:
            row: list[int | float]
            try:
                tree = ast.parse(str(code))
                nc = Counter(n.__class__.__name__ for n in ast.walk(tree))
                row = [nc.get(t, 0) for t in self.NODES]

                def depth(n: ast.AST) -> int:
                    return 1 + max((depth(c) for c in ast.iter_child_nodes(n)), default=0)

                row.append(float(np.log1p(depth(tree))))
            except Exception:
                row = [0] * 22
            rows.append(row)
        return np.array(rows)


class SecurityPatternExtractor(BaseEstimator, TransformerMixin):
    """30 patrones DANGER + 15 SAFE + features derivadas."""

    DANGER = [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"compile\s*\(.*exec",
        r"\bsubprocess\.call\b.*shell\s*=\s*True",
        r"\bsubprocess\.run\b.*shell\s*=\s*True",
        r"\bsubprocess\.Popen\b.*shell\s*=\s*True",
        r"\bos\.system\s*\(",
        r"\bos\.popen\s*\(",
        r"pickle\.loads\b",
        r"marshal\.loads\b",
        r"yaml\.load\s*\([^)]*\)",
        r"render_template_string\b",
        r"__import__\s*\(",
        r"cursor\.execute\s*\([^?%]+\+",
        r"db\.query\s*\([^?%]+\+",
        r"db\.execute\s*\([^?%]+\+",
        r"(SELECT|INSERT|UPDATE|DELETE)\s+.{0,80}\+\s*[\w\'\"]",
        r"open\s*\([^)]*\+",
        r"hashlib\.(md5|sha1)\b",
        r"\brandom\.random\b",
        r"\brandom\.randint\b",
        r"getattr\s*\(.*,\s*[\w\'\"]",
        r"shell\s*=\s*True",
        r"html\s*=\s*[\'\"<].*\+",
        r"\.format\s*\(.*request",
        r"f[\'\"]{.*request",
        r"\+\s*user_input|user_input\s*\+",
        r"\+\s*request\.",
        r"ALLOWED_HOSTS\s*=\s*\[\s*[\'\"\*]",
        r"DEBUG\s*=\s*True",
    ]

    SAFE = [
        r"%s|\?|:param|:name|:\w+",
        r"\bparameterize\b|\bprepared\b",
        r"ast\.literal_eval\b",
        r"secrets\.",
        r"html\.escape\b",
        r"bleach\.clean\b",
        r"markupsafe",
        r"yaml\.safe_load\b",
        r"json\.loads\b",
        r"hashlib\.sha256\b|hashlib\.sha512\b",
        r"\bhmac\.",
        r"shell\s*=\s*False",
        r"subprocess\.check_output\b",
        r"re\.(match|fullmatch|search)\s*\([^)]*\^",
        r"startswith\s*\(.*base_dir|realpath",
    ]

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = []
        for code in X:
            s = str(code)
            d_flags = [int(bool(re.search(p, s, re.IGNORECASE | re.DOTALL))) for p in self.DANGER]
            s_flags = [int(bool(re.search(p, s, re.IGNORECASE))) for p in self.SAFE]
            n_d = sum(d_flags)
            n_s = sum(s_flags)
            row = d_flags + s_flags + [
                n_d,
                n_s,
                n_d - n_s,
                min(n_d / max(n_s, 1), 10),
                len(s),
                float(np.log1p(len(s))),
                s.count("\n"),
                int(bool(re.search(r"\btry\b", s))),
                int(bool(re.search(r"\bexcept\b", s))),
                len(re.findall(r"\bimport\b", s)),
                len(re.findall(r"\bdef\b", s)),
            ]
            rows.append(row)
        return np.array(rows)
