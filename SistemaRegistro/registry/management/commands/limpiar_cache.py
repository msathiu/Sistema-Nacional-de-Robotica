"""
Comando de gestión para limpiar cache y archivos temporales del sistema.
"""
import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Limpia cache de Python, pytest, coverage y archivos temporales"

    def add_arguments(self, parser):
        parser.add_argument(
            "--todo",
            action="store_true",
            help="Incluye staticfiles y media (usar con precaución)",
        )

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        todo = options["todo"]

        # Patrones a limpiar
        patterns = [
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/.pytest_cache",
            "**/.coverage",
            "**/htmlcov",
            "**/*.log",
            "**/.DS_Store",
            "**/Thumbs.db",
        ]

        if todo:
            patterns.extend(
                [
                    "staticfiles",
                    "media",
                ]
            )

        deleted_count = 0

        for pattern in patterns:
            if "**/" in pattern:
                # Búsqueda recursiva
                for path in Path(base_dir).rglob(pattern.replace("**/", "")):
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                            self.stdout.write(f"🗑️  Eliminado directorio: {path}")
                        else:
                            path.unlink()
                            self.stdout.write(f"🗑️  Eliminado archivo: {path}")
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  No se pudo eliminar {path}: {e}")
                        )
            else:
                # Directorio específico en la raíz
                path = base_dir / pattern
                if path.exists():
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                            self.stdout.write(f"🗑️  Eliminado directorio: {path}")
                        else:
                            path.unlink()
                            self.stdout.write(f"🗑️  Eliminado archivo: {path}")
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  No se pudo eliminar {path}: {e}")
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Limpieza completada. {deleted_count} elementos eliminados."
            )
        )
