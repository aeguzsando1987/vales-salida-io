"""
Autodiscovery de Permisos - Phase 2

Escanea automaticamente todas las rutas de FastAPI y pobla la tabla permissions
sin necesidad de escribir manualmente cada permiso.

Autor: E. Guzman
Fecha: 2025-11-06
"""

from typing import List, Dict, Set
from fastapi import FastAPI
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.shared.models.permission import Permission


def extract_entity_from_path(path: str) -> str:
    """
    Extrae el nombre de la entidad desde la ruta del endpoint.

    Ejemplos:
        /individuals/{id} -> "individuals"
        /companies/search -> "companies"
        /countries/states -> "countries"
        /admin/permissions -> "admin"

    Args:
        path: Ruta del endpoint (ej: "/individuals/{id}")

    Returns:
        Nombre de la entidad en plural
    """
    # Remover slashes iniciales y finales
    clean_path = path.strip("/")

    # Si la ruta esta vacia, retornar "root"
    if not clean_path:
        return "root"

    # Dividir por slash y tomar el primer segmento
    parts = clean_path.split("/")
    entity = parts[0]

    # Si el primer segmento es un parametro, tomar el segundo
    if entity.startswith("{") and len(parts) > 1:
        entity = parts[1]

    return entity


def infer_action_from_method_and_path(http_method: str, path: str) -> str:
    """
    Infiere la accion desde el metodo HTTP y la ruta.

    Reglas:
        GET /entities/ -> "list"
        GET /entities/{id} -> "get"
        GET /entities/search -> "search"
        POST /entities/ -> "create"
        PUT /entities/{id} -> "update"
        PATCH /entities/{id} -> "update"
        DELETE /entities/{id} -> "delete"

    Args:
        http_method: Metodo HTTP (GET, POST, PUT, PATCH, DELETE)
        path: Ruta del endpoint

    Returns:
        Nombre de la accion
    """
    method = http_method.upper()

    # Mapeo basico por metodo
    action_map = {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete"
    }

    if method in action_map:
        return action_map[method]

    # Para GET, inferir segun la ruta
    if method == "GET":
        # Si tiene parametro de ID, es "get"
        if "{id}" in path or "/{" in path:
            return "get"

        # Si tiene "search", "filter", "by-", es "search"
        if any(keyword in path for keyword in ["search", "filter", "by-", "enums"]):
            return "search"

        # Si termina en estadisticas, details, stats
        if any(keyword in path for keyword in ["statistics", "stats", "details", "overview"]):
            return "view_statistics"

        # Por defecto, es "list"
        return "list"

    return "unknown"


def discover_endpoints(app: FastAPI) -> List[Dict]:
    """
    Escanea todas las rutas registradas en la aplicacion FastAPI.

    Args:
        app: Instancia de FastAPI

    Returns:
        Lista de diccionarios con informacion de permisos:
        [
            {
                "entity": "individuals",
                "action": "list",
                "endpoint": "/individuals/",
                "http_method": "GET",
                "description": "List all individuals"
            },
            ...
        ]
    """
    discovered_permissions = []

    for route in app.routes:
        # Solo procesar rutas de API (APIRoute)
        if not isinstance(route, APIRoute):
            continue

        # Ignorar rutas de sistema
        if route.path.startswith("/docs") or route.path.startswith("/openapi") or route.path == "/":
            continue

        # Obtener el primer metodo HTTP (usualmente hay uno solo)
        if not route.methods:
            continue

        http_method = list(route.methods)[0]

        # Extraer entidad y accion
        entity = extract_entity_from_path(route.path)
        action = infer_action_from_method_and_path(http_method, route.path)

        # Obtener descripcion desde el docstring o nombre de la ruta
        description = route.summary or route.name or f"{action.title()} {entity}"

        # Crear registro de permiso
        permission_data = {
            "entity": entity,
            "action": action,
            "endpoint": route.path,
            "http_method": http_method,
            "description": description
        }

        discovered_permissions.append(permission_data)

    return discovered_permissions


def get_existing_permissions(db: Session) -> Set[tuple]:
    """
    Obtiene los permisos existentes en la base de datos.

    Args:
        db: Sesion de base de datos

    Returns:
        Set de tuplas (entity, action, http_method)
    """
    existing = db.query(Permission).filter(Permission.is_active == True).all()
    return {
        (p.entity, p.action, p.http_method)
        for p in existing
    }


def sync_permissions_to_db(discovered: List[Dict], db: Session, dry_run: bool = False) -> Dict:
    """
    Sincroniza los permisos descubiertos con la base de datos.

    Args:
        discovered: Lista de permisos descubiertos
        db: Sesion de base de datos
        dry_run: Si es True, solo muestra cambios sin aplicarlos

    Returns:
        Diccionario con estadisticas:
        {
            "new": 5,
            "existing": 20,
            "total_discovered": 25,
            "new_permissions": [...]
        }
    """
    # Obtener permisos existentes
    existing_keys = get_existing_permissions(db)

    new_permissions = []
    existing_count = 0

    for perm_data in discovered:
        key = (perm_data["entity"], perm_data["action"], perm_data["http_method"])

        if key in existing_keys:
            existing_count += 1
        else:
            # Nuevo permiso encontrado
            new_permissions.append(perm_data)

            if not dry_run:
                # Crear en base de datos
                new_perm = Permission(
                    entity=perm_data["entity"],
                    action=perm_data["action"],
                    endpoint=perm_data["endpoint"],
                    http_method=perm_data["http_method"],
                    description=perm_data["description"],
                    is_active=True
                )
                db.add(new_perm)

    if not dry_run and new_permissions:
        db.commit()

    return {
        "new": len(new_permissions),
        "existing": existing_count,
        "total_discovered": len(discovered),
        "new_permissions": new_permissions
    }


def autodiscover_and_sync(app: FastAPI, db: Session, dry_run: bool = False, auto_assign: bool = True) -> Dict:
    """
    Ejecuta el proceso completo de autodiscovery y sincronizacion.

    Args:
        app: Instancia de FastAPI
        db: Sesion de base de datos
        dry_run: Si es True, solo muestra cambios sin aplicarlos
        auto_assign: Si es True, asigna automáticamente permisos nuevos a roles

    Returns:
        Diccionario con estadisticas y permisos nuevos
    """
    print("Iniciando autodiscovery de permisos...")

    # Descubrir endpoints
    discovered = discover_endpoints(app)
    print(f"Endpoints descubiertos: {len(discovered)}")

    # Sincronizar con BD
    stats = sync_permissions_to_db(discovered, db, dry_run=dry_run)

    if dry_run:
        print("\n=== DRY RUN MODE ===")
        print(f"Permisos existentes: {stats['existing']}")
        print(f"Permisos nuevos encontrados: {stats['new']}")

        if stats['new_permissions']:
            print("\nPermisos que se agregarian:")
            for perm in stats['new_permissions']:
                print(f"  - {perm['entity']}:{perm['action']} ({perm['http_method']} {perm['endpoint']})")
    else:
        print(f"\nPermisos existentes: {stats['existing']}")
        print(f"Permisos nuevos agregados: {stats['new']}")

        if stats['new_permissions']:
            print("\nPermisos agregados:")
            for perm in stats['new_permissions']:
                print(f"  + {perm['entity']}:{perm['action']} ({perm['http_method']} {perm['endpoint']})")

    print("\nAutodiscovery completado.")

    # Auto-asignar permisos a roles si está habilitado
    if auto_assign:
        try:
            from app.shared.test_auto_assign_permissions import auto_assign_after_discovery
            stats = auto_assign_after_discovery(stats, db, dry_run=dry_run)
        except Exception as e:
            print(f"\nWARNING: Error en auto-asignacion: {e}")
            print("Los permisos fueron descubiertos pero no asignados a roles.")

    return stats
