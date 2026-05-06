# Quickstart

Esta guía asume que ya tienes Python 3.10+ y pip instalados.

## Instalación

```bash
pip install datos-mexico
```

Para uso en notebooks Jupyter:

```bash
pip install datos-mexico jupyter
```

## Primer ejemplo

```python
from datos_mexico import DatosMexico

client = DatosMexico()

# Obtener KPIs de servidores públicos de la Ciudad de México
stats = client.cdmx.dashboard_stats()

print(f"Total: {stats['totalServidores']:,} servidores")
print(f"Sueldo medio: ${stats['avgSalary']:,.2f} MXN mensuales")
print(f"Sueldo mediano: ${stats['medianSalary']:,.2f} MXN mensuales")
```

## Manejo de errores

```python
from datos_mexico import DatosMexico
from datos_mexico.exceptions import DatosMexicoError, ApiError

client = DatosMexico()

try:
    stats = client.cdmx.dashboard_stats()
except ApiError as e:
    print(f"Error de API: {e.status_code} — {e.endpoint}")
except DatosMexicoError as e:
    print(f"Error: {e}")
```

## Próximos pasos

- Explora los datasets en los notebooks de [examples/](../examples/)
- Lee la API completa en [docs/api/](api/)
- Si encuentras errores en datos, reportarlo en [errores@datosmexico.org](mailto:errores@datosmexico.org)
