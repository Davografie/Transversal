"""
	Game logic and database connections
"""
from enum import Enum
import os

# https://docs.python-arango.com/en/main/
from arango import ArangoClient
ARANGO_HOST = "tv_adb"
ARANGO_PORT = "8529"
ARANGO_USERNAME = "root"
ARANGO_PASSWORD = os.environ["ARANGO_ROOT_PASSWORD"]
ARANGO_DB = "transversal"

class SessionPhase(Enum):
	START = 0
	MIDDLE = 1
	END = 2

class Trigger(Enum):
	DIRECT = 0
	DICEPOOL_END = 1
	BEAT_END = 2
	SCENE_END = 3
	SESSION_END = 4
	CHANGE_LOCATION = 5

client = ArangoClient(hosts=f"http://{ARANGO_HOST}:{ARANGO_PORT}")
db = client.db(
	ARANGO_DB,
	username=ARANGO_USERNAME,
	password=ARANGO_PASSWORD
)
print("Transversal ArangoDB connection established")

class Session:
	players = [] # active players in this session
	entities = [] # entities in this session that have temporary stat changes
	# queues = [] # [{ trigger: string, target: string, description: string }]
	# end_of_session_queue = [] # a reference to entities and functions to execute at end of session
	def __init__(self):
		self.phase = SessionPhase.START
	def start_playing(self):
		self.phase = SessionPhase.MIDDLE
	def end_session(self):
		self.phase = SessionPhase.END
		# for queue_item in self.end_of_session_queue:
		# 	queue_item[0](queue_item[1]) # execute function queue_item[0] with arguments queue_item[1]

class Dicepool:
	resolutions = [] # [{ player: ID, dice: Die[], effect: Trait }]
	def add_resolution(self, resolution):
		self.resolutions.append(resolution)
	def get_winner(self):
		return max(self.resolutions, key=lambda r: r.result)
	def clear_resolutions(self):
		self.resolutions = []

class Node:
	id = ""
	key = ""
	revision = 0
	def __init__(self, id, collection):
		self.doc = db.collection(collection).get(id)
		self.id = self.doc['_id']
		self.key = self.doc['_key']

class Player:
	"""user stored in the client session and cookie"""
	id = ""
	revision = 0
	character = lambda: Character()
	def __init__(self, id=None):
		self.id = id

class Entity(Node):
	name = ""
	description = ""
	traitsets = []
	def __init__(self, id):
		print("(001) initializing entity: ", id)
		super().__init__(id, 'Entities')
		self.name = self.doc['name']
		self.description = self.doc['description']

class Character(Entity):
	player = lambda: Player()
	location = lambda: Location()
	sfxs = [] # special abilities of a character regardless of traits
	highest_complication = 0 # gets added to session log at end of session

class Location(Entity):
	location = lambda: Location()
	sfxs = [] # ways in which characters can interact with the location
	transversable = [] # list of locations the characters can reach from here
	characters = [] # list of characters in this location
	assets = [] # list of assets in this location

def retrieve_hierarchy(location_id):
	query = f"""FOR v, e, p IN 0..20 OUTBOUND "{ location_id }" Relations
				FILTER p.edges[*].type ALL == 'super'
				RETURN v"""
	cursor = db.aql.execute(query)
	return [doc for doc in cursor]

class Asset(Entity):
	"""Complex asset, can be vehicles, weapons, etc."""
	sfxs = [] # special effects this asset can activate regardless of traits
	traits = []

class Traitset:
	id = ""
	name = ""
	limit = 0
	sfxs = [] # special effects that affect this traitset
	traits = [] # all traits grouped under this traitset

class Trait:
	id = ""
	revision = 0
	statement = ""
	name = ""
	sfxs = [] # special effects that affect this trait
	rating = []

class SFX:
	description = ""
	effects = [] # [{ trigger: string, target: string, description: string }]

class Effect:
	target = ""
	trigger = ""
	description = ""
