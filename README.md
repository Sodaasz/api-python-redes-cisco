# TP N° 4 - Integrador - Redes de Computadoras (3643) - Grupo 01

Scripts de Python que interactúan con la API REST (Northbound API) del Network Controller de Packet Tracer.
Repositorio basado en el de la cátedra: [redes-computadoras/api-python-redes-cisco](https://github.com/redes-computadoras/api-python-redes-cisco).

## Requisitos

- Packet Tracer 9.0.1 abierto, con el archivo del TP y el Network Controller funcionando.
- La API se consulta en `http://localhost:58000/api/v1`.
- Python 3.10 o superior.

## Preparación

```
python -m venv cisco
cisco\Scripts\activate          # Windows  (Linux/Mac: source cisco/bin/activate)
pip install -r requirements.txt
```

El entorno virtual (`cisco/`) y los archivos `.env` **no** se suben al repositorio.

## Credenciales

Los scripts usan el usuario y la clave **del controlador** (no los de los equipos de red),
que son los registrados en la pantalla de inicio de sesión del Network Controller:
usuario `cisco` y clave `cisco123`.

Si el controlador tiene otras credenciales, hay que cambiarlas en `01_get-ticket.py`,
`02_get-network-device.py`, `04_tabulate.py` y `05_reporte_gestion.py`
(en este último también se pueden pasar por las variables de entorno `NC_USER` y `NC_PASS`).

## Scripts

| Script | Origen | Qué hace |
|---|---|---|
| `src/01_get-ticket.py` | Cátedra | `POST /ticket`: pide el ticket de autenticación (`X-Auth-Token`) y lo muestra. |
| `src/02_get-network-device.py` | Cátedra (modificado) | `GET /network-device`: lista hostname, plataforma e IP de gestión de los equipos. |
| `src/03_get-host.py` | Cátedra | `GET /host`: lista los hosts detectados con IP, MAC e interfaz de acceso. Requiere pegar un ticket vigente en el header `X-Auth-Token`. |
| `src/04_tabulate.py` | Cátedra (modificado) | Pide su propio ticket y muestra en tablas los equipos de red y los hosts. |
| `src/05_reporte_gestion.py` | **Grupo 01** | Script propio: verifica la gestión de la red desde el controlador y genera un reporte JSON. |

### Modificaciones a los scripts de la cátedra

El ISP está fuera del sistema autónomo y no tiene cargada la credencial en el controlador,
por lo que aparece con estado *Wrong credential* y **sin `hostname`** en `GET /network-device`.
Los scripts originales fallaban con `KeyError: 'hostname'` al llegar a ese equipo.
Se reemplazó el acceso `equipo["campo"]` por `equipo.get("campo", valor_por_defecto)` en
`02_get-network-device.py` y `04_tabulate.py`. En `02` además se pide el ticket de forma
automática y se muestra una tabla en lugar del JSON completo.

### Script propio: `05_reporte_gestion.py`

Compara los equipos que ve el controlador (`GET /network-device`) contra la lista de
equipos esperados de la topología (constante `ESPERADOS`, al inicio del script) y detecta:

- equipos esperados que **no aparecen** en el inventario,
- equipos que aparecen pero **no están en estado Managed**,
- equipos **fuera de la lista** (por ejemplo, el ISP),
- cantidad de **hosts por interfaz de acceso** (`GET /host`).

Muestra tablas por consola y guarda un reporte JSON con fecha y hora. Termina con código
de salida `0` si todo está gestionado, o `1` si falta algún equipo o alguno no está Managed.
Tolera equipos sin hostname.

```
python src/05_reporte_gestion.py                  # genera reporte_gestion.json
python src/05_reporte_gestion.py otro_nombre.json # nombre a elección
```

Variables de entorno opcionales: `NC_URL` (por defecto `http://localhost:58000/api/v1`),
`NC_USER` (por defecto `cisco`) y `NC_PASS`.

## Orden de ejecución sugerido

1. `python src/01_get-ticket.py`: copiar el ticket que muestra.
2. Pegar el ticket en el header `X-Auth-Token` de `src/03_get-host.py` y ejecutarlo.
3. `python src/02_get-network-device.py`
4. `python src/04_tabulate.py`
5. `python src/05_reporte_gestion.py`

Los tickets vencen al cerrar o reabrir Packet Tracer: si un script devuelve `403 invalid ticket`,
hay que pedir uno nuevo con el script 01.
