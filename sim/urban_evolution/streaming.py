"""
StreamServer - WebSocket server for broadcasting simulation state
and receiving control commands in real-time.
"""
import asyncio
import json
import time
import websockets
from typing import Set, Optional
import numpy as np


class StreamServer:
    """
    WebSocket server that broadcasts simulation state to connected clients
    and processes incoming control commands.
    """

    def __init__(self, model, host="localhost", port=8765):
        self.model = model
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.running = False

    async def start(self):
        """Start the WebSocket server"""
        self.server = await websockets.serve(
            self.handle_client, self.host, self.port
        )
        self.running = True
        print(f"🌐 StreamServer listening on ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop the WebSocket server"""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )
        print("🛑 StreamServer stopped")

    async def handle_client(self, websocket):
        """Handle a new client connection"""
        self.clients.add(websocket)
        client_id = id(websocket)
        print(f"✅ Client {client_id} connected (total: {len(self.clients)})")

        try:
            # Send initial state
            await self.send_initial_state(websocket)

            # Listen for incoming messages
            async for message in websocket:
                await self.process_command(message, websocket)

        except websockets.exceptions.ConnectionClosed:
            print(f"❌ Client {client_id} disconnected")
        finally:
            self.clients.discard(websocket)

    async def send_initial_state(self, websocket):
        """Send current simulation state to a newly connected client"""
        state = self._build_state_message()
        await websocket.send(json.dumps(state))

    async def process_command(self, message: str, websocket):
        """Process incoming control commands from clients"""
        try:
            cmd = json.loads(message)
            command_type = cmd.get("command")

            if command_type == "update_param":
                param = cmd.get("param")
                value = cmd.get("value")
                self._update_parameter(param, value)
                response = {
                    "status": "ok",
                    "message": f"Updated {param} to {value}"
                }

            elif command_type == "set_policy":
                policy = cmd.get("policy")
                payload = cmd.get("payload", {})
                self._apply_policy(policy, payload)
                response = {
                    "status": "ok",
                    "message": f"Applied policy: {policy}"
                }

            elif command_type == "pause":
                # This would require coordination with the simulation loop
                response = {"status": "ok", "message": "Pause requested"}

            elif command_type == "resume":
                response = {"status": "ok", "message": "Resume requested"}

            elif command_type == "get_state":
                response = self._build_state_message()

            else:
                response = {
                    "status": "error",
                    "message": f"Unknown command: {command_type}"
                }

            await websocket.send(json.dumps(response))

        except json.JSONDecodeError as e:
            error_msg = {"status": "error", "message": f"Invalid JSON: {str(e)}"}
            await websocket.send(json.dumps(error_msg))
        except Exception as e:
            error_msg = {"status": "error", "message": f"Error: {str(e)}"}
            await websocket.send(json.dumps(error_msg))

    def _update_parameter(self, param: str, value):
        """Update a model parameter dynamically"""
        if param == "rent_cap":
            self.model.rent_cap_monthly = float(value)
        elif param == "aff_share":
            self.model.current_affordable_share = float(value)
        elif param == "voucher_discount":
            self.model.voucher_discount = float(value)
        elif param == "vacancy_penalty":
            self.model.vacancy_penalty = float(value)
        else:
            print(f"⚠️  Unknown parameter: {param}")

    def _apply_policy(self, policy: str, payload: dict):
        """Apply a policy to the model"""
        from . import policies as policies_mod
        policies_mod.apply_policy(self.model, policy, payload)

    def _build_state_message(self) -> dict:
        """Build a complete state message with KPIs and spatial data"""
        # Get latest metrics
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

        # Get spatial grids
        grids = self.model.spatial_grids()

        # Convert numpy arrays to lists for JSON serialization
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
        """Broadcast current state to all connected clients"""
        if not self.clients:
            return

        message = self._build_state_message()
        message_str = json.dumps(message)

        # Send to all clients concurrently
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients],
            return_exceptions=True
        )

    async def broadcast_message(self, message: dict):
        """Broadcast a custom message to all clients"""
        if not self.clients:
            return

        message_str = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_str) for client in self.clients],
            return_exceptions=True
        )
