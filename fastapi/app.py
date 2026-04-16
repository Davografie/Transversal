from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - line %(lineno)d - %(message)s')
stream_handler = logging.StreamHandler()

class ColorFormatter(logging.Formatter):
	def format(self, record):
		CYAN = "\033[1;96m"
		BLUE = "\033[94m"
		YELLOW = "\033[93m"
		ORANGE = "\033[93m"
		RESET = "\033[0m"

		if record.levelname == "INFO":
			COLOR = CYAN
		elif record.levelname == "DEBUG":
			COLOR = BLUE
		elif record.levelname == "WARNING":
			COLOR = YELLOW
		elif record.levelname == "ERROR":
			COLOR = ORANGE
		else:
			COLOR = RESET
		original_msg = super().format(record)
		# Only color the actual message part
		if record.msg:
			msg_str = str(record.getMessage())
			colored_msg = f"{COLOR}{msg_str}{RESET}"
			# Replace only the message part in the formatted string
			return original_msg.replace(msg_str, colored_msg, 1)
		return original_msg

log_formatter = ColorFormatter(
	"%(asctime)s [%(levelname)s] %(name)s/%(funcName)s(%(lineno)d): %(message)s",
	datefmt="%Y-%m-%d %H:%M:%S"
)

stream_handler.setFormatter(log_formatter)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logger.addHandler(stream_handler)

logger.info("Starting server")

app = FastAPI()

dicepools = []

class ConnectionManager:
	def __init__(self):
		self.active_connections: Dict[str, str|WebSocket] = {}

	async def connect(self, websocket: WebSocket, player_key: str, session_id: str):
		await websocket.accept()

		self.active_connections[session_id] = {}
		self.active_connections[session_id]['player_key'] = player_key
		self.active_connections[session_id]['session_id'] = session_id
		self.active_connections[session_id]['websocket'] = websocket

		logger.info(f"Connected player: {player_key}")
		await self.broadcast({
			"player_key": player_key,
			"session_id": session_id,
			"type": "player_connected"
		})

		try:
			while True:
				data = await websocket.receive_json()
				logger.debug(f"Received data from player: {player_key}\n\t{data}")
				# await self.broadcast(data, player_key, session_id)
				match data['type']:
					case "hello_world":
						await self.broadcast(data)
					case "dicepool":
						await self.broadcast({
							"player_key": player_key,
							"session_id": session_id,
							**data
						})
					case "engage":
						await self.broadcast(data)
		except WebSocketDisconnect:
			logger.info(f"Disconnected player: {player_key}")
			del self.active_connections[session_id]
			await self.broadcast({"type": "player_disconnected"})
	
	# def set_dicepool(self, player_key: str, session_id: str, dicepool: dict):
	# 	global dicepools
	# 	new_dicepool = {
	# 		"player": {
				
	# 		}
	# 	}
	
	async def broadcast(self, message: Dict[str, str]):
		"""
		Send message to all other active connections
		"""
		logger.debug(f"Broadcasting message to sessions {self.active_connections.keys()}")
		for session_id in self.active_connections.keys():
			await self.active_connections[session_id]['websocket'].send_json(message)
			
manager = ConnectionManager()

# example endpoint url: ws://localhost:8000/ws/123
@app.websocket("/ws/{player_key}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, player_key: str, session_id: str):
	await manager.connect(websocket, player_key, session_id)
	

		