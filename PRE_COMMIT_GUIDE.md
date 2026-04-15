# Manual de Pre-commit hooks

Este proyecto utiliza pre-commit hooks para mantener la calidad y seguridad del código.

## Requisitos

Las herramientas ya están en `requirements.txt` (`bandit==1.8.3`, `pip-audit==2.10.0`). Solo necesitas instalar pre-commit:

```bash
pip install pre-commit
```

O si prefieres instalar todo desde el requirements.txt del proyecto:

```bash
cd SistemaRegistro
pip install -r requirements.txt
```

## Instalación

Una vez instaladas las dependencias, ejecuta:

```bash
pre-commit install
```

Esto configura los hooks para que se ejecuten automáticamente antes de cada commit.

## Uso básico

### Ejecutar todos los hooks manualmente

```bash
pre-commit run --all-files
```

### Ejecutar un hook específico

```bash
pre-commit run black
pre-commit run bandit
pre-commit run pip-audit
```

### Verificar hooks instalados

```bash
pre-commit hooks
```

### Saltar hooks en un commit (emergencias)

```bash
git commit --no-verify -m "Mensaje de emergencia"
```

---

## Descripción de hooks

| Hook | Propósito |
|------|------------|
| `check-yaml` | Valida archivos YAML |
| `end-of-file-fixer` | Elimina líneas vacías al final de archivos |
| `trailing-whitespace` | Elimina espacios en blanco innecesarios |
| `black` | Formatea código Python automáticamente |
| `detect-secrets` | Detecta secretos accidentalmente commitidos |
| `bandit` | Analiza código en busca de vulnerabilidades de seguridad |
| `pip-audit` | Verifica vulnerabilidades en dependencias pip |

---

## Comandos útiles

### Actualizar versiones de hooks

```bash
pre-commit autoupdate
```

### Depurar problemas

```bash
pre-commit run <hook-id> --show-stack-trace
```

### Limpiar cache de pre-commit

```bash
pre-commit clean
```

---

## Integración con CI/CD

Los hooks se ejecutan automáticamente en local. Para ejecutar en GitHub Actions, agrega un step en tu workflow:

```yaml
- name: Run pre-commit
  uses: pre-commit/action@v3.0.1
```

---

## Solución de problemas

### "Failed to run git hook"

Ejecuta:
```bash
pip install pre-commit
pre-commit install
```

### Hooks muy lentos en primer ejecución

Es normal en la primera ejecución. Los hooks se cachean automáticamente.

### Errores con detect-secrets

Si detect-secrets detecta falsos positivos, agrégalos al archivo `.secrets.baseline` o ajusta el hook en `.pre-commit-config.yaml`.
