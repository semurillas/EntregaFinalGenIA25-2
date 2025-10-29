# herramientas_ecomarket.py (MODIFICADO para usar strings)
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime, timedelta
import json
import re

# --- BASES DE DATOS DE ECOMARKET (FIJAS) ---
# ... (PRODUCTOS_DB y PEDIDOS_DB se mantienen iguales)
PRODUCTOS_DB = {
    "cepillo de bambú": {"retornable": False, "sku": "3001"},
    "pasta dental ecológica": {"retornable": False, "sku": "3002"},
    "toalla orgánica": {"retornable": False, "sku": "3003"},
    "botella ecológica": {"retornable": True, "sku": "3004"},
    "bolsas reutilizables": {"retornable": True, "sku": "3005"},
    "detergente natural": {"retornable": False, "sku": "3006"},
    "jabón orgánico": {"retornable": False, "sku": "3007"},
    "desodorante ecológico": {"retornable": False, "sku": "3008"},
    "esponja vegetal": {"retornable": False, "sku": "3009"},
    "shampoo sólido": {"retornable": False, "sku": "3010"},
    "acondicionador sólido": {"retornable": False, "sku": "3011"},
    "hilo dental natural": {"retornable": False, "sku": "3012"},
    "bálsamo labial": {"retornable": False, "sku": "3013"},
    "toallas de algodón orgánico": {"retornable": False, "sku": "3014"},
    "set de limpieza ecológica": {"retornable": True, "sku": "3015"},
    "paquete de pajillas reutilizables": {"retornable": True, "sku": "3016"},
    "crema hidratante natural": {"retornable": False, "sku": "3017"},
}

PEDIDOS_DB = {
    "P-1001": {"status": "En preparación", "date": "2025-09-25", "productos": ["Cepillo de bambú", "Pasta dental ecológica", "Toalla orgánica"], "nro_id": "10204578", "nombre_cliente": "Juan Pérez"},
    "P-1002": {"status": "Enviado", "date": "2025-09-24", "productos": ["Botella ecológica", "Bolsas reutilizables"], "nro_id": "20305689", "nombre_cliente": "Ana Gómez"},
    "P-1003": {"status": "Entregado", "date": "2025-10-20", "productos": ["bolsas reutilizables"], "nro_id": "30406790", "nombre_cliente": "Luis Rojas"},
    "P-1004": {"status": "Cancelado", "date": "", "productos": ["Detergente natural"], "nro_id": "40507812", "nombre_cliente": "Marta Díaz"},
    "P-1005": {"status": "Enviado", "date": "2025-09-26", "productos": ["Jabón orgánico", "Shampoo sólido", "Crema hidratante natural", "Cepillo de bambú", "Desodorante ecológico"], "nro_id": "50608923", "nombre_cliente": "Pedro Ramírez"},
    "P-1006": {"status": "En preparación", "date": "2025-09-27", "productos": ["Desodorante ecológico", "Jabón orgánico"], "nro_id": "60709034", "nombre_cliente": "Sofía Herrera"},
    "P-1007": {"status": "Entregado", "date": "2025-10-23", "productos": ["paquete de pajillas reutilizables", "Pasta dental ecológica", "bolsas reutilizables"], "nro_id": "30406790", "nombre_cliente": "Luis Rojas"}, 
    "P-1008": {"status": "Entregado", "date": "2025-09-19", "productos": ["Toallas de algodón orgánico", "Shampoo sólido", "Acondicionador sólido"], "nro_id": "80902356", "nombre_cliente": "Laura Torres"},
    "P-1009": {"status": "En preparación", "date": "2025-09-28", "productos": ["Paquete de pajillas reutilizables", "Botella ecológica"], "nro_id": "90103467", "nombre_cliente": "Daniela Gómez"},
    "P-1010": {"status": "Entregado", "date": "2025-09-24", "productos": ["Set de limpieza ecológica"], "nro_id": "11204578", "nombre_cliente": "Carlos Ruiz"},
}
# ---------------------------------------------

def verificar_elegibilidad_devolucion(id_referencia: str) -> Dict[str, Any]:
    """
    Verifica (simulado) la elegibilidad de un pedido completo. Recibe el ID del pedido 
    O el nro_id del cliente como string.
    """
    # ... (El cuerpo de esta función se mantiene igual)
    id_referencia = str(id_referencia).strip()
    
    if not id_referencia:
        return {"success": False, "elegible": False, "razon": "Falta el ID del pedido (P-XXXX) o el número de identificación del cliente (8 dígitos).", "productos_retornables": [], "id_devolucion": None}

    # 1. Búsqueda y Filtrado de Pedidos Entregados
    pedidos_entregados_candidatos = {}
    
    if id_referencia.upper().startswith('P-'):
        # Búsqueda por ID de Pedido (solo un pedido)
        pedido_info = PEDIDOS_DB.get(id_referencia.upper())
        if pedido_info:
            pedidos_entregados_candidatos[id_referencia.upper()] = pedido_info
    elif re.match(r'^\d{8}$', id_referencia):
        # Búsqueda por nro_id y filtrado inicial (solo 'Entregado')
        for id_pedido, info in PEDIDOS_DB.items():
            if info.get('nro_id') == id_referencia and "entregado" in info.get('status', '').lower():
                pedidos_entregados_candidatos[id_pedido] = info
    else:
        return {"success": False, "elegible": False, "razon": "Formato de referencia inválido. Debe ser ID de pedido (P-XXXX) o nro_id (8 dígitos).", "productos_retornables": [], "id_devolucion": None}

    if not pedidos_entregados_candidatos:
        return {"success": True, "elegible": False, "razon": f"No se encontró un pedido 'Entregado' asociado a la referencia '{id_referencia}'.", "productos_retornables": [], "id_devolucion": None}

    # 2. Selección del Último Pedido Entregado
    pedido_seleccionado = None
    id_pedido_seleccionado = None
    fecha_mas_reciente = datetime.min
    
    for id_pedido, info in pedidos_entregados_candidatos.items():
        try:
            fecha_entrega = datetime.strptime(info["date"], '%Y-%m-%d')
            
            fecha_limite = fecha_entrega + timedelta(days=30)
            hoy = datetime.now()

            if hoy <= fecha_limite:
                if fecha_entrega > fecha_mas_reciente:
                    fecha_mas_reciente = fecha_entrega
                    pedido_seleccionado = info
                    id_pedido_seleccionado = id_pedido
            
        except ValueError:
            continue 

    if not pedido_seleccionado:
        return {"success": True, "elegible": False, "razon": "Se encontraron pedidos entregados, pero todos han excedido el plazo de 30 días para devolución.", "productos_retornables": [], "id_devolucion": None}


    # 3. Validación de Plazo
    fecha_entrega_str = pedido_seleccionado["date"]
    try:
        fecha_entrega = datetime.strptime(fecha_entrega_str, '%Y-%m-%d')
        fecha_limite = fecha_entrega + timedelta(days=30)
        hoy = datetime.now()
        
        if hoy > fecha_limite:
            return {"success": True, "elegible": False, "razon": f"El pedido {id_pedido_seleccionado} fue el último entregado, pero el plazo de 30 días ha expirado (límite: {fecha_limite.strftime('%Y-%m-%d')}).", "productos_retornables": [], "id_devolucion": None}
    except:
        return {"success": True, "elegible": False, "razon": "Error al procesar la fecha de entrega del pedido seleccionado.", "productos_retornables": [], "id_devolucion": None}


    # 4. Determinar Productos Retornables
    productos_retornables = []
    
    for producto_nombre_raw in pedido_seleccionado["productos"]:
        nombre_producto_norm = producto_nombre_raw.lower().strip()
        
        producto_info = PRODUCTOS_DB.get(nombre_producto_norm)
        if not producto_info:
            producto_info = next((info for name, info in PRODUCTOS_DB.items() 
                                 if nombre_producto_norm in name or name in nombre_producto_norm), None)
        
        if producto_info and producto_info["retornable"]:
            productos_retornables.append(producto_nombre_raw)
    
    # 5. Elegible Final
    if not productos_retornables:
        return {"success": True, "elegible": False, "razon": f"El pedido {id_pedido_seleccionado} es válido, pero ninguno de los productos contenidos es retornable según nuestra política.", "productos_retornables": [], "id_devolucion": None}
    
    id_dev = f"DEV-{uuid.uuid4()}"[:20]
    razon_final = f"El pedido {id_pedido_seleccionado} de {pedido_seleccionado['nombre_cliente']} es elegible. Los siguientes productos son aptos para devolución: {', '.join(productos_retornables)}."
    
    return {
        "success": True, 
        "elegible": True, 
        "razon": razon_final, 
        "productos_retornables": productos_retornables,
        "id_pedido": id_pedido_seleccionado,
        "nro_id": pedido_seleccionado["nro_id"],
        "nombre_cliente": pedido_seleccionado["nombre_cliente"],
        "id_devolucion": id_dev
    }


def generar_etiqueta_devolucion(id_devolucion: str, direccion_origen: str) -> Dict[str, Any]:
    """
    Genera una etiqueta de devolución. Recibe el id_devolucion y la direccion_origen como strings.
    """
    id_dev = id_devolucion.strip()
    direccion = direccion_origen.strip()
    
    if not id_dev:
        return {"success": False, "url_etiqueta": None, "tracking_id": None, "mensaje": "Falta id_devolucion"}
    
    if not direccion or len(direccion) < 5:
        return {"success": False, "url_etiqueta": None, "tracking_id": None, "mensaje": "La dirección de origen es inválida o incompleta. Por favor, solicite una dirección completa."}

    tracking = f"TRK-{id_dev[4:12]}"
    url = f"https://ecomarket.com/etiquetas/{id_dev}.pdf"
    
    return {"success": True, "url_etiqueta": url, "tracking_id": tracking, "mensaje": f"Etiqueta generada. El tracking es {tracking}. El PDF de la etiqueta se ha enviado al cliente (URL simulada: {url})."}


def procesar_reembolso(id_devolucion: str) -> Dict[str, Any]:
    """
    Inicia el proceso de reembolso. Recibe el id_devolucion como string.
    """
    id_dev = id_devolucion.strip()
    
    if not id_dev:
        return {"success": False, "mensaje": "Falta id_devolucion para procesar el reembolso."}
    
    # Simulación de error o éxito
    if id_dev.endswith("-ERROR"): 
        return {"success": False, "mensaje": f"Error: No se pudo conectar con la pasarela de pagos para el ID {id_dev}. Intente más tarde."}
    
    return {"success": True, "mensaje": f"Reembolso procesado. El monto correspondiente a la devolución {id_dev} se ha iniciado y se reflejará en la cuenta del cliente en 3-5 días hábiles."}