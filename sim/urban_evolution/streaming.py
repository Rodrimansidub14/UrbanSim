"""
StreamServer - Servidor WebSocket para transmitir el estado de la simulación
y recibir comandos de control en tiempo real.
"""
import asyncio
import json
import time
import websockets
from typing import Set, Optional
import numpy as np


class StreamServer:
    """
    Servidor WebSocket que transmite el estado de la simulación a los clientes conectados
    y procesa los comandos de control entrantes.
    """

    def __init__(self, model, host="localhost", port=8765):
        self.model = model
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = False

    async def start(self):
        """Iniciar el servidor WebSocket"""
        self.server = await websockets.serve(
            self.handle_client, self.host, self.port
        )
        self.running = True
        print(f"Servidor StreamServer escuchando en ws://{self.host}:{self.port}")

    async def stop(self):
        """Detener el servidor WebSocket"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # Cerrar todas las conexiones de clientes
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )
        print("Servidor StreamServer detenido")

    async def handle_client(self, websocket):
        """Manejar una nueva conexión de cliente"""
        self.clients.add(websocket)
        client_id = id(websocket)
        print(f"Cliente {client_id} conectado (total: {len(self.clients)})")

        try:
            # Enviar estado inicial
            await self.send_initial_state(websocket)

            # Escuchar mensajes entrantes
            async for message in websocket:
                await self.process_command(message, websocket)

        except websockets.exceptions.ConnectionClosed:
            print(f"Cliente {client_id} desconectado")
        finally:
            self.clients.discard(websocket)

    async def send_initial_state(self, websocket):
        """Enviar el estado actual de la simulación a un cliente recién conectado"""
        state = self._build_state_message()
        await websocket.send(json.dumps(state))

    async def process_command(self, message: str, websocket):
        """Procesar comandos de control recibidos desde los clientes"""
        try:
            cmd = json.loads(message)
            command_type = cmd.get("command")

            if command_type == "update_param":
                param = cmd.get("param")
                value = cmd.get("value")
                self._update_parameter(param, value)
                response = {
                    "status": "ok",
                    "message": f"Parámetro actualizado: {param} = {value}"
                }

            elif command_type == "set_policy":
                policy = cmd.get("policy")
                payload = cmd.get("payload", {})
                self._apply_policy(policy, payload)
                response = {
                    "status": "ok",
                    "message": f"Política aplicada: {policy}"
                }

            elif command_type == "pause":
                # Requiere coordinación con el bucle de simulación
                response = {"status": "ok", "message": "Pausa solicitada"}

            elif command_type == "resume":
                response = {"status": "ok", "message": "Reanudación solicitada"}

            elif command_type == "get_state":
                response = self._build_state_message()

            else:
                response = {
                    "status": "error",
                    "message": f"Comando desconocido: {command_type}"
                }

            await websocket.send(json.dumps(response))

        except json.JSONDecodeError as e:
            error_msg = {"status": "error", "message": f"JSON inválido: {str(e)}"}
            await websocket.send(json.dumps(error_msg))
        except Exception as e:
            error_msg = {"status": "error", "message": f"Error: {str(e)}"}
            await websocket.send(json.dumps(error_msg))

    def _update_parameter(self, param: str, value):
        """Actualizar un parámetro del modelo dinámicamente"""
        if param == "rent_cap":
            self.model.rent_cap_monthly = float(value)
        elif param == "aff_share":
            self.model.current_affordable_share = float(value)
        elif param == "voucher_discount":
            self.model.voucher_discount = float(value)
        elif param == "vacancy_penalty":
            self.model.vacancy_penalty = float(value)
        else:
            print(f"Parámetro desconocido: {param}")

    def _apply_policy(self, policy: str, payload: dict):
        """Aplicar una política al modelo"""
        from . import policies as policies_mod
        policies_mod.apply_policy(self.model, policy, payload)

    def _build_state_message(self) -> dict:
        """Construir un mensaje completo de estado con KPIs y datos espaciales"""
        # Obtener las métricas más recientes
        if self.model.records:
            latest = self.model.records[-1]
        else:
            latest = {
                "step": 0,
                "avg_rent": 0,
                "avg_travel": 0,
                "share_low_income": 0,
                "gentr_dispersion": 0,
                "displacements": 0,
                "vacancy_rate": 0,
                "aff_units": 0,
                "mkt_units": 0,
                "total_units": 0,
            }

        # Obtener las cuadrículas espaciales
        grids = self.model.spatial_grids()

        # Convertir arreglos de numpy a listas para serialización JSON
        spatial_data = {
            key: arr.tolist() if isinstance(arr, np.ndarray) else arr
            for key, arr in grids.items()
        }

        return {
            "type": "state_update",
            "step": self.model.step,
            "timestamp": time.time(),
            "kpis": {
                "step": self.model.step,
                "avg_rent": float(latest["avg_rent"]),
                "avg_travel": float(latest["avg_travel"]),
                "share_low_income": float(latest["share_low_income"]),
                "gentr_dispersion": float(latest["gentr_dispersion"]),
                "displacements": int(latest["displacements"]),
                "vacancy_rate": float(latest["vacancy_rate"]),
                "aff_units": int(latest["aff_units"]),
                "mkt_units": int(latest["mkt_units"]),
                "params": {
                    "rent_cap": float(self.model.rent_cap_monthly if self.model.rent_cap_monthly is not None else 0.99),
                    "aff_share": float(getattr(self.model, 'current_affordable_share', 0.3)),
                    "voucher_discount": float(getattr(self.model, 'voucher_discount', 0.0)),
                },
                "total_units": int(latest["total_units"]),
            },
            "spatial": spatial_data,
            "params": {
                "rent_cap_monthly": self.model.rent_cap_monthly,
                "affordable_share": self.model.current_affordable_share,
                "voucher_discount": self.model.voucher_discount,
                "vacancy_penalty": self.model.vacancy_penalty,
            }
        }

    async def broadcast_tick(self):
        """Transmitir el estado actual a todos los clientes conectados"""
        if not self.clients:
            return

        message = self._build_state_message()
        message_str = json.dumps(message)

        # Enviar a todos los clientes de forma concurrente
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients],
            return_exceptions=True
        )

    async def broadcast_message(self, message: dict):
        """Transmitir un mensaje personalizado a todos los clientes"""
        if not self.clients:
            return

        message_str = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients],
            return_exceptions=True
        )
