"""
Exportación de reportes tabulares (Excel / CSV) con validación estricta de formato.

Seguridad:
- Solo se admiten formatos de la lista blanca (xlsx, csv).
- Nombres de archivo generados en servidor (sin entrada del usuario directa).
- Celdas CSV: mitigación básica de inyección de fórmulas (=, +, -, @, tab, CR).
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any, Optional, Sequence

import pandas as pd
from django.http import HttpResponse

ALLOWED_EXPORT_FORMATS = frozenset({"xlsx", "csv"})


def parse_export_format(request) -> Optional[str]:
    """
    Lee ?format= de la querystring.

    Returns:
        None: no se indicó formato → mostrar pantalla de elección Excel/CSV.
        "xlsx" | "csv": formato válido.
    Raises:
        ValueError: valor no permitido (el caller puede devolver 400).
    """
    raw = request.GET.get("format")
    if raw is None or str(raw).strip() == "":
        return None
    v = str(raw).strip().lower()
    if v in ("excel", "xlsx", "xls"):
        return "xlsx"
    if v == "csv":
        return "csv"
    raise ValueError("formato_invalido")


def safe_export_filename_base(name: str, max_len: int = 80) -> str:
    """Base de nombre de archivo: solo caracteres seguros para sistemas de archivos."""
    s = re.sub(r"[^\w\-. ]", "_", name, flags=re.UNICODE)
    s = "_".join(s.split())
    s = (s[:max_len] or "export").strip("._- ")
    return s or "export"


def csv_formula_safe_cell(value: Any) -> str:
    """
    Reduce riesgo de CSV injection al abrir en Excel/LibreOffice
    (celdas que empiezan por =, +, -, @, tab, CR).
    """
    if value is None:
        return ""
    s = str(value)
    if not s:
        return ""
    if s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def dataframe_to_response(
    df: pd.DataFrame,
    filename_base: str,
    fmt: str,
) -> HttpResponse:
    """
    Serializa un DataFrame a Excel (.xlsx) o CSV (.csv) según fmt ∈ {xlsx, csv}.
    """
    if fmt not in ALLOWED_EXPORT_FORMATS:
        raise ValueError("fmt inválido")
    base = safe_export_filename_base(filename_base)

    if fmt == "xlsx":
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{base}.xlsx"'
        df.to_excel(response, index=False, engine="openpyxl")
        return response

    df = df.copy()
    buf = io.StringIO()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(
                lambda x: csv_formula_safe_cell(x) if pd.notna(x) else ""
            )
    df.to_csv(buf, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
    response = HttpResponse(
        "\ufeff" + buf.getvalue(),
        content_type="text/csv; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{base}.csv"'
    return response


def rows_to_dataframe(
    headers: Sequence[str], rows: Sequence[Sequence[Any]]
) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=list(headers))


def rows_to_response(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    filename_base: str,
    fmt: str,
) -> HttpResponse:
    df = rows_to_dataframe(headers, rows)
    return dataframe_to_response(df, filename_base, fmt)


def dict_rows_to_response(
    records: Sequence[dict],
    filename_base: str,
    fmt: str,
) -> HttpResponse:
    if not records:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame.from_records(records)
    return dataframe_to_response(df, filename_base, fmt)
