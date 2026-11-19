"""
05_reporte_gestion.py - Script propio (TP N° 4, actividad 4)

Verifica que el Network Controller esté gestionando todos los equipos de la
topología. Compara los equipos que ve el controlador (GET /network-device)
contra la lista de equipos esperados, y detecta:

  - equipos esperados que NO aparecen en el inventario,
  - equipos que aparecen pero no están en estado Managed (credencial incorrecta, etc.),
  - equipos inesperados (por ejemplo el ISP, que queda fuera del sistema autónomo),
  - cantidad de hosts detectados por interfaz de acceso (GET /host).

Guarda el resultado en un archivo JSON con fecha y hora, y devuelve un
código de salida distinto de 0 si falta algún equipo esperado o alguno
no está Managed (útil para automatizar la verificación).

Uso:
    python src/05_reporte_gestion.py
    python src/05_reporte_gestion.py reporte.json

Configuración opcional por variables de entorno (no se guardan claves en el repo):
    NC_URL   URL base de la API       (por defecto http://localhost:58000/api/v1)
    NC_USER  usuario del controlador  (por defecto cisco)
    NC_PASS  clave del controlador    (por defecto class)
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

import requests
from tabulate import tabulate

BASE_URI = os.environ.get("NC_URL", "http://localhost:58000/api/v1")
USUARIO = os.environ.get("NC_USER", "cisco")
CLAVE = os.environ.get("NC_PASS", "cisco123")
ARCHIVO = sys.argv[1] if len(sys.argv) > 1 else "reporte_gestion.json"

# Equipos que el controlador debería gestionar (routers y switches del sistema
# autónomo). Se compara por hostname. El ISP no va: queda fuera de la gestión.
ESPERADOS = [
    "R-Borde", "R-PisoA", "R-PisoB",
    "SW-EdifA", "SW-EdifB", "SW-Servidores",
    "SW-Svrs", "SW-PisoA", "SW-PisoB",
]

# Campos donde la API puede informar el estado de gestión de un equipo.
CAMPOS_ESTADO = ("collectionStatus", "reachabilityStatus", "managementState")


def pedir(metodo, ruta, **kwargs):
    resp = requests.request(metodo, BASE_URI + ruta, timeout=10, **kwargs)
    print("%s %s -> %s" % (metodo, ruta, resp.status_code))
    resp.raise_for_status()
    return resp.json()


def estado_de(equipo):
    """Devuelve el estado informado por el controlador, o 'sin dato'."""
    for campo in CAMPOS_ESTADO:
        valor = equipo.get(campo)
        if valor:
            return str(valor)
    return "sin dato"


def esta_managed(estado):
    return "managed" in estado.lower() or estado.lower() in ("reachable", "collected")


def main():
    try:
        cuerpo = json.dumps({"username": USUARIO, "password": CLAVE})
        ticket = pedir("POST", "/ticket", data=cuerpo,
                       headers={"Content-Type": "application/json"})["response"]["serviceTicket"]
        auth = {"X-Auth-Token": ticket}
        equipos = pedir("GET", "/network-device", headers=auth).get("response", [])
        hosts = pedir("GET", "/host", headers=auth).get("response", [])
    except requests.exceptions.ConnectionError:
        sys.exit("No se pudo conectar al controlador. ¿Está abierto Packet Tracer?")
    except requests.exceptions.HTTPError as e:
        sys.exit("El controlador devolvió un error: %s" % e)

    # --- Análisis de equipos -------------------------------------------------
    inventario = []
    for e in equipos:
        inventario.append({
            "hostname": e.get("hostname") or "(sin hostname)",
            "ip": e.get("managementIpAddress", ""),
            "modelo": e.get("platformId", ""),
            "estado": estado_de(e),
        })

    vistos = {d["hostname"] for d in inventario}
    faltantes = sorted(set(ESPERADOS) - vistos)
    inesperados = sorted(vistos - set(ESPERADOS))
    no_managed = [d for d in inventario
                  if d["hostname"] in ESPERADOS and not esta_managed(d["estado"])]

    # --- Hosts por interfaz --------------------------------------------------
    por_interfaz = Counter(h.get("connectedInterfaceName") or "sin dato" for h in hosts)

    # --- Salida por consola --------------------------------------------------
    print()
    print(tabulate([[d["hostname"], d["ip"], d["modelo"], d["estado"]] for d in inventario],
                   headers=["Equipo", "IP de gestión", "Modelo", "Estado"], tablefmt="rst"))
    print()
    print("Equipos esperados: %d | vistos por el controlador: %d" % (len(ESPERADOS), len(equipos)))
    print("Faltan en el inventario :", ", ".join(faltantes) or "ninguno")
    print("No Managed              :", ", ".join(d["hostname"] for d in no_managed) or "ninguno")
    print("Fuera de la lista (esperable: ISP):", ", ".join(inesperados) or "ninguno")
    print()
    if por_interfaz:
        print(tabulate(sorted(por_interfaz.items()), headers=["Interfaz", "Hosts"], tablefmt="rst"))
    print("Hosts detectados: %d" % len(hosts))

    # --- Reporte JSON --------------------------------------------------------
    reporte = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "resumen": {
            "esperados": len(ESPERADOS),
            "vistos": len(equipos),
            "faltantes": faltantes,
            "no_managed": [d["hostname"] for d in no_managed],
            "inesperados": inesperados,
            "hosts": len(hosts),
        },
        "equipos": inventario,
        "hosts_por_interfaz": dict(por_interfaz),
    }
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    print("\nReporte guardado en '%s'" % ARCHIVO)

    ok = not faltantes and not no_managed
    print("Resultado:", "TODO GESTIONADO" if ok else "HAY EQUIPOS SIN GESTIONAR")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
