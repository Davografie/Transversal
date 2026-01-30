"""
	Flask and GraphQL endpoints
"""
from uuid import uuid4
import pandas as pd
import datetime
import random
import json

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import shutil
import math
import re
from PIL import Image

# https://github.com/graphql-python/graphql-server/blob/master/docs/flask.md
from graphql_server.flask import GraphQLView

# https://docs.graphene-python.org/en/latest/
from graphene import Interface, ObjectType, InputObjectType, Mutation, Field, ID, String, Int, Boolean, Schema, List, JSONString

# https://docs.python-arango.com/en/main/
from arango import ArangoClient

import redis

import transversal as tv
from imagegen import generate_image

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - line %(lineno)d - %(message)s')
stream_handler = logging.StreamHandler()

class ColorFormatter(logging.Formatter):
	def format(self, record):
		# ANSI escape code for bright cyan
		CYAN = "\033[96m"
		RESET = "\033[0m"
		original_msg = super().format(record)
		# Only color the actual message part
		if record.msg:
			msg_str = str(record.getMessage())
			colored_msg = f"{CYAN}{msg_str}{RESET}"
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

app.config['UPLOAD_FOLDER'] = '/media/uploads'
app.config['IMAGEN_FOLDER'] = '/media/imagens'
app.config['T2I_MODELS_FOLDER'] = '/media/ComfyUI/models'

arango_host = "tv_adb"
arango_port = "8529"
arango_username = "root"
arango_password = os.environ.get("ARANGO_ROOT_PASSWORD")
arango_db = "transversal"

r = redis.Redis(host='redis', port=6379)
logger.info(f"Redis connection established.")

# session variables
dicepool_limit = -1
result_limit = 2
effect_limit = 1

session_characters = []
# {
# 	"player": player ID,
# 	"character": entity ID
# }

session_rev = uuid4()
scene_rev = uuid4()
beat_rev = uuid4()
resolutions_rev = uuid4()
resolutions = []
complication_pool = []
RATINGS = {
	'd4': {'value': 4},
	'd6': {'value': 6},
	'd8': {'value': 8},
	'd10': {'value': 10},
	'd12': {'value': 12},
}

session = tv.Session()

# GraphQL API

client = ArangoClient(hosts=f"http://{arango_host}:{arango_port}")
db = client.db(
	arango_db,
	username=arango_username,
	password=arango_password
)
logger.info("ArangoDB connection established")


def get_doc_by_id(collection_name: str, doc_id: str):
	"""
	Helper function to get a document by ID from a collection and store it in Redis.
	@param collection_name: Name of the collection
	@param doc_id: ID of the document
	@return: Document data
	"""
	# first check if the doc is in redis
	# throw an exception if doc_id is convertible to a number
	if isinstance(doc_id, (int, float)) or (isinstance(doc_id, str) and re.fullmatch(r'[+-]?\d+(\.\d+)?', doc_id.strip())):
		raise Exception("doc_id must not be a bare numeric value; provide a full Arango document id like 'Collection/123'")
	if r.exists(doc_id):
		stored = r.hgetall(doc_id)
		doc = deserialize_doc(stored)
	else:
		doc = db.collection(collection_name).get(doc_id)
		doc = {k: v for k, v in doc.items() if v is not None}
		serialized = serialize_doc(doc)
		r.hset(doc_id, mapping=serialized)
	return doc

def update_doc(collection_name: str, doc: dict, temp=False):
	"""
	Helper function to update a document in a collection and update it in Redis.
	@param collection_name: Name of the collection
	@param doc: Document data
	@return: Updated document data
	"""
	if not temp:
		db_doc = { k: v for k, v in doc.items() if not (k.startswith('_rev') or k.startswith('_key')) }
		# check if database is busy writing
		# logger.log("DATABASE STATUS ::::::: ", db.status())
		# while db.status():
		# 	pass
		try:
			db.status()
		except:
			logger.info("Database is busy writing. Retrying...")
		finally:
			pass
			# logger.info("Database is not busy writing.")
		db.collection(collection_name).update(db_doc)

	serialized = serialize_doc(doc)
	r.hset(doc.get('_id'), mapping=serialized)

	return doc

def serialize_doc(doc):
	serialized = {}
	for k, v in doc.items():
		if isinstance(v, (list, bool)):
			serialized[k] = json.dumps(v)
		else:
			serialized[k] = str(v)
	return serialized

def deserialize_doc(stored):
	doc = {}
	for k, v in stored.items():
		try:
			doc[k.decode('utf-8')] = json.loads(v.decode('utf-8'))
		except json.JSONDecodeError:
			doc[k.decode('utf-8')] = v.decode('utf-8')
			# logger.info(f"JSONDecodeError: {k.decode('utf-8')}: {v.decode('utf-8')}")
	return doc


def filter_trait_settings_by_location(trait_settings, location_id):
	"""
	Systematically filters out traits restricted by the location hierarchy.

	Args:
		trait_settings (list): A list of ArangoDB trait setting (TraitSettings) documents.
		location_id (str): The ID of the location to be used for filtering.

	Returns:
		list: Filtered list of trait settings.
	"""
	result = []
	# logger.info(f"filter_trait_settings_by_location:\n\ttrait_settings: {[trait_setting.get('_id') for trait_setting in trait_settings]}")
	hierarchy_ids = [location.get('_id') for location in retrieve_hierarchy(location_id)]
	# logger.info(f"filter_trait_settings_by_location:\n\thierarchy_ids: {hierarchy_ids}")
	for trait_setting in trait_settings:
		# logger.info(f"filter_trait_settings_by_location:\n\tProcessing trait setting: {trait_setting.get('_id')}")
		determined = False
		for location_id in hierarchy_ids:
			# logger.info(f"filter_trait_settings_by_location:\n\tChecking location_id {location_id} in enabled locations")
			if trait_setting.get('locations_enabled') and location_id in trait_setting.get('locations_enabled'):
				result.append(trait_setting)
				determined = True
				# logger.info("filter_trait_settings_by_location:\n\tTrait setting enabled at this location, added to result")
				break
			elif trait_setting.get('locations_disabled') and location_id in trait_setting.get('locations_disabled'):
				determined = True
				# logger.info("filter_trait_settings_by_location:\n\tTrait setting disabled at this location, not added")
				break
		if not determined and trait_setting.get('_to') is not None and trait_setting.get('_to') != 'Traits/1':
			# logger.info("filter_trait_settings_by_location:\n\tChecking default trait setting")
			default_trait_setting = db.collection('TraitSettings').find({ '_from': trait_setting.get('_to'), '_to': 'Traits/1' })
			if not default_trait_setting.empty():
				default_trait_setting = [doc for doc in default_trait_setting][0]
				for location_id in hierarchy_ids:
					# logger.info(f"filter_trait_settings_by_location:\n\tChecking location_id {location_id} in default enabled locations")
					if default_trait_setting.get('locations_enabled') and location_id in default_trait_setting.get('locations_enabled'):
						result.append(trait_setting)
						determined = True
						# logger.info("filter_trait_settings_by_location:\n\tDefault trait setting enabled, added to result")
						break
					elif default_trait_setting.get('locations_disabled') and location_id in default_trait_setting.get('locations_disabled'):
						determined = True
						# logger.info("filter_trait_settings_by_location:\n\tDefault trait setting disabled, not added")
						break
		if not determined and trait_setting.get('_from') is not None and not trait_setting.get('_from').startswith('Traitsets'):
			# logger.info("filter_trait_settings_by_location:\n\tChecking traitset default setting")
			traitset_id = get_doc_by_id('Traits', trait_setting.get('_to')).get('traitset')
			traitset_setting = db.collection('TraitSettings').find({ '_from': traitset_id, '_to': 'Traits/1' })
			if not traitset_setting.empty():
				traitset_setting = [doc for doc in traitset_setting][0]
				for location_id in hierarchy_ids:
					# logger.info(f"filter_trait_settings_by_location:\n\tChecking location_id {location_id} in traitset enabled locations")
					if traitset_setting.get('locations_enabled') and location_id in traitset_setting.get('locations_enabled'):
						result.append(trait_setting)
						determined = True
						# logger.info("filter_trait_settings_by_location:\n\tTraitset default setting enabled, added to result")
						break
					elif traitset_setting.get('locations_disabled') and location_id in traitset_setting.get('locations_disabled'):
						determined = True
						# logger.info("filter_trait_settings_by_location:\n\tTraitset default setting disabled, not added")
						break
		if not determined:
			result.append(trait_setting)
			# logger.info("filter_trait_settings_by_location:\n\tNo location restrictions, added trait setting to result")
			# logger.info(f"filter_trait_settings_by_location:\n\tNo location restrictions, ignoring trait setting")
			# break
	return result

def retrieve_location(entity):
	"""
	Retrieves the location of an entity.

	Args:
		entity (dict): The entity to retrieve the location for.

	Returns:
		dict: The location of the entity.
	"""
	if entity.get('type') != 'location':
		# if the entity is not a location, get the location from its location attribute
		location_id = entity.get('location')
		location = get_doc_by_id('Entities', location_id)
		if location.get('type') != 'location':
			# if the location is not a location, get the location from its location attribute
			location = retrieve_location(location)
	elif entity.get('_id') != 'Entities/2':
		# if the entity is a location, get the location from its super relations
		location_id = [doc.get('_to') for doc in db.collection('Relations').find({ '_from': entity.get('_id'), 'type': 'super' })][0]
		location = get_doc_by_id('Entities', location_id)
	else:
		location = entity
	return location

def retrieve_hierarchy(location_id):
	"""
	Retrieves the hierarchy of a location.

	Args:
		location_id (str): The ID of the location to retrieve the hierarchy for.

	Returns:
		list: A list of dictionaries representing the hierarchy of the location, where index 0 is the location itself and index 1 is its parent.
	"""
	query = f"""FOR v, e, p IN 0..20 OUTBOUND "{ location_id }" Relations
				FILTER p.edges[*].type ALL == 'super'
				RETURN v"""
	cursor = db.aql.execute(query)
	return [doc for doc in cursor]



class Player(ObjectType):
	uuid = ID()
	id = ID()
	name = String()
	is_gm = Boolean()
	character = Field(lambda: Character)
	entities = List(lambda: Entity)

	@classmethod
	def _hydrate_player(cls, parent, info):
		if parent.id is not None:
			player = get_doc_by_id('Players', parent.id)
			parent.name = player.get('name')

	def resolve_name(parent, info):
		if parent.name is None:
			Player._hydrate_player(parent, info)
		return parent.name

	def resolve_character(parent, info):
		global session_characters
		for character in session_characters:
			if character.get('player') == parent.id:
				return Character(id=character.get('character'))

	def resolve_entities(parent, info):
		relations = db.collection('Relations').find({ '_from': parent.id, 'type': 'agency' })
		# for every entity, get the entity and check the type to make sure to return the proper object
		for relation in relations:
			entity = get_doc_by_id('Entities', relation.get('_to'))
			if entity.get('type') == 'character':
				yield Character(id=entity.get('_id'))
			elif entity.get('type') == 'npc':
				yield NPC(id=entity.get('_id'))
			elif entity.get('type') == 'asset':
				yield Asset(id=entity.get('_id'))
			elif entity.get('type') == 'faction':
				yield Faction(id=entity.get('_id'))
			elif entity.get('type') == 'location':
				yield Location(id=entity.get('_id'))

class CreatePlayer(Mutation):
	class Arguments:
		name = String(required=True)
	
	player = Field(lambda: Player)
	
	def mutate(self, info, name):
		player = db.collection('Players').insert({ 'name': name })
		return CreatePlayer(player=Player(id=player.get('_id'), name=name))

class DeletePlayer(Mutation):
	class Arguments:
		player_id = ID(required=True)
	
	message = String()
	
	def mutate(self, info, player_id):
		# remove all player relations
		relations = db.collection('Relations').find({ '_from': player_id, 'type': 'agency' })
		for relation in relations:
			db.collection('Relations').delete({ '_id': relation.get('_id') })
		db.collection('Players').delete({ '_id': player_id })
		return DeletePlayer(message='Player deleted')

class ActivateEntity(Mutation):
	class Arguments:
		player_id = ID(required=True)
		entity_id = ID(required=True)
	
	player = Field(lambda: Player)
	
	def mutate(self, info, player_id, entity_id):
		# check if agency relation exists
		if db.collection('Relations').find({ '_from': player_id, '_to': entity_id, 'type': 'agency' }).empty():
			db.collection('Relations').insert({ '_from': player_id, '_to': entity_id, 'type': 'agency' })
		
		# activate entity for player
		global session_characters
		# first, check if the player ID is registered in session_characters
		if not any(char['player'] == player_id for char in session_characters):
			session_characters.append({ 'player': player_id, 'character': entity_id })
		# if player ID is in session_characters, update the character
		else:
			for char in session_characters:
				if char['player'] == player_id:
					# deactivate the previous character
					if char['character'] is not None:
						character_doc = get_doc_by_id('Entities', str(char['character']))
						character_doc['active'] = False
						update_doc('Entities', character_doc)
					char['character'] = entity_id
		# activate the character in ADB
		entity_doc = get_doc_by_id('Entities', entity_id)
		entity_doc['active'] = True
		update_doc('Entities', entity_doc)
		return ActivateEntity(player=Player(id=player_id))
	


class Dicepool(ObjectType):
	dice = List(JSONString)
	phase = String()
	player = Field(lambda: Player)

class Session(ObjectType):
	dicepool_limit = Int()
	result_limit = Int()
	effect_limit = Int()
	session = String()
	scene = String()
	beat = String()
	characters = List(lambda: Character)
	dicepools = List(lambda: Dicepool)

	def resolve_dicepool_limit(parent, info):
		global dicepool_limit
		return dicepool_limit

	def resolve_result_limit(parent, info):
		return result_limit

	def resolve_effect_limit(parent, info):
		return effect_limit

	def resolve_session(parent, info):
		return session_rev

	def resolve_scene(parent, info):
		return scene_rev

	def resolve_beat(parent, info):
		return beat_rev

	def resolve_characters(parent, info):
		return [Character(id='Entities/' + str(char.get('character'))) for char in session_characters]

	def resolve_dicepools(parent, info):
		return [Dicepool(
			dice=resolution.get('dice'),
			phase=resolution.get('phase'),
			player=Player(uuid=resolution.get('player').get('uuid'))
		) for resolution in resolutions]

class SessionInput(InputObjectType):
	dicepool_limit = Int()
	result_limit = Int()
	effect_limit = Int()
	new_session = Boolean()
	next_scene = Boolean()
	next_beat = Boolean()

class UpdateSession(Mutation):
	class Arguments:
		session_input = SessionInput(required=True)

	message = String()
	session = Field(lambda: Session)

	def mutate(self, info, session_input):
		global session_characters
		global dicepool_limit
		global session_rev, scene_rev, beat_rev
		global resolutions, resolutions_rev
		dicepool_limit = session_input.dicepool_limit
		
		if session_input.new_session:
			session_rev = uuid4()
			session_characters = []

			active_entities = db.collection('Entities').find({'active': True})
			for entity in active_entities:
				entity['active'] = False
				update_doc('Entities', entity)

			stuck_on_imagening = db.collection('Entities').find({'imagening': True})
			for entity in stuck_on_imagening:
				entity['imagening'] = False
				update_doc('Entities', entity)
			
			# clear the redis database
			r.flushdb()

		if session_input.new_session or session_input.next_scene:
			scene_rev = uuid4()
			
			active_entities = db.collection('Entities').find({'active': True, 'type': 'npc'})
			for entity in active_entities:
				entity['active'] = False
				update_doc('Entities', entity)

		if session_input.new_session or session_input.next_scene or session_input.next_beat:
			beat_rev = uuid4()
			resolutions = []
			resolutions_rev = uuid4()

		return UpdateSession(message="Session updated", session=Session(
			dicepool_limit=dicepool_limit,
			result_limit=result_limit,
			effect_limit=effect_limit
		))


class SFX(ObjectType):
	id = ID()
	name = String()
	description = String()
	traits = List(lambda: Trait)

	def resolve_name(parent, info):
		return get_doc_by_id('SFXs', parent.id)['name']

	def resolve_description(parent, info):
		return get_doc_by_id('SFXs', parent.id)['description']

	def resolve_traits(parent, info):
		query = f"""FOR trait IN Traits
			FILTER '{ parent.id }' IN trait.possible_sfxs
			RETURN trait"""
		cursor = db.aql.execute(query)
		return [Trait(id=doc.get('_id')) for doc in cursor]

class CreateSFX(Mutation):
	class Arguments:
		name = String(required=True)
		description = String(required=True)

	sfx = Field(lambda: SFX)

	def mutate(self, info, name, description):
		sfx = db.collection('SFXs').insert({
			'name': name,
			'description': description
		})
		return CreateSFX(sfx=SFX(id=sfx.get('id'), name=name, description=description))

class UpdateSFX(Mutation):
	class Arguments:
		id = ID(required=True)
		name = String()
		description = String()

	sfx = Field(lambda: SFX)

	def mutate(self, info, id, name=None, description=None):
		sfx = get_doc_by_id('SFXs', id)
		if name:
			sfx['name'] = name
		if description:
			sfx['description'] = description
		update_doc('SFXs', sfx)
		return UpdateSFX(sfx=SFX(id=id, name=name, description=description))

class DeleteSFX(Mutation):
	class Arguments:
		id = ID(required=True)

	success = Boolean()
	message = String()

	def mutate(self, info, id):
		try:
			# Remove SFX as possible from all Traits
			query = f"""FOR trait IN Traits
				FILTER '{ id }' IN trait.possible_sfxs
				RETURN trait"""
			results = db.aql.execute(query)
			for result in results:
				new_sfxs = result.get('possible_sfxs')
				new_sfxs.remove(id)
				update_doc('Traits', result, {'possible_sfxs': new_sfxs})
			# Remove SFX from all TraitSettings
			query = f"""FOR ts IN TraitSettings
				FILTER '{ id }' IN ts.sfxs
				RETURN ts"""
			results = db.aql.execute(query)
			for result in results:
				new_sfxs = result.get('sfxs')
				new_sfxs.remove(id)
				update_doc('TraitSettings', result, {'sfxs': new_sfxs})
			db.collection('SFXs').delete(id)
			return DeleteSFX(success=True, message="SFX deleted")
		except Exception as e:
			return DeleteSFX(success=False, message=f"DeleteSFX failed: {str(e)}")


absolute_default_trait_setting = {
	'rating_type': 'empty',
	'rating': [],
	'locations_enabled': [],
	'locations_disabled': [],
	'sfxs': []
}

class TraitSetting(ObjectType):
	id = ID()
	trait = Field(lambda: Trait)
	from_entity = Field(lambda: Entity)
	to_entity = Field(lambda: Entity)
	statement = String()
	notes = String()
	rating_type = String()
	rating = List(String)
	scaling = Int()
	locations_enabled = List(String)
	locations_disabled = List(String)
	sfxs = List(lambda: SFX)
	sfxs_ids = List(String)
	known_to = List(lambda: Character) # characters who have learned about this trait
	hidden = Boolean()
	priority = Int()

	@classmethod
	def _hydrate_traitsetting(cls, parent, info):
		if parent.id:
			traitsetting = get_doc_by_id('TraitSettings', parent.id)
			parent.statement = traitsetting.get('statement')
			parent.notes = traitsetting.get('notes')
			parent.rating_type = traitsetting.get('rating_type')
			parent.rating = traitsetting.get('rating')
			parent.scaling = traitsetting.get('scaling')
			parent.locations_enabled = traitsetting.get('locations_enabled')
			parent.locations_disabled = traitsetting.get('locations_disabled')
			parent.sfxs_ids = traitsetting.get('sfxs')
			parent.hidden = traitsetting.get('hidden')

	def resolve_trait(parent, info):
		if parent.trait:
			return parent.trait
		elif parent.id:
			return Trait(id=get_doc_by_id('TraitSettings', parent.id).get('_to'))
		else:
			return None

	def resolve_from_entity(parent, info):
		if parent.from_entity and parent.from_entity.id is not None:
			return parent.from_entity
		elif parent.id:
			entity_id = get_doc_by_id('TraitSettings', parent.id).get('_from')
			if entity_id.startswith('Entities/'):
				entity_type = get_doc_by_id('Entities', entity_id).get('type')
				if entity_type == 'character':
					return Character(id=entity_id)
				elif entity_type in ['npc', 'gm']:
					return NPC(id=entity_id)
				elif entity_type == 'asset':
					return Asset(id=entity_id)
				elif entity_type == 'location':
					return Location(id=entity_id)
				elif entity_type == 'faction':
					return Faction(id=entity_id)
			elif entity_id.startswith('Relations/'):
				entity_id = get_doc_by_id('Relations', entity_id).get('_from')
				if entity_id.startswith('Entities/'):
					entity_type = get_doc_by_id('Entities', entity_id).get('type')
					if entity_type in ['character', 'gm']:
						return Character(id=entity_id)
					elif entity_type == 'npc':
						return NPC(id=entity_id)
					elif entity_type == 'asset':
						return Asset(id=entity_id)
					elif entity_type == 'location':
						return Location(id=entity_id)
					elif entity_type == 'faction':
						return Faction(id=entity_id)
			else:
				return None
		else:
			return None
	
	def resolve_to_entity(parent, info):
		# only for relation traits
		if parent.to_entity and parent.to_entity.id is not None:
			return parent.to_entity
		elif parent.id:
			relation_id = get_doc_by_id('TraitSettings', parent.id).get('_from')
			if relation_id.startswith('Relations/'):
				entity_id = get_doc_by_id('Relations', relation_id).get('_to')
				if entity_id.startswith('Entities/'):
					entity_type = get_doc_by_id('Entities', entity_id).get('type')
					if entity_type in ['character', 'gm']:
						return Character(id=entity_id)
					elif entity_type == 'npc':
						return NPC(id=entity_id)
					elif entity_type == 'asset':
						return Asset(id=entity_id)
					elif entity_type == 'location':
						return Location(id=entity_id)
					elif entity_type == 'faction':
						return Faction(id=entity_id)
			else:
				return None
		else:
			return None

	def resolve_statement(parent, info):
		if parent.statement:
			return parent.statement
		if parent.id:
			return get_doc_by_id('TraitSettings', parent.id).get('statement')
		else:
			return None

	def resolve_notes(parent, info):
		if parent.notes:
			return parent.notes
		elif parent.id:
			return get_doc_by_id('TraitSettings', parent.id).get('notes')
		else:
			return None

	def resolve_rating_type(parent, info):
		if parent.rating_type:
			return parent.rating_type
		if parent.id:
			return get_doc_by_id('TraitSettings', parent.id).get('rating_type')
		else:
			return None

	def resolve_rating(parent, info):
		if parent.rating != None:
			return parent.rating
		if parent.id:
			return get_doc_by_id('TraitSettings', parent.id).get('rating')
		else:
			return None

	def resolve_scaling(parent, info):
		if parent.scaling is None:
			TraitSetting._hydrate_traitsetting(parent, info)
		return parent.scaling

	def resolve_locations_enabled(parent, info):
		# logger.info(f"\nresolve_locations_enabled:\tparent:\n{parent}")
		if parent.locations_enabled is not None:
			return parent.locations_enabled
		if parent.id:
			return get_doc_by_id('TraitSettings', parent.id).get('locations_enabled')
		else:
			return None
		
	def resolve_locations_disabled(parent, info):
		if parent.locations_disabled is not None:
			return parent.locations_disabled
		if parent.id:
			return get_doc_by_id('TraitSettings', parent.id).get('locations_disabled')
		else:
			return None

	def resolve_sfxs(parent, info):
		if parent.sfxs != None:
			return parent.sfxs
		if parent.id:
			sfxs = get_doc_by_id('TraitSettings', parent.id).get('sfxs')
			if sfxs is not None:
				return [SFX(id=sfx) for sfx in sfxs]
		else:
			return []

	def resolve_sfxs_ids(parent, info):
		if get_doc_by_id('TraitSettings', parent.id).get('sfxs') is not None:
			return get_doc_by_id('TraitSettings', parent.id).get('sfxs')

	def resolve_known_to(parent, info):
		if parent.id:
			characters = get_doc_by_id('TraitSettings', parent.id).get('known_to')
			if characters is None:
				return []
			return [Character(id=character) for character in characters]
		else:
			return []

	def resolve_hidden(parent, info):
		if parent.id and parent.hidden is None:
			TraitSetting._hydrate_traitsetting(parent, info)
		if parent.hidden is not None:
			return parent.hidden
		else:
			return False

	def resolve_priority(parent, info):
		if parent.priority:
			return parent.priority
		else:
			return 0

class TraitSettingInput(InputObjectType):
	new_trait_id = ID(required=False)
	rating_type = String(required=False)
	rating = List(Int, required=False)
	scaling = Int(required=False)
	resource = Boolean(required=False)
	statement = String(required=False)
	notes = String(required=False)
	locations_enabled = List(String, required=False)
	locations_disabled = List(String, required=False)
	sfxs = List(String, required=False)
	known_to = List(String, required=False)
	hidden = Boolean(required=False)
	teach_to = String(required=False)
	inherited_as = ID(required=False)

class MutateTraitSetting(Mutation):
	class Arguments:
		trait_setting_id = ID(required=False)
		trait_setting_input = TraitSettingInput(required=False)
		entity_id = ID(required=False) # for transferring traits
		die_type = Int(required=False) # for transferring resources
		temp = Boolean(required=False)

	trait = Field(lambda: Trait)
	message = String()

	def mutate(self, info, trait_setting_id=None, trait_setting_input=None, entity_id=None, die_type=None, temp=False):
		"""
		trait_setting_id: ID of trait setting to update, if not provided, trait will be created
		entity_id: ID of entity to add trait setting to
		die_type: for transferring resources
		"""
		# try:
		trait_setting = get_doc_by_id('TraitSettings', trait_setting_id)
		if trait_setting is None and entity_id is not None:
			trait_setting = db.collection('TraitSettings').insert({**trait_setting_input, '_from': entity_id})
		elif trait_setting is not None and trait_setting.get('_from').startswith('Entities/'):

			# transfering a trait
			if entity_id is not None and trait_setting.get('_from') != entity_id:

				# transferring resources happens per die
				if trait_setting.get('rating_type') == 'resource' and die_type is not None:
					# take out one die of the type from the original resource's rating
					new_rating = trait_setting.get('rating').copy()
					new_rating.remove(die_type)
					trait_setting = { **trait_setting, 'rating': new_rating }

					# needed query to compare "" statement with null statement
					query = f"""FOR setting IN TraitSettings
					FILTER setting._from == '{ entity_id }'
					FILTER setting._to == '{ trait_setting.get('_to') }'
					FILTER TRIM(setting.statement) == TRIM('{ trait_setting.get('statement') }')
					RETURN setting"""
					pockets = db.aql.execute(query)
					if not pockets.empty():
						to_pocket = [doc for doc in pockets][0]
						to_pocket['rating'] = to_pocket.get('rating') + [die_type]
						# logger.info(f"MutateTraitSetting:\tto_pocket: { to_pocket }")
						update_doc('TraitSettings', to_pocket, temp=temp)
					else:
						new_doc = {
							'_from': entity_id,
							'_to': trait_setting.get('_to'),
							**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
							'rating': [die_type],
							'hidden': False
						}
						# logger.info(f"MutateTraitSetting:\tnew pocket: { new_doc }")
						db.collection('TraitSettings').insert(new_doc)

				# if it's not a resource, but instead an asset, the entire asset is transferred at once
				elif get_doc_by_id('Traits', trait_setting.get('_to')).get('traitset') == 'Traitsets/3':
					trait_setting = { **trait_setting, '_from': entity_id }

			# then update the actual setting
			# new_trait_id exception
			if trait_setting_input is not None and trait_setting_input.get('new_trait_id') is not None:
				trait_setting = {
					'_id': trait_setting.get('_id'),
					'_from': trait_setting.get('_from'),
					'_to': trait_setting_input.get('new_trait_id'),
					**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
					**trait_setting_input
				}

			# teach_to exception
			if trait_setting_input is not None and trait_setting_input.get('teach_to') is None:
				trait_setting = {
					'_id': trait_setting.get('_id'),
					'_from': trait_setting.get('_from'),
					'_to': trait_setting.get('_to'),
					**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
					**trait_setting_input
				}
			elif trait_setting_input is not None \
					and trait_setting_input.get('teach_to') is not None \
					and get_doc_by_id('Entities', trait_setting_input.get('teach_to')).get('type') == 'character':
				trait_setting = {
					'_id': trait_setting.get('_id'),
					'_from': trait_setting.get('_from'),
					'_to': trait_setting.get('_to'),
					**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
					'known_to': list(set(trait_setting.get('known_to', []) + [trait_setting_input.get('teach_to')]))
				}
			update_doc('TraitSettings', trait_setting, temp=temp)
		else:
			if trait_setting_input is not None:
				trait_setting = {
					'_id': trait_setting.get('_id'),
					'_from': trait_setting.get('_from'),
					'_to': trait_setting.get('_to'),
					**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
					**trait_setting_input
				}
			update_doc('TraitSettings', trait_setting, temp=temp)
		return MutateTraitSetting(trait=Trait(trait_setting_id=trait_setting.get('_id')))
		# except Exception as e:
		# 	logger.info(e)
		# 	return MutateTraitSetting(message=f"MutateTraitSetting failed: {str(e)}")

class CloneTraitSetting(Mutation):
	class Arguments:
		trait_setting_id = ID(required=True)
		trait_setting_input = TraitSettingInput()
	
	trait = Field(lambda: Trait)

	def mutate(root, info, trait_setting_id=None, trait_setting_input=None):
		trait_setting = get_doc_by_id('TraitSettings', trait_setting_id)

		new_trait_settings = { key: value for key, value in trait_setting.items() if not key.startswith('_') }
		if trait_setting_input is not None:
			new_trait_settings = { **new_trait_settings, **trait_setting_input }

		new_trait_setting = db.collection('TraitSettings').insert({
			'_from': trait_setting.get('_from'),
			'_to': trait_setting.get('_to'),
			**new_trait_settings
		})

		# also clone subtraits
		subtraits = db.collection('TraitSettings').find({'_from': trait_setting_id})
		for subtrait in subtraits:
			db.collection('TraitSettings').insert({
				'_from': new_trait_setting.get('_id'),
				'_to': subtrait.get('_to'),
				**{ key: value for key, value in subtrait.items() if not key.startswith('_') },
			})
		return CloneTraitSetting(trait=Trait(trait_setting_id=new_trait_setting.get('_id')))


class Trait(ObjectType):
	global absolute_default_trait_setting

	traitset = Field(lambda: Traitset)
	traitset_id = ID()

	id = ID()
	name = String()
	explanation = String()
	required_traits = List(lambda: Trait)
	location_restricted = Boolean()

	trait_setting_id = ID()
	trait_setting = Field(lambda: TraitSetting)
	trait_settings = List(lambda: TraitSetting)

	statement = String()
	statement_examples = List(String)
	notes = String()

	rating_type = String()
	rating = List(Int)

	sfxs = List(lambda: SFX)
	possible_sfxs = List(lambda: SFX)

	sub_traits = List(lambda: Trait)
	possible_sub_traits = List(lambda: Trait)

	inheritable = Boolean()

	default_trait_setting = Field(lambda: TraitSetting)

	# returns all entities that have this trait
	entities = List(lambda: Entity)

	@classmethod
	def _hydrate_trait(cls, parent, info):
		if parent.id:
			trait = get_doc_by_id('Traits', parent.id)
		if parent.trait_setting_id:
			trait_id = get_doc_by_id('TraitSettings', parent.trait_setting_id).get('_to')
			trait = get_doc_by_id('Traits', trait_id)
		parent.traitset_id = trait.get('traitset')
		parent.id = trait.get('_id')
		parent.name = trait.get('name')
		parent.explanation = trait.get('explanation')
		parent.location_restricted = trait.get('location_restricted')
		parent.inheritable = trait.get('inheritable')
	
	@classmethod
	def _hydrate_traitsetting(cls, parent, info):
		if parent.trait_setting_id:
			traitsetting = get_doc_by_id('TraitSettings', parent.trait_setting_id)
			parent.statement = traitsetting.get('statement')
			parent.notes = traitsetting.get('notes')
			parent.rating_type = traitsetting.get('rating_type')
			parent.rating = traitsetting.get('rating')
		

	def resolve_id(parent, info):
		if parent.id:
			# Trait initialized with id
			return parent.id
		elif parent.trait_setting_id:
			# Trait initialized with traitsetting
			parent.id = get_doc_by_id('TraitSettings', parent.trait_setting_id).get('_to')
			return parent.id
		else:
			raise Exception("trait_setting is None 1")

	def resolve_name(parent, info):
		# logger.info(f"\nTrait.resolve_name:\ttrait:\n'{ parent }'")
		# if parent.name:
		# 	return parent.name
		# else:
		# 	Trait._hydrate_trait(parent, info)
		# 	return parent.name
		result = get_doc_by_id('Traits', parent.id).get('name')
		return result

	def resolve_explanation(parent, info):
		# logger.info(f"resolve_explanation:\ttrait: '{ parent.id }'")
		result = get_doc_by_id('Traits', parent.id).get('explanation')
		return result

	def resolve_traitset_id(parent, info):
		return get_doc_by_id('Traits', parent.id).get('traitset')

	def resolve_traitset(parent, info):
		# logger.info("resolving traitset for trait: ", parent.id)
		return Traitset(id=get_doc_by_id('Traits', parent.id).get('traitset'))

	def resolve_required_traits(parent, info):
		# logger.info("resolve_required_traits:\ttrait: ", parent.id)
		if parent.id is None and parent.trait_setting_id:
			parent.id = get_doc_by_id('TraitSettings', parent.trait_setting_id).get('_to')
		required_traits = get_doc_by_id('Traits', parent.id).get('required_traits') or []
		return [Trait(id=trait) for trait in required_traits]

	def resolve_location_restricted(parent, info):
		if not parent.location_restricted:
			Trait._hydrate_trait(parent, info)
		return parent.location_restricted or get_doc_by_id('Traitsets', parent.traitset_id).get('location_restricted')

	def resolve_trait_setting(parent, info):
		if parent.trait_setting:
			return parent.trait_setting
		elif parent.trait_setting_id:
			return TraitSetting(id=parent.trait_setting_id)
		elif info.context.get('trait_setting_id'):
			return TraitSetting(id=info.context.get('trait_setting_id'))
		elif parent.id is not None and info.context.get('entity_id') is not None:
			# logger.info("resolve_trait_setting:\ttrait: ", parent.id, "\tentity_id: ", info.context.get('entity_id'))
			cursor = db.collection('TraitSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			# logger.info("cursor count: ", cursor.count())
			if cursor.count() > 0:
				return TraitSetting(id=[doc.get('_id') for doc in cursor][0])
		else:
			raise Exception("trait_setting is None 2")

	def resolve_trait_settings(parent, info):
		if parent.trait_setting_id:
			return [TraitSetting(id=parent.trait_setting_id)]
		elif parent.id is not None and info.context.get('entity_id') is not None:
			return [TraitSetting(id=doc.get('_id')) for doc in db.collection('TraitSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})]
		else:
			return [TraitSetting(id=doc.get('_id')) for doc in db.collection('TraitSettings').find({'_to': parent.id})]

	def resolve_statement(parent, info):
		if parent.statement:
			return parent.statement
		elif parent.trait_setting_id:
			trait_setting = get_doc_by_id('TraitSettings', parent.trait_setting_id)
			parent.statement = trait_setting.get('statement')
			parent.rating_type = trait_setting.get('rating_type')
			parent.rating = trait_setting.get('rating')
			return parent.statement
		elif parent.id is not None and info.context.get('entity_id') is not None:
			# logger.info("resolve_statement:\ttrait: ", parent.id, "\tentity_id: ", info.context.get('entity_id'))
			cursor = db.collection('TraitSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			# logger.info("cursor count: ", cursor.count())
			if cursor.count() > 0:
				# logger.info('skibedob')
				return cursor.next().get('statement')
		else:
			raise Exception("trait_setting is None 3")

	def resolve_statement_examples(parent, info):
		if parent.statement_examples:
			return parent.statement_examples
		elif parent.id:
			examples = db.collection('TraitSettings').find({'_to': parent.id})
			seen = set()
			result = []
			for doc in examples:
				statement = doc.get('statement')
				if statement:
					lowered = statement.strip().lower()
					if lowered not in seen:
						result.append(statement)
						seen.add(lowered)
			return result

	def resolve_notes(parent, info):
		if parent.notes:
			return parent.notes
		elif parent.trait_setting_id:
			trait_setting = get_doc_by_id('TraitSettings', parent.trait_setting_id)
			parent.statement = trait_setting.get('statement')
			parent.notes = trait_setting.get('notes')
			parent.rating_type = trait_setting.get('rating_type')
			parent.rating = trait_setting.get('rating')
			return parent.notes

	def resolve_rating_type(parent, info):
		if parent.rating_type:
			return parent.rating_type
		elif parent.trait_setting_id:
			trait_setting = get_doc_by_id('TraitSettings', parent.trait_setting_id)
			parent.statement = trait_setting.get('statement')
			parent.notes = trait_setting.get('notes')
			parent.rating_type = trait_setting.get('rating_type')
			parent.rating = trait_setting.get('rating')
			return parent.rating_type
		else:
			raise Exception("trait_setting is None 4")

	def resolve_rating(parent, info):
		if parent.rating:
			return parent.rating
		elif parent.trait_setting_id:
			trait_setting = get_doc_by_id('TraitSettings', parent.trait_setting_id)
			parent.statement = trait_setting.get('statement')
			parent.rating_type = trait_setting.get('rating_type')
			parent.rating = trait_setting.get('rating')
			return parent.rating
		else:
			raise Exception("trait_setting is None 5")

	def resolve_sfxs(parent, info):
		if parent.trait_setting_id:
			# logger.info("resolve_sfxs:\ttrait_setting: ", parent.trait_setting_id)
			sfxs = get_doc_by_id('TraitSettings', parent.trait_setting_id).get('sfxs')
			if sfxs is not None:
				return [SFX(id=sfx) for sfx in sfxs]
		return []

	def resolve_possible_sfxs(parent, info):
		trait = get_doc_by_id('Traits', parent.id)
		return [SFX(id=sfx) for sfx in trait.get('possible_sfxs') or []]

	def resolve_inheritable(parent, info):
		if not parent.inheritable:
			Trait._hydrate_trait(parent, info)
		return parent.inheritable

	def resolve_default_trait_setting(parent, info):
		global absolute_default_trait_setting
		if parent.id:
			default_trait_settings = db.collection('TraitSettings').find({'_from': parent.id, '_to': 'Traits/1'})
			default_trait_setting = [doc for doc in default_trait_settings][0] if default_trait_settings.count() == 1 else None
			if default_trait_setting:
				return TraitSetting(id=default_trait_setting.get('_id'))
			else:
				traitset_id = get_doc_by_id('Traits', parent.id).get('traitset')
				default_traitset_settings = db.collection('TraitSettings').find({'_from': traitset_id, '_to': 'Traits/1'})
				default_trait_setting = [doc for doc in default_traitset_settings][0] if default_traitset_settings.count() == 1 else None
				if default_trait_setting:
					return TraitSetting(id=default_trait_setting.get('_id'))
				else:
					default_settings = db.collection('TraitSettings').find({'_from': 'Traits/1', '_to': 'Traits/1'})
					default_setting = [doc for doc in default_settings][0] if default_settings.count() == 1 else None
					if default_setting:
						return TraitSetting(id=default_setting.get('_id'))
		else:
			default_settings = db.collection('TraitSettings').find({'_from': 'Traits/1', '_to': 'Traits/1'})
			default_setting = [doc for doc in default_settings][0] if default_settings.count() == 1 else None
			if default_setting:
				return TraitSetting(id=default_setting.get('_id'))
			else:
				return absolute_default_trait_setting

	def resolve_entities(parent, info):
		if parent.trait_setting_id:
			entity_id = get_doc_by_id('TraitSettings', parent.trait_setting_id).get('_from')
			if entity_id.startswith('Entities/'):
				entity_type = get_doc_by_id('Entities', entity_id).get('type')
				if entity_type == 'character':
					return [Character(id=entity_id)]
				elif entity_type == 'npc':
					return [NPC(id=entity_id)]
				elif entity_type == 'asset':
					return [Asset(id=entity_id)]
				elif entity_type == 'faction':
					return [Faction(id=entity_id)]
				elif entity_type == 'location':
					return [Location(id=entity_id)]
			elif entity_id.startswith('Relations/'):
				return [Relation(id=entity_id)]
		else:
			# return all entities that have this trait
			entities = []
			traitsettings = db.collection('TraitSettings').find({'_to': parent.id})
			for setting in traitsettings:
				entity_id = setting.get('_from')
				if entity_id.startswith('Entities/'):
					entity_type = get_doc_by_id('Entities', entity_id).get('type')
					if entity_type == 'character':
						entities.append(Character(id=entity_id))
					elif entity_type == 'npc':
						entities.append(NPC(id=entity_id))
					elif entity_type == 'asset':
						entities.append(Asset(id=entity_id))
					elif entity_type == 'faction':
						entities.append(Faction(id=entity_id))
					elif entity_type == 'location':
						entities.append(Location(id=entity_id))
				elif entity_id.startswith('Relations/'):
					entities.append(Relation(id=entity_id))
			unique_entities = list({entity.id: entity for entity in entities}.values())

			return unique_entities

	def resolve_sub_traits(parent, info):
		if not parent.trait_setting_id:
			raise Exception("trait_setting is None 7")
		# sub_traits = db.collection('TraitSettings').find({'_from': parent.trait_setting_id})
		query = f"""FOR subtraits IN TraitSettings
			FILTER subtraits._from == '{ parent.trait_setting_id }'
			FOR trait IN Traits
			FILTER trait._id == subtraits._to
			SORT trait.traitset ASC, SUM(ABS(subtraits.rating)), trait._id ASC
			RETURN subtraits"""
		sub_traits = list(db.aql.execute(query))
		query = f"""FOR setting IN TraitSettings
			FILTER setting._id == '{ parent.trait_setting_id }'
			FOR shortcut_trait IN setting.shortcut_traits OR []
			FOR trait_setting IN TraitSettings
			FILTER shortcut_trait == trait_setting._id
			RETURN trait_setting"""
		shortcuts = list(db.aql.execute(query))
		result = sub_traits + shortcuts
		return [Trait(id=doc.get('_to'), trait_setting_id=doc.get('_id')) for doc in result]

	def resolve_possible_sub_traits(parent, info):
		if parent.id.startswith('Traits/') and (possible_sub_traits := get_doc_by_id('Traits', parent.id).get('possible_sub_traits')):
			result = []
			for sub_trait in possible_sub_traits:
				traitset_id = get_doc_by_id('Traits', sub_trait).get('traitset')
				# sub-traitsets
				if 'subtrait' in get_doc_by_id('Traitsets', traitset_id).get('entity_types'):
					result.append(Trait(id=sub_trait))
				# entity traits
				elif info.context.get('entity_id'):
					traits = db.collection('TraitSettings').find({ '_from': info.context.get('entity_id'), '_to': sub_trait })
					entity = get_doc_by_id('Entities', info.context.get('entity_id'))
					traits = filter_trait_settings_by_location(traits, retrieve_location(entity).get('_id'))
					for trait in traits:
						result.append(Trait(id=trait.get('_to'), trait_setting_id=trait.get('_id')))
				elif info.context.get('trait_setting_id'):
					entity_id = get_doc_by_id('TraitSettings', info.context.get('trait_setting_id')).get('_from')
					traits = db.collection('TraitSettings').find({ '_from': entity_id, '_to': sub_trait })
					for trait in traits:
						result.append(Trait(id=trait.get('_to'), trait_setting_id=trait.get('_id')))
				else:
					result.append(Trait(id=sub_trait))
			return result
		else:
			return []

class TraitInput(InputObjectType):
	name = String(required=False)
	explanation = String(required=False)
	traitset_id = ID(required=False)
	required_traits = List(ID, required=False)
	location_restricted = Boolean(required=False)
	possible_sub_traits = List(ID, required=False)
	possible_sfxs = List(ID, required=False)
	inheritable = Boolean(required=False)

class CreateTrait(Mutation):
	class Arguments:
		trait_input = TraitInput(required=True)

	trait = Field(Trait)

	def mutate(self, info, trait_input=None):
		# can't straight up put trait_input because the key names are different
		new_trait = db.collection('Traits').insert({
			'name': trait_input.name,
			'explanation': trait_input.explanation,
			'traitset': trait_input.traitset_id,
			'required_traits': trait_input.required_traits,
			'possible_sub_traits': trait_input.possible_sub_traits
		})

		# now also create the trait default, based on the traitset default if it exists or the absolute default
		traitset_default = db.collection('TraitSettings').find({'_from': trait_input.get('traitset_id'), '_to': 'Traits/1'})
		
		if not traitset_default.empty():
			traitset_default = [doc for doc in traitset_default][0]
			db.collection('TraitSettings').insert({
				'_from': new_trait.get('_id'),
				'_to': 'Traits/1',
				**{k: v for k, v in traitset_default.items() if v is not None and not k.startswith('_')}
			})
		else:
			absolute_default = db.collection('TraitSettings').find({'_from': 'Traits/1', '_to': 'Traits/1'})
			if not absolute_default.empty():
				absolute_default = [doc for doc in absolute_default][0]
				db.collection('TraitSettings').insert({
					'_from': new_trait.get('_id'),
					'_to': 'Traits/1',
					**{k: v for k, v in absolute_default.items() if v is not None and not k.startswith('_')}
				})

		return CreateTrait(trait=Trait(id=new_trait['_id']))

class UpdateTraitDefault(Mutation):
	class Arguments:
		trait_id = ID(required=True)
		default_settings = TraitSettingInput(required=True)

	trait = Field(lambda: Trait)

	def mutate(root, info, trait_id, default_settings):
		if db.collection('TraitSettings').find({'_from': trait_id, '_to': 'Traits/1'}).count() > 1:
			traits = db.collection('TraitSettings').find({'_from': trait_id, '_to': 'Traits/1'})
			db.collection('TraitSettings').delete_many([trait.get('_id') for trait in traits])
		if db.collection('TraitSettings').find({'_from': trait_id, '_to': 'Traits/1'}).count() == 1:
			db.collection('TraitSettings').update_match(
				{ '_from': trait_id, '_to': 'Traits/1' },
				default_settings
			)
		else:
			db.collection('TraitSettings').insert(
				{
					'_from': trait_id,
					'_to': 'Traits/1',
					**default_settings
				}
			)
		# if default_settings.get('locations_disabled') is not None:
		# 	db.collection('TraitSettings').update_match(
		# 		{ '_to': trait_id },
		# 		{ 'locations_disabled': default_settings.get('locations_disabled') }
		# 	)
		return UpdateTraitDefault(trait=Trait(id=trait_id))

class MutateTrait(Mutation):
	class Arguments:
		trait_id = ID(required=True)
		trait_input = TraitInput(required=False)
		entity_id = ID(required=False)

	trait = Field(Trait)

	def mutate(root, info, trait_id=None, trait_input=None):
		"""either change trait defaults, or change trait settings for an entity"""
		trait = get_doc_by_id('Traits', trait_id)
		if trait_input is not None:
			if trait_input.get('required_traits') is not None:
				for required_trait in trait_input.get('required_traits'):
					try:
						db.collection('Traits').has(required_trait)
					except:
						if(setting := get_doc_by_id('TraitSettings', required_trait)):
							trait_input['required_traits'].remove(required_trait)
							trait_input['required_traits'].append(setting['_to'])
			
			if trait_input.get('traitset_id') is not None:
				trait_input['traitset'] = trait_input.pop('traitset_id')

			trait = {**trait, **trait_input}

		update_doc('Traits', trait)
		return MutateTrait(trait=Trait(id=trait.get('_id')))

class AssignTrait(Mutation):
	class Arguments:
		# input = TraitSettingInput(required=True)
		trait_id = ID(required=True)
		entity_id = ID(required=True)
		location_id = ID(required=False)
		trait_setting_input = TraitSettingInput(required=False)

	trait = Field(Trait)

	def mutate(root, info, trait_id=None, entity_id=None, location_id=None, trait_setting_input=None):
		global absolute_default_trait_setting
		traitsetting = None
		old_traitsetting_id = ""

		# location given means that the trait is only available at that location and its zones
		# otherwise, leave constraint empty
		locations_enabled = []
		locations_disabled = []
		if location_id is not None:
			locations_enabled = [location_id]
			locations_disabled = ['Entities/2']

		# retrieving default trait setting
		query = f"""FOR traitsetting IN TraitSettings
				FILTER traitsetting._from == '{ trait_id }'
				FILTER traitsetting._to == 'Traits/1'
				RETURN {{
					'_id': traitsetting._id,
					'rating_type': traitsetting.rating_type,
					'rating': traitsetting.rating,
					{
						"'locations_enabled': ['" + "', '".join(locations_enabled) + "'], 'locations_disabled':['" + "', '".join(locations_disabled) + "'],"
						if location_id is not None else "'locations_enabled': traitsetting.locations_enabled, 'locations_disabled': traitsetting.locations_disabled,"
					}
					'sfxs': traitsetting.sfxs,
					'hidden': traitsetting.hidden,
					{
						"'known_to': ['" + "', '".join(trait_setting_input.get('known_to', [])) + "']," if trait_setting_input.get('known_to') else ''
					}
					'statement': traitsetting.statement,
					'notes': traitsetting.notes
				}}"""
		logger.info(f"AssignTrait:\tquerying for trait default:\n{ query }")
		cursor = db.aql.execute(query)
		# retrieving default traitset setting
		if cursor.empty():
			query = f"""FOR traitsetting IN TraitSettings
				FILTER traitsetting._from == '{ get_doc_by_id('Traits', trait_id)['traitset'] }'
				FILTER traitsetting._to == 'Traits/1'
				RETURN {{
					'_id': traitsetting._id,
					'rating_type': traitsetting.rating_type,
					'rating': traitsetting.rating,
					{
						"'locations_enabled':['" + "', '".join(locations_enabled) + "'], 'locations_disabled':['" + "', '".join(locations_disabled) + "'],"
						if location_id is not None else "'locations_enabled': traitsetting.locations_enabled, 'locations_disabled': traitsetting.locations_disabled,"
					}
					'sfxs': traitsetting.sfxs,
					'hidden': traitsetting.hidden,
					{
						"'known_to': ['" + "', '".join(trait_setting_input.get('known_to', [])) + "']," if trait_setting_input.get('known_to') else ''
					}
					'statement': traitsetting.statement,
					'notes': traitsetting.notes
				}}"""
			cursor = db.aql.execute(query)
		# retrieving global default setting
		if cursor.empty():
			query = f"""FOR traitsetting IN TraitSettings
					FILTER traitsetting._id == 'TraitSettings/1'
					RETURN {{
						'_id': traitsetting._id,
						'rating_type': traitsetting.rating_type,
						'rating': traitsetting.rating,
						{
							"'locations_enabled':['" + "', '".join(locations_enabled) + "'], 'locations_disabled':['" + "', '".join(locations_disabled) + "'],"
							if location_id is not None else "'locations_enabled': traitsetting.locations_enabled, 'locations_disabled': traitsetting.locations_disabled,"
						}
						'sfxs': traitsetting.sfxs,
						'hidden': traitsetting.hidden,
						{
							"'known_to': ['" + "', '".join(trait_setting_input.get('known_to', [])) + "']," if trait_setting_input.get('known_to') else ''
						}
						'statement': traitsetting.statement,
						'notes': traitsetting.notes
					}}"""
			cursor = db.aql.execute(query)
		if not cursor.empty():
			traitsetting = [doc for doc in cursor][0]
			old_traitsetting_id = traitsetting.get('_id')
			traitsetting = {
				**absolute_default_trait_setting,
				**{k: v for k, v in traitsetting.items() if v is not None and not k.startswith('_')}
			}
		else:
			traitsetting = {
				**absolute_default_trait_setting,
				'locations_enabled': { locations_enabled },
				'locations_disabled': { locations_disabled },
			}

		# use the defaults found to assign the trait
		new_traitsetting = db.collection('TraitSettings').insert({
			'_from': entity_id,
			'_to': trait_id,
			**{k: v for k, v in traitsetting.items() if v is not None and not k.startswith('_')},
			**{k: v for k, v in trait_setting_input.items() if v is not None and not k.startswith('_')}
		})

		# also assign the subtraits
		# logger.info(f"AssignTrait:\tassigning subtraits for { new_traitsetting.get('_id') } from { old_traitsetting_id }")
		query = f"""FOR setting IN TraitSettings
			FILTER setting._from == '{ old_traitsetting_id }'
			FILTER setting._to != 'Traits/1'
			RETURN setting"""
		cursor = db.aql.execute(query)
		for subtrait in cursor:
			db.collection('TraitSettings').insert({
				'_from': new_traitsetting.get('_id'),
				'_to': subtrait.get('_to'),
				**{k: v for k, v in subtrait.items() if v is not None and not k.startswith('_')}
			})

		# if the entity doesn't have traitset settings yet, create it
		trait = get_doc_by_id('Traits', trait_id)
		traitset_settings = db.collection('TraitsetSettings').find({ '_from': entity_id, '_to': trait.get('traitset') })
		if traitset_settings.empty():
			traitset = get_doc_by_id('Traitsets', trait.get('traitset'))
			db.collection('TraitsetSettings').insert({
				'_from': entity_id,
				'_to': trait.get('traitset'),
				**{k: v for k, v in traitset.items() if not k.startswith('_')}
			})

		# if the entity was an archetype,
		# also add the trait to entities based on that archetype
		# that don't yet have the trait
		# if entity_id.startswith('Entities/') and get_doc_by_id('Entities', entity_id).get('is_archetype'):
		# 	for entity in db.collection('Entities').find({'archetype_id': entity_id}):
		# 		if db.collection('TraitSettings').find({
		# 			'_from': entity.get('_id'),
		# 			'_to': trait_id,
		# 			'locations_disabled': traitsetting.get('locations_disabled'),
		# 			'locations_enabled': traitsetting.get('locations_enabled'),
		# 		}).empty():
		# 			db.collection('TraitSettings').insert({
		# 				'_from': entity.get('_id'),
		# 				'_to': trait_id,
		# 				**traitsetting
		# 			})
		# 		if db.collection('TraitsetSettings').find({
		# 			'_from': entity.get('_id'),
		# 			'_to': trait.get('traitset')
		# 		}).empty():
		# 			traitset = get_doc_by_id('Traitsets', trait.get('traitset'))
		# 			db.collection('TraitsetSettings').insert({
		# 				'_from': entity.get('_id'),
		# 				'_to': trait.get('traitset'),
		# 				**{k: v for k, v in traitset.items() if not k.startswith('_')}
		# 			})

		return AssignTrait(trait=Trait(id=trait_id))

class AssignSubTrait(Mutation):
	class Arguments:
		trait_setting_id = ID(required=True)
		subtrait_id = ID(required=True)
		entity_id = ID(required=False)

	trait = Field(Trait)

	def mutate(self, info, trait_setting_id=None, subtrait_id=None, entity_id=None):
		"""
		Assigns subtrait to given trait setting.

		This is a shortcut for creating a trait setting between the given trait
		setting and the given subtrait, using the default trait setting for the
		traitset that the subtrait is in.

		Args:
			trait_setting_id: The ID of the trait setting to assign the subtrait to.
			subtrait_id: The ID of the subtrait to assign.
			entity_id: The ID of the entity to assign the subtrait to. If not
				provided, the entity ID will be taken from the trait setting.

		Returns:
			A GraphQL `AssignSubTrait` object with the ID of the new subtrait.
		"""
		global absolute_default_trait_setting

		traitset_id = get_doc_by_id('Traits', subtrait_id).get('traitset')
		traitset = get_doc_by_id('Traitsets', traitset_id)

		if 'subtrait' in traitset.get('entity_types'):
			# get the default trait setting for this subtrait
			default_trait_setting = absolute_default_trait_setting

			# if the subtrait already has a default trait setting, use that
			default_trait_settings = db.collection('TraitSettings').find({ '_from': subtrait_id, '_to': 'Traits/1' })
			if not default_trait_settings.empty():
				default_trait_setting = [doc for doc in default_trait_settings][0]
				default_trait_setting = {k: v for k, v in default_trait_setting.items() if not k.startswith('_')}
			else:
				# if the subtrait doesn't have a default trait setting, use the default
				# trait setting for the traitset that the subtrait is in
				traitset_id = get_doc_by_id('Traits', subtrait_id).get('traitset')
				traitset_settings = db.collection('TraitsetSettings').find({ '_from': traitset_id, '_to': 'Traits/1' })
				if not traitset_settings.empty():
					default_trait_setting = [doc for doc in traitset_settings][0]
					default_trait_setting = {k: v for k, v in default_trait_setting.items() if not k.startswith('_')}
				else:
					# if the subtrait doesn't have a default trait setting, and the
					# traitset it's in doesn't have a default trait setting, use the
					# absolute default trait setting
					default_trait_settings = db.collection('TraitSettings').find({ '_from': 'Traits/1', '_to': 'Traits/1' })
					if not default_trait_settings.empty():
						default_trait_setting = [doc for doc in default_trait_settings][0]
						default_trait_setting = {k: v for k, v in default_trait_setting.items() if not k.startswith('_')}
					else:
						default_trait_setting = absolute_default_trait_setting

			# check if entity was archetype and given entity ID is not the archetype
			traitsetting = get_doc_by_id('TraitSettings', trait_setting_id)
			from_entity_id = traitsetting.get('_from')
			if from_entity_id.startswith('Entities/') and get_doc_by_id('Entities', from_entity_id).get('is_archetype') and entity_id and from_entity_id != entity_id:
				# if so copy the original trait setting for the given entity
				new_traitsetting = db.collection('TraitSettings').insert({
					'_from': entity_id,
					'_to': traitsetting.get('_to'),
					**{k: v for k, v in traitsetting.items() if not k.startswith('_')},
					'inherited_as': trait_setting_id
				})
				new_trait_setting_id = traitsetting.get('_id')
				# also copy all the original traitsetting's subtraits
				for subtrait in db.collection('TraitSettings').find({
					'_from': trait_setting_id
				}):
					if subtrait.get('_to') != subtrait_id:
						db.collection('TraitSettings').insert({
							'_from': new_trait_setting_id,
							'_to': subtrait.get('_to'),
							**{k: v for k, v in subtrait.items() if not k.startswith('_')}
						})
				trait_setting_id = new_traitsetting.get('_id')


			# if the subtrait isn't already assigned to the given trait setting,
			# create a new trait setting
			if db.collection('TraitSettings').find({
				'_from': trait_setting_id,
				'_to': subtrait_id
			}).empty():
				new_subtrait = db.collection('TraitSettings').insert({
					'_from': trait_setting_id,
					'_to': subtrait_id,
					**default_trait_setting
				})



				return AssignSubTrait(trait=Trait(id=new_subtrait.get('_to'), trait_setting_id=new_subtrait.get('_id')))
			else:
				raise Exception("Subtrait already assigned")
		else:
			# maybe assign entity trait as shortcut subtrait
			entity_id = info.context.get('entity_id') or (trait := get_doc_by_id('TraitSettings', trait_setting_id)).get('_from')
			if not (shortcut_traits := db.collection('TraitSettings').find({
				'_from': entity_id,
				'_to': subtrait_id
			})).empty():
				if trait.get('shortcut_traits') is None:
					trait['shortcut_traits'] = []
				for shortcut_trait in shortcut_traits:
					trait['shortcut_traits'].append(shortcut_trait.get('_id'))
				trait['shortcut_traits'] = list(set(trait.get('shortcut_traits')))
				update_doc('TraitSettings', trait)
				return AssignSubTrait(trait=Trait(id=subtrait_id, trait_setting_id=trait_setting_id))

class UnassignSubTrait(Mutation):
	class Arguments:
		trait_setting_id = ID()
		subtrait_setting_id = ID(required=True)

	success = Boolean()
	message = String()

	def mutate(root, info, trait_setting_id=None, subtrait_setting_id=None):
		# logger.info(f"UnassignSubTrait:\t{ trait_setting_id }")
		if trait_setting_id is not None:
			trait = get_doc_by_id('TraitSettings', trait_setting_id)

			if trait is not None and 'shortcut_traits' in trait and subtrait_setting_id in trait.get('shortcut_traits'):
				# logger.info(f"UnassignSubTrait:\t{ trait }")
				trait['shortcut_traits'].remove(subtrait_setting_id)
				update_doc('TraitSettings', trait)
			else:
				db.collection('TraitSettings').delete(subtrait_setting_id)
			return UnassignSubTrait(success=True)
		else:
			return UnassignSubTrait(success=False, message="No trait specified")

class UnassignTrait(Mutation):
	class Arguments:
		trait_setting_id = ID(required=True)

	success = Boolean()
	message = String()

	def mutate(root, info, trait_setting_id=None):
		# logger.info(f"UnassignTrait:\t{ trait_setting_id }")
		trait_setting = get_doc_by_id('TraitSettings', trait_setting_id)
		# check the instances of the archetype
		if trait_setting.get('_from').startswith('Entities/'):
			archetype = get_doc_by_id('Entities', trait_setting.get('_from'))
			if archetype.get('is_archetype'):
				instances = db.collection('Relations').find({'_to': archetype.get('_id'), 'type': 'archetype'})
				if not instances.empty():
					for instance in instances:
						# check if settings are the same
						instance_trait_settings = db.collection('TraitSettings').find({
							'_from': instance.get('_id'),
							'_to': trait_setting.get('_to'),
							'rating_type': trait_setting.get('rating_type'),
							'rating': trait_setting.get('rating'),
							'statement': trait_setting.get('statement'),
							'locations_enabled': trait_setting.get('locations_enabled'),
							'locations_disabled': trait_setting.get('locations_disabled'),
							'sfxs': trait_setting.get('sfxs')
						})
						if not instance_trait_settings.empty():
							for instance_trait_setting in instance_trait_settings:
								subtraits = db.collection('TraitSettings').find({'_from': instance_trait_setting.get('_id')})
								for subtrait in subtraits:
									db.collection('TraitSettings').delete(subtrait.get('_id'))
								db.collection('TraitSettings').delete(instance_trait_setting.get('_id'))
		subtraits = db.collection('TraitSettings').find({'_from': trait_setting_id})
		for subtrait in subtraits:
			db.collection('TraitSettings').delete(subtrait.get('_id'))
		db.collection('TraitSettings').delete(trait_setting_id)
		return UnassignTrait(success=True)

class AssignTraitRating(Mutation):
	class Arguments:
		trait_id = ID()
		character_id = ID()
		rating = List(String)

	trait = Field(Trait)

	def mutate(root, info, trait_id=None, character_id=None, rating=None):
		# logger.info(f"arguments; trait_id: { trait_id }, character_id: { character_id }, rating: { ', '.join(rating) }")
		if not (trait_id and character_id and rating):
			errorMessage = f"missing argument(s), trait_id: { trait_id }, character_id: { character_id }, rating: { rating }"
			# logger.info(errorMessage)
			return { 'error': errorMessage }
		doc = db.collection('character_has_trait').update_match({'_from': character_id, '_to': trait_id}, {'rating': rating})
		return AssignTraitRating(trait=Trait(id=trait_id, rating=rating))

class DeleteTrait(Mutation):
	class Arguments:
		trait_id = ID(required=True)

	success = Boolean()
	error = String()

	def mutate(root, info, trait_id=None):
		# deletes the trait document and all traitsetting edges associated with it
		try:
			db.collection('Traits').delete(trait_id)
			settings = db.collection('TraitSettings').find({'_to': trait_id})
			for setting in settings:
				db.collection('TraitSettings').delete(setting.get('_id'))
			settings = db.collection('TraitSettings').find({'_from': trait_id})
			for setting in settings:
				db.collection('TraitSettings').delete(setting.get('_id'))
			return DeleteTrait(success=True)
		except Exception as e:
			return DeleteTrait(success=False, error=f"DeleteTrait failed: {str(e)}")


class Traitset(ObjectType):
	key = ID()
	id = ID(required=True)
	name = String()
	explainer = String()
	entity_types = List(String)
	location_restricted = Boolean()
	limit = Int()
	order = Int()
	duplicates = Boolean()
	traits = List(Trait)
	sfxs = List(lambda: SFX)
	# rating = List(String)
	default_trait_setting = Field(lambda: TraitSetting)
	# character = Field(lambda: Character)
	score = Int()
	initial_xp = Int()
	traitset_setting = Field(lambda: TraitsetSetting)

	hydrated = False

	@classmethod
	def _hydrate(cls, parent, info):
		traitset = get_doc_by_id('Traitsets', parent.id)
		parent.key = traitset.get('_key')
		parent.name = traitset.get('name')
		parent.explainer = traitset.get('explainer')
		parent.entity_types = traitset.get('entity_types')
		parent.location_restricted = traitset.get('location_restricted')
		parent.limit = traitset.get('limit')
		parent.order = traitset.get('order')
		parent.duplicates = traitset.get('duplicates')
		parent.hydrated = True

	def resolve_key(parent, info):
		if not parent.key:
			Traitset._hydrate(parent, info)
		if parent.key:
			return parent.key
		return get_doc_by_id('Traitsets', parent.id).get('_key')

	def resolve_name(parent, info):
		if not parent.name:
			Traitset._hydrate(parent, info)
		if parent.name:
			return parent.name
		return get_doc_by_id('Traitsets', parent.id).get('name')

	def resolve_explainer(parent, info):
		if not parent.explainer:
			Traitset._hydrate(parent, info)
		if parent.explainer:
			return parent.explainer
		return get_doc_by_id('Traitsets', parent.id).get('explainer')

	def resolve_entity_types(parent, info):
		if not parent.entity_types:
			Traitset._hydrate(parent, info)
		if parent.entity_types:
			return parent.entity_types
		return get_doc_by_id('Traitsets', parent.id).get('entity_types')

	def resolve_location_restricted(parent, info):
		if not parent.location_restricted:
			Traitset._hydrate(parent, info)
		if parent.location_restricted is not None:
			return parent.location_restricted
		return get_doc_by_id('Traitsets', parent.id).get('location_restricted') or False

	def resolve_limit(parent, info):
		if info.context.get('entity_id') is not None:
			# check in traitset settings if limit is overridden
			traitset_settings = db.collection('TraitsetSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			for traitset_setting in traitset_settings:
				if traitset_setting.get('dicepool_limit') is not None:
					return traitset_setting.get('dicepool_limit')
		if parent.limit:
			return parent.limit
		return get_doc_by_id('Traitsets', parent.id).get('dicepool_limit')

	def resolve_order(parent, info):
		if parent.order:
			return parent.order
		return get_doc_by_id('Traitsets', parent.id).get('order')

	def resolve_duplicates(parent, info):
		if parent.duplicates:
			return parent.duplicates
		return get_doc_by_id('Traitsets', parent.id).get('duplicates')

	def resolve_traits(parent, info):
		if not parent.hydrated:
			Traitset._hydrate(parent, info)
		if parent.traits:
			return parent.traits

		# traits per relation
		elif info.context.get('entity_id') is not None and info.context.get('entity_id').startswith('Relations/'):
			query = f"""FOR traitsettings IN TraitSettings
				FILTER traitsettings._from == '{ info.context.get('entity_id') }'
			FOR trait IN Traits
				FILTER traitsettings._to == trait._id
				FILTER trait.traitset == '{ parent.id }'
			SORT TO_NUMBER(SUBSTRING(MAX(traitsettings.rating), 1)) DESC, trait.name
			RETURN {{ id: trait._id, setting: traitsettings._id }}"""
			cursor = db.aql.execute(query)
			return [Trait(
				id=doc['id'],
				trait_setting_id=doc['setting']
			) for doc in cursor]
		
		# traits for relationships
		elif 'relation' in parent.entity_types:
			query = f"""FOR relation IN Relations
				FILTER relation._from == '{ info.context.get('entity_id') }'
			FOR traitsettings IN TraitSettings
				FILTER traitsettings._from == relation._id
			FOR trait IN Traits
				FILTER traitsettings._to == trait._id
				FILTER trait.traitset == '{ parent.id }'
			SORT TO_NUMBER(SUBSTRING(MAX(traitsettings.rating), 1)) DESC, trait.name
			RETURN {{ id: trait._id, setting: traitsettings._id }}"""
			cursor = db.aql.execute(query)
			return [Trait(
				id=doc['id'],
				trait_setting_id=doc['setting']
			) for doc in cursor]

		elif info.context.get('entity_id') is not None and info.context.get('entity_id').startswith('Entities/'):
			# logger.info(f"Traitset.resolve_traits:\tentity_id: { info.context.get('entity_id') }")
			entity = get_doc_by_id('Entities', info.context.get('entity_id'))

			# traits for location are inherited, so special query
			if entity is not None and entity.get('type') == 'location':
				if info.context.get('sorting') is not None and info.context.get('sorting') == 'NAME':
					sorting = "SORT t.name, setting.statement, MAX(setting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], setting.rating_type, true) ASC"
				else:
					sorting = "SORT MAX(setting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], setting.rating_type, true) ASC, t.name, setting.statement"
				# logger.info(f"Traitset.resolve_traits:\treturning location traits")
				query = f"""FOR location IN Entities
					FILTER location._id == '{ info.context.get('entity_id') }'
					FILTER location.type == 'location'
					LET direct_traits = (
						FOR setting IN TraitSettings
							FILTER location._id == setting._from
						FOR t IN Traits
							FILTER setting._to == t._id
							FILTER t.traitset == '{ parent.id }'
						{ sorting }
						RETURN setting
					)
					LET parent_locations = (
						FOR v, e, p IN 0..20 OUTBOUND location._id Relations
						FILTER p.edges[*].type ALL == 'super'
						RETURN v._id
					)
					LET hierarchies = APPEND([location._id], parent_locations)
					LET inherited_traits = (
						FOR entity IN hierarchies
							FOR trait, traitsetting IN OUTBOUND entity TraitSettings
							FILTER trait.traitset == '{ parent.id }'
							FILTER trait.inheritable == true
							COLLECT traitId = traitsetting._to INTO traitsettings
							RETURN traitsettings[0].traitsetting
					)
					FOR trait IN UNIQUE(APPEND(direct_traits, inherited_traits))
					RETURN trait"""
				cursor = db.aql.execute(query)
				return [Trait(id=trait['_to'], trait_setting_id=trait['_id']) for trait in cursor]




			# traits for non-location entities
			elif entity is not None and entity.get('type') != 'location':

				location = retrieve_location(entity)
				location_id = location.get('_id')

				# direct traits
				if info.context.get('sorting') is not None and info.context.get('sorting') == 'NAME':
					sorting = "SORT trait.name, setting.statement, MAX(setting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], setting.rating_type, true) ASC"
				else:
					sorting = "SORT MAX(setting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], setting.rating_type, true) ASC, trait.name"
				
				query = f"""FOR setting IN TraitSettings
					FILTER setting._from == '{ entity.get('_id') }'
					FOR trait IN Traits
						FILTER setting._to == trait._id
						FILTER trait.traitset == '{ parent.id }'
					{ sorting }
					RETURN setting"""
				direct_trait_settings = [doc for doc in db.aql.execute(query)]
				direct_trait_settings = [{
					'max': 10000,
					'entity_depth': 0,
					**doc
				} for doc in direct_trait_settings]
				# logger.info(f"Traitset.resolve_traits:\tentity trait_settings: { trait_settings }")
				direct_trait_settings = filter_trait_settings_by_location(direct_trait_settings, location_id)

				location_hierarchy = retrieve_hierarchy(location_id)

				# inherited traits
				if info.context.get('sorting') is not None and info.context.get('sorting') == 'NAME':
					sorting = "SORT t.name, traitsettings[0].traitsetting.statement, MAX(traitsettings[0].traitsetting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], traitsettings[0].traitsetting.rating_type, true) ASC"
				else:
					sorting = "SORT MAX(traitsettings[0].traitsetting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], traitsettings[0].traitsetting.rating_type, true) ASC, t.name"
				# inherited_traits = [ts.get('inherited_as') for ts in trait_settings if ts.get('inherited_as') is not None]
				# logger.info(f"Traitset.resolve_traits:\tinherited_traits: { inherited_traits }")
				query = f"""LET archetypes = (
						FOR v, e, p IN 0..20 OUTBOUND '{ entity.get('_id') }' Relations
						FILTER p.edges[*].type ALL == 'archetype'
						FILTER v._id != '{ entity.get('_id') }'
						FILTER v.location IN [{ ",".join(["'" + location.get('_id') + "'" for location in location_hierarchy]) }]
						RETURN {{
							id: v._id,
							depth: LENGTH(p.edges)
						}}
					)
					LET max_depth = MAX(archetypes[*].depth) + 1
					FOR entity IN archetypes
						FOR trait, traitsetting IN OUTBOUND entity.id TraitSettings
						COLLECT traitId = traitsetting._to INTO traitsettings
					FOR t IN Traits
						FILTER traitsettings[0].traitsetting._to == t._id
						FILTER t.traitset == '{ parent.id }'
						{ sorting }
					FOR ts IN traitsettings
					RETURN {{
						max: max_depth,
						entity: ts.entity,
						traitsetting: ts.traitsetting
					}}"""
				# logger.info(f"Traitset.resolve_traits:\tarchetype query: { query }")
				inherited_trait_settings = [doc for doc in db.aql.execute(query)]
				inherited_trait_settings = [
					{
						'max': ts.get('max') or 0,
						'entity_depth': ts.get('entity').get('depth') or 0,
						**ts.get('traitsetting')
					}
					for ts in inherited_trait_settings
				]
				inherited_trait_settings = filter_trait_settings_by_location(inherited_trait_settings, location_id)

				result = [
					Trait(
						id=ts.get('_to'),
						trait_setting_id=ts.get('_id'),
						trait_setting=TraitSetting(
							id=ts.get('_id'),
							priority=0 if ts == direct_trait_settings else ts.get('max') - ts.get('entity_depth')
						)
					)
					for ts in direct_trait_settings + inherited_trait_settings
				]
				return result

				# return [Trait(
				# 		id=trait_setting.get('_to'),
				# 		trait_setting_id=trait_setting.get('_id'),
				# 		trait_setting=TraitSetting(
				# 			id=trait_setting.get('_id'),
				# 			priority=trait_setting.get('entity_depth'),
				# 		)
				# 	) for trait_setting in inherited_trait_settings]


			# neither entity nor relation
			else:
				# logger.info(f"Traitset.resolve_traits:\tNo entity or relation found")
				return []

		elif info.context.get('entity_id') is None:
			# logger.info(f"Traitset.resolve_traits:\tResolving traits for traitsets irrespective of entity")
			query = f"""FOR trait IN Traits
				FILTER trait.traitset == '{ parent.id }'
				SORT trait.name ASC
				RETURN {{ 'id': trait._id, 'name': trait.name }}"""
			cursor = db.aql.execute(query)
			if not cursor.empty():
				result = [
					Trait(id=doc['id'], name=doc['name'])
					for doc in cursor
				]
			else:
				result = []
			return result

		else:
			return []

	def resolve_sfxs(parent, info):
		sfxs = get_doc_by_id('Traitsets', parent.id).get('sfxs')
		if sfxs is not None:
			return [SFX(id=sfx) for sfx in sfxs]
		else:
			return []

	def resolve_default_trait_setting(parent, info):
		setting = db.collection('TraitSettings').find({'_from': parent.id, '_to': 'Traits/1'})
		if setting.count() == 0:
			# logger.info("resolve_default_trait_setting:\tdefault trait")
			setting = db.collection('TraitSettings').find({'_from': 'Traits/1', '_to': 'Traits/1'})
		return [TraitSetting(id=setting['_id']) for setting in setting][0]

	def resolve_initial_xp(parent, info):
		traitset = get_doc_by_id('Traitsets', parent.id)
		if traitset.get('initial_xp') is not None:
			return traitset.get('initial_xp')
		return 0

	def resolve_score(parent, info):
		logging.warning("traitset\tscore:\tusing deprecated function")
		if info.context.get('entity_id') is not None:
			set_query = f"""LET Scores = [
					{{ 'rating': -5, 'score': -8 }},
					{{ 'rating': -4, 'score': -5 }},
					{{ 'rating': -3, 'score': -3 }},
					{{ 'rating': -2, 'score': -2 }},
					{{ 'rating': -1, 'score': -1 }},
					{{ 'rating': 1, 'score': 1 }},
					{{ 'rating': 2, 'score': 2 }},
					{{ 'rating': 3, 'score': 3 }},
					{{ 'rating': 4, 'score': 5 }},
					{{ 'rating': 5, 'score': 8 }}
				]
				RETURN SUM(
					FOR setting IN TraitSettings
						FILTER '{ info.context.get('entity_id') }' == setting._from
					FOR trait IN Traits
						FILTER setting._to == trait._id
						FILTER trait.traitset == '{ parent.id }'
						FOR r IN setting.rating
							FOR s IN Scores
								FILTER r == s.rating
								RETURN s.score
				)"""
			# logger.info("(005) using query: ", set_query)
			set_cursor = db.aql.execute(set_query)
			result = [doc for doc in set_cursor][0]
			return result
		return 0

	def resolve_traitset_setting(parent, info):
		# logger.info(f"Traitset.resolve_traitset_settings")
		if info.context.get('entity_id') is not None:
			# logger.info(f"Traitset.resolve_traitset_settings:\tentity_id: { info.context.get('entity_id') }")
			traitset_settings = db.collection('TraitsetSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			if not traitset_settings.empty():
				traitset_setting = [doc for doc in traitset_settings][0]
				# logger.info(f"Traitset.resolve_traitset_settings:\ttraitset_setting: { traitset_setting }")
				return TraitsetSetting(id=traitset_setting.get('_id'), limit=traitset_setting.get('dicepool_limit'))
		else:
			return None

class CreateTraitset(Mutation):
	class Arguments:
		name = String(required=True)
		entity_types = List(String)
		order = Int(required=False)

	traitset = Field(Traitset)

	def mutate(self, info, name=None, entity_types=None, order=50):
		new_traitset = db.collection('Traitsets').insert({
			'name': name,
			'entity_types': entity_types,
			'dicepool_limit': 1,
			'order': order,
			'duplicates': False
		})

		for entity_type in entity_types:
			entities = db.collection('Entities').find({'type': entity_type})
			for entity in entities:
				db.collection('TraitsetSettings').insert({
					'_from': entity.get('_id'),
					'_to': new_traitset.get('_id'),
					'dicepool_limit': 1
				})

		return CreateTraitset(traitset=Traitset(id=new_traitset.get('_id')))

class TraitsetInput(InputObjectType):
	name = String(required=False)
	explainer = String(required=False)
	entity_types = List(String)
	location_restricted = Boolean(required=False)
	limit = Int(required=False)
	initial_xp = Int(required=False)
	order = Int(required=False)
	duplicates = Boolean(required=False)
	sfxs = List(ID)

class MutateTraitset(Mutation):
	class Arguments:
		traitset_id = ID(required=True)
		traitset_input = TraitsetInput(required=True)

	traitset = Field(Traitset)
	message = String()

	def mutate(self, info, traitset_id=None, traitset_input=None):
		ts = get_doc_by_id('Traitsets', traitset_id)
		traitset_settings = db.collection('TraitsetSettings').find({'_to': traitset_id}) if traitset_id is not None else None

		# rename limit to dicepool_limit
		if 'limit' in traitset_input:
			traitset_input['dicepool_limit'] = traitset_input.pop('limit')
			if traitset_settings is not None:
				for setting in traitset_settings:
					if setting.get('dicepool_limit') < traitset_input.get('dicepool_limit'):
						update_doc('TraitsetSettings', setting, {'dicepool_limit': traitset_input.get('dicepool_limit')})
		
		if 'sfxs' in traitset_input:
			# remove old sfxs from traitset settings if removed from traitset
			# first check which sfxs have been removed from the traitset
			if traitset_settings is not None and ts.get('sfxs') is not None:
				for sfx in ts.get('sfxs'):
					if sfx not in traitset_input.get('sfxs'):
						# then remove them from the traitset settings
						for setting in traitset_settings:
							if sfx in setting.get('sfxs'):
								update_doc('TraitsetSettings', setting, {'sfxs': [s for s in setting.get('sfxs') if s != sfx]})

			# add new sfxs to traitset settings if added to traitset and not yet present in traitset settings
			if traitset_settings is not None and ts.get('sfxs') is not None:
				for sfx in traitset_input.get('sfxs'):
					if sfx not in ts.get('sfxs'):
						for setting in traitset_settings:
							if sfx not in setting.get('sfxs'):
								update_doc('TraitsetSettings', setting, {'sfxs': setting.get('sfxs') + [sfx]})

		ts = {**ts, **traitset_input}
		update_doc('Traitsets', ts)
		return MutateTraitset(traitset=Traitset(id=ts.get('_id')), message="Traitset updated")

class DeleteTraitset(Mutation):
	class Arguments:
		traitset_id = ID(required=True)

	message = String()
	success = Boolean()

	def mutate(self, info, traitset_id=None):
		traits = db.collection('Traits').find({'traitset': traitset_id})
		if not traits.empty():
			for trait in traits:
				default_trait_setting = db.collection('TraitSettings').find({'_from': trait.get('_id'), '_to': 'Traits/1'})
				if not default_trait_setting.empty():
					for default in default_trait_setting:
						db.collection('TraitSettings').delete(default.get('_id'))
				trait_settings = db.collection('TraitSettings').find({'_to': trait.get('_id')})
				if not trait_settings.empty():
					for trait_setting in trait_settings:
						db.collection('TraitSettings').delete(trait_setting.get('_id'))
				db.collection('Traits').delete(trait.get('_id'))
		traitset_default = db.collection('TraitSettings').find({'_from': traitset_id, '_to': 'Traits/1'})
		if not traitset_default.empty():
			for default in traitset_default:
				db.collection('TraitSettings').delete(default.get('_id'))
		traitset_settings = db.collection('TraitsetSettings').find({'_to': traitset_id})
		if not traitset_settings.empty():
			for traitset_setting in traitset_settings:
				db.collection('TraitsetSettings').delete(traitset_setting.get('_id'))
		db.collection('Traitsets').delete(traitset_id)

		return DeleteTraitset(message="Traitset deleted", success=True)

class UpdateTraitsetDefault(Mutation):
	class Arguments:
		traitset_id = ID(required=True)
		default_settings = TraitSettingInput(required=True)

	traitset = Field(lambda: Traitset)

	def mutate(root, info, traitset_id, default_settings):
		if default_settings.rating_type is None:
			default_settings.rating_type = 'empty'
		if default_settings.rating is None:
			default_settings.rating = []
		if default_settings.locations_enabled is None:
			default_settings.locations_enabled = []
		if default_settings.locations_disabled is None:
			default_settings.locations_disabled = []
		if default_settings.sfxs is None:
			default_settings.sfxs = []
		if default_settings.hidden is None:
			default_settings.hidden = False
		else:
			traitset_traits = db.collection('Traits').find({'traitset': traitset_id})
			for trait in traitset_traits:
				default_trait_settings = db.collection('TraitSettings').find({'_from': trait.get('_id'), '_to': 'Traits/1'})
				for default_trait_setting in default_trait_settings:
					default_trait_setting['hidden'] = default_settings.hidden
					update_doc('TraitSettings', default_trait_setting)
		# logger.info("Updating default trait setting for traitset: ", traitset_id, " to: ", default_settings)
		if db.collection('TraitSettings').find({'_from': traitset_id, '_to': 'Traits/1'}).count() == 1:
			db.collection('TraitSettings').update_match(
				{'_from': traitset_id, '_to': 'Traits/1'},
				{
					'rating_type': default_settings.rating_type,
					'rating': default_settings.rating,
					'locations_enabled': default_settings.locations_enabled,
					'locations_disabled': default_settings.locations_disabled,
					'sfxs': default_settings.sfxs,
					'hidden': default_settings.hidden
				}
			)
		else:
			db.collection('TraitSettings').insert(
				{
					'_from': traitset_id,
					'_to': 'Traits/1',
					'rating_type': default_settings.rating_type,
					'rating': default_settings.rating,
					'locations_enabled': default_settings.locations_enabled,
					'locations_disabled': default_settings.locations_disabled,
					'sfxs': default_settings.sfxs,
					'hidden': default_settings.hidden
				}
			)
		# if default_settings.get('rating') is not None and default_settings.get('rating_type') is not None:
		# 	traits = db.collection('Traits').find({'traitset': traitset_id})
		# 	for trait in traits:
		# 		if trait.get('rating') is None and trait.get('rating_type') is not None:
		# 			db.collection('TraitSettings').update_match(
		# 				{ '_to': trait.get('_id') },
		# 				{ 'rating_type': default_settings.get('rating_type'), 'rating': default_settings.get('rating') }
		# 			)
		# 			db.collection('TraitSettings').update_match(
		# 				{ '_from': trait.get('_id'), '_to': 'Traits/1' },
		# 				{ 'rating_type': default_settings.get('rating_type'), 'rating': default_settings.get('rating') }
		# 			)
		return UpdateTraitsetDefault(traitset=Traitset(id=traitset_id))

class TraitsetSetting(ObjectType):
	id = ID()
	entity = Field(lambda: Entity)
	traitset = Field(lambda: Traitset)
	limit = Int()
	sfxs = List(lambda: SFX)

	def resolve_entity(parent, info):
		entity_id = get_doc_by_id('TraitsetSettings', parent.id).get('_from')
		if entity_id.startswith('Entities/'):
			entity = get_doc_by_id('Entities', entity_id)
			if entity.get('type') == 'character':
				return Character(id=entity_id)
			elif entity.get('type') == 'npc':
				return NPC(id=entity_id)
			elif entity.get('type') == 'asset':
				return Asset(id=entity_id)
			elif entity.get('type') == 'faction':
				return Faction(id=entity_id)
			else:
				return None
		else:
			return None
	
	def resolve_traitset(parent, info):
		traitset_id = get_doc_by_id('TraitsetSettings', parent.id).get('_to')
		return Traitset(id=traitset_id)

	def resolve_limit(parent, info):
		return get_doc_by_id('TraitsetSettings', parent.id).get('dicepool_limit')

	def resolve_sfxs(parent, info):
		sfx_ids = get_doc_by_id('TraitsetSettings', parent.id).get('sfxs')
		if sfx_ids is not None:
			return [SFX(id=sfx) for sfx in sfx_ids]
		else:
			return []

class TraitsetSettingInput(InputObjectType):
	limit = Int()
	sfxs = List(ID)

class UpdateTraitsetSetting(Mutation):
	class Arguments:
		traitset_id = ID(required=False)
		entity_id = ID(required=False)
		traitset_setting_id = ID(required=False)
		traitset_setting_input = TraitsetSettingInput(required=True)

	traitset_setting = Field(lambda: TraitsetSetting)

	def mutate(root, info, traitset_id=None, entity_id=None, traitset_setting_id=None, traitset_setting_input=None):
		if traitset_id and entity_id:
			tss = db.collection('TraitsetSettings').find({'_from': entity_id, '_to': traitset_id})
			tss = next((doc for doc in tss), None)
		else:
			tss = get_doc_by_id('TraitsetSettings', traitset_setting_id)

		# rename limit to dicepool_limit
		if 'limit' in traitset_setting_input:
			traitset_setting_input['dicepool_limit'] = traitset_setting_input.pop('limit')

		if tss:
			tss = { **tss, **traitset_setting_input }
			update_doc('TraitsetSettings', tss)
			return UpdateTraitsetSetting(traitset_setting=TraitsetSetting(id=traitset_setting_id))
		else:
			db.collection('TraitsetSettings').insert(
				{
					'_from': entity_id,
					'_to': traitset_id,
					**traitset_setting_input
				}
			)
			return UpdateTraitsetSetting(traitset_setting=TraitsetSetting(id=traitset_setting_id))


class Portrait(ObjectType):
	path = String(required=True)
	ext = String(required=True)
	size = String(required=True)
	width = Int()
	height = Int()

	@classmethod
	def _hydrate_size(cls, parent, info):
		from PIL import Image
		img = Image.open(f"{app.config['UPLOAD_FOLDER']}/{parent.path}/{parent.size}{parent.ext}")
		parent.width = img.width
		parent.height = img.height

	def resolve_width(parent, info):
		if parent.width is None:
			Portrait._hydrate_size(parent, info)
		return parent.width

	def resolve_height(parent, info):
		if parent.height is None:
			Portrait._hydrate_size(parent, info)
		return parent.height

class Entity(Interface):
	id = ID(required=True)
	key = ID()
	name = String()
	description = String()
	image = Field(lambda: Portrait)
	imagening = Boolean()
	imagened = Boolean()
	entity_type = String()
	traitsets = List(lambda: Traitset)
	traits = List(lambda: Trait)
	location = Field(lambda: Location)
	following = Field(lambda: Entity)
	followers = List(lambda: Entity)
	relations = List(lambda: Relation)
	favorite = Boolean()
	is_archetype = Boolean()
	archetype = Field(lambda: Entity)
	archetypes = List(lambda: Entity)
	instances = List(lambda: Entity)
	active = Boolean()
	hidden = Boolean()
	known_to = List(lambda: Entity)

	@classmethod
	def _resolve_type(cls, instance, info):
		if instance.entity_type in ['character', 'gm']:
			return lambda: Character
		elif instance.entity_type == 'location':
			return lambda: Location
		elif instance.entity_type == 'faction':
			return lambda: Faction
		elif instance.entity_type == 'asset':
			return lambda: Asset
		elif instance.entity_type == 'npc':
			return lambda: NPC
		else:
			return lambda: Entity

	@classmethod
	def _hydrate_entity(cls, parent, info):
		if hasattr(parent, '_hydrated'):
			return
		
		entity = get_doc_by_id('Entities', parent.id)
		parent.key = entity.get('_key')
		parent.name = entity.get('name')
		parent.description = entity.get('description')
		parent.entity_type = entity.get('type')
		parent.favorite = entity.get('favorite')
		parent.is_archetype = entity.get('is_archetype')
		parent.active = entity.get('active') or False
		parent.hidden = entity.get('hidden') or False

		parent._hydrated = True

	def resolve_key(parent, info):
		Entity._hydrate_entity(parent, info)
		return str(parent.key)

	def resolve_name(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.name

	def resolve_description(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.description

	def resolve_image(parent, info):
		# logger.info("Resolving image: ", parent.key)
		if not parent.key:
			Entity._hydrate_entity(parent, info)
		
		location_key = None
		if not parent.location:
			if parent.entity_type != 'location':
				location_id = get_doc_by_id('Entities', parent.id).get('location')
				location = get_doc_by_id('Entities', location_id)
				if location.get('type') != 'location':
					# if following
					location_id = location.get('location')
					location = get_doc_by_id('Entities', location_id)
				parent.location = Location(id=location.get('_id'), key=location.get('_key'))
				location_hierarchy = retrieve_hierarchy(parent.location.id)
				if len(location_hierarchy) > 1:
					location_key = location_hierarchy[-2].get('_key')
				else:
					location_key = location_hierarchy[0].get('_key')
			else: # if location
				parents = [rel.get('_to') for rel in db.collection('Relations').find({ '_from': parent.id, 'type': 'super' })]
				if len(parents) > 0:
					location_id = parents[0]
					location = get_doc_by_id('Entities', location_id)
					parent.location = Location(id=location.get('_id'), key=location.get('_key'))
					location_hierarchy = retrieve_hierarchy(parent.location.id)
					if len(location_hierarchy) > 1:
						location_key = location_hierarchy[-2].get('_key')
					else:
						location_key = location_hierarchy[0].get('_key')
		if parent.entity_type != 'location' and location_key is not None and os.path.isdir(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{str(location_key)}"):
			# logger.info("Resolving image 2: ", parent.key, "/", location_key)
			old_file = os.listdir(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{str(location_key)}")[0]
			ext = os.path.splitext(old_file)[1]
			save_image(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{str(location_key)}/{old_file}", parent.key, location_key)
			os.remove(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{str(location_key)}/{old_file}")
			os.rmdir(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{str(location_key)}")
			os.rmdir(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}")
			# return f"{str(parent.key)}/{str(location_key)}/original{ext}"
			return Portrait(path=f"{str(parent.key)}/{str(location_key)}/", size="original", ext=ext)
		elif parent.entity_type != 'location' and location_key is not None and os.path.isdir(f"{app.config['UPLOAD_FOLDER']}/{str(parent.key)}/{str(location_key)}"):
			# logger.info("Resolving image 3: ", parent.key, "/", location_key)
			for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
				if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{str(parent.key)}/{str(location_key)}/original{ext}"):
					# return f"{str(parent.key)}/{str(location_key)}/original{ext}"
					return Portrait(path=f"{str(parent.key)}/{str(location_key)}/", size="original", ext=ext)
		elif os.path.isdir(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}"):
			logger.info("Resolving image 4: ", parent.key)
			old_file = os.listdir(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}")[0]
			logger.info("old_file: ")
			logger.info(old_file)
			ext = os.path.splitext(old_file)[1]
			# os.rename(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{old_file}", f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/original.jpg")
			save_image(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{old_file}", parent.key)
			os.remove(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}/{old_file}")
			os.rmdir(f"{app.config['IMAGEN_FOLDER']}/{str(parent.key)}")
			# return f"{str(parent.key)}/original{ext}"
			return Portrait(path=f"{str(parent.key)}/", size="original", ext=ext)
		else:
			# logger.info("Resolving image 5: ", parent.key)
			for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
				if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{str(parent.key)}/original{ext}"):
					# return f"{str(parent.key)}/original{ext}"
					return Portrait(path=f"{str(parent.key)}/", size="original", ext=ext)
				elif parent.entity_type == 'location' and parent.location is not None:
					if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{parent.location.key}/original{ext}"):
						# return f"{parent.location.key}/original{ext}"
						return Portrait(path=f"{parent.location.key}/", size="original", ext=ext)
					else:
						return None
				# elif (archetype_id := get_doc_by_id('Entities', parent.id).get('archetype_id')) is not None:
				elif not db.collection('Relations').find({ '_from': parent.id, 'type': 'archetype' }).empty():
					archetype_id = [rel.get('_to') for rel in db.collection('Relations').find({ '_from': parent.id, 'type': 'archetype' })][0]
					archetype = get_doc_by_id('Entities', archetype_id)
					if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{archetype.get('_key')}/{str(location_key)}/original{ext}"):
						# return f"{archetype.get('_key')}/{str(location_key)}/original{ext}"
						return Portrait(path=f"{archetype.get('_key')}/{str(location_key)}/", size="original", ext=ext)
					elif os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{archetype.get('_key')}/original{ext}"):
						# return f"{archetype.get('_key')}/original{ext}"
						return Portrait(path=f"{archetype.get('_key')}/", size="original", ext=ext)
					else:
						return None
				else:
					return None

	def resolve_imagening(parent, info):
		"""prevents the user from running image generation while busy"""
		return get_doc_by_id('Entities', parent.id).get('imagening')

	def resolve_imagened(parent, info):
		""""""
		if parent.entity_type is None:
			entity = get_doc_by_id('Entities', parent.id)
			parent.entity_type = entity.get('type')
			parent.name = entity.get('name') if entity.get('name') is not None else parent.name
			parent.description = entity.get('description') if entity.get('description') is not None else parent.description
		if parent.entity_type == 'character':
			if parent.location is None:
				location_id = get_doc_by_id('Entities', parent.id).get('location')
				location = get_doc_by_id('Entities', location_id)
				if location.get('type') != 'location':
					# if following
					location_id = location.get('location')
					location = get_doc_by_id('Entities', location_id)
				parent.location = Location(id=location.get('_id'), name=location.get('name'), description=location.get('description'))
				location_hierarchy = retrieve_hierarchy(parent.location.id)
				if len(location_hierarchy) > 1:
					location_key = location_hierarchy[-2].get('_key')
				if os.path.isdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{location_key}"):
					return True
		return False

	def resolve_entity_type(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.entity_type

	def resolve_traitsets(parent, info):
		# entity type required to filter sets
		if parent.entity_type is None:
			Entity._hydrate_entity(parent, info)
		
		# retrieve all populated sets
		query = f"""LET archetypes = (
						FOR v, e, p IN 0..5 OUTBOUND '{ parent.id }' Relations
						FILTER p.edges[*].type ALL == 'archetype'
						RETURN v._id
					)
					FOR entity IN archetypes
						FOR trait, traitsetting IN OUTBOUND entity TraitSettings
						COLLECT traitId = traitsetting._to INTO traitsettings
					FOR t IN Traits
						FILTER traitsettings[0].traitsetting._to == t._id
					FOR set IN Traitsets
						FILTER t.traitset == set._id
						FILTER '{ parent.entity_type }' IN set.entity_types
					SORT set.order ASC
					RETURN MERGE(
						traitsettings[0].traitsetting,
						{{ traitset: t.traitset }}
					)"""
		cursor = db.aql.execute(query)
		trait_settings = [doc for doc in cursor]
		location = retrieve_location(get_doc_by_id('Entities', parent.id))
		# logger.info(f"Entity\n\tresolve_traitsets:\n\t\tretrieved {len(trait_settings)} trait settings, now filtering by location { location.get('name') }")
		filtered_trait_settings = filter_trait_settings_by_location(trait_settings, location.get('_id'))
		unique_traitsets = []
		for traitsetting in filtered_trait_settings:
			traitset_id = traitsetting.get('traitset')
			if traitset_id not in unique_traitsets:
				unique_traitsets.append(traitset_id)
		# logger.info(f"Entity\n\tresolve_traitsets:\n\t\tfiltered to {len(unique_traitsets)} trait sets")
		
		# retrieve unpopulated sets, filtered by location
		query = f"""FOR set IN Traitsets
						FILTER '{ parent.entity_type }' IN set.entity_types
						FILTER set._id NOT IN {unique_traitsets}
					FOR default IN TraitSettings
						FILTER set._id == default._from
						FILTER default._to == 'Traits/1'
					SORT set.order ASC
					RETURN {{
						traitset: set._id,
						locations_enabled: default.locations_enabled,
						locations_disabled: default.locations_disabled
					}}"""
		cursor = db.aql.execute(query)
		unpopulated_traitsets = [doc for doc in cursor]
		# logger.info(f"Entity\n\tresolve_traitsets:\n\t\tretrieved {len(unpopulated_traitsets)} unpopulated trait sets, now filtering by location { location.get('name') }")
		filtered_unpopulated_traitsets = filter_trait_settings_by_location(unpopulated_traitsets, location.get('_id'))
		for traitsetting in filtered_unpopulated_traitsets:
			traitset_id = traitsetting.get('traitset')
			if traitset_id not in unique_traitsets:
				unique_traitsets.append(traitset_id)
		# logger.info(f"Entity\n\tresolve_traitsets:\n\t\tfiltered to {len(unique_traitsets)} trait sets")
		return [Traitset(id=traitset) for traitset in unique_traitsets]
	
	def resolve_traits(parent, info):
		trait_settings = [setting for setting in db.collection('TraitSettings').find({'_from': parent.id})]
		location = retrieve_location(get_doc_by_id('Entities', parent.id))
		archetype_ids = db.collection('Relations').find({'_from': parent.id, 'type': 'archetype'})
		for archetype in archetype_ids:
			archetype_trait_settings = db.collection('TraitSettings').find({'_from': archetype.get('_to')})
			for ats in archetype_trait_settings:
				trait_settings.append(ats)
		filtered_trait_settings = filter_trait_settings_by_location(trait_settings, location.get('_id'))
		return [Trait(id=setting.get('_to')) for setting in filtered_trait_settings]

	def resolve_location(parent, info):
		entity = get_doc_by_id('Entities', parent.id)
		location = retrieve_location(entity)
		if location.get('_id') is not None:
			return Location(id=location.get('_id'))
		else:
			return None

	def resolve_following(parent, info):
		loc_id = get_doc_by_id('Entities', parent.id).get('location')
		if not loc_id:
			return None
		loc = get_doc_by_id('Entities', loc_id)
		if loc.get('type') == 'asset':
			return Asset(id=loc.get('_id'))
		elif loc.get('type') == 'character':
			return Character(id=loc.get('_id'))
		elif loc.get('type') == 'npc':
			return NPC(id=loc.get('_id'))
		elif loc.get('type') == 'faction':
			return Faction(id=loc.get('_id'))
		else:
			return None

	def resolve_followers(parent, info):
		result = []
		following_entities = db.collection('Entities').find({'location': parent.id})
		for entity in following_entities:
			if entity.get('type') == 'character':
				result.append(Character(id=entity.get('_id')))
			elif entity.get('type') == 'npc':
				result.append(NPC(id=entity.get('_id')))
			elif entity.get('type') == 'asset':
				result.append(Asset(id=entity.get('_id')))
			elif entity.get('type') == 'faction':
				result.append(Faction(id=entity.get('_id')))
		return result

	def resolve_relations(parent, info):
		query = f"""FOR relation IN Relations
			FILTER relation._from == '{parent.id}'
			FOR e IN Entities
			FILTER e._id == relation._to
			FILTER relation.type == 'relation'
			SORT relation.favorite DESC, POSITION(['character', 'npc', 'asset', 'faction', 'location'], e.type, true) ASC, e.name ASC

			RETURN relation"""
		# logger.info("query: ", query)
		cursor = db.aql.execute(query)
		# relations = db.collection('Relations').find({'_from': parent.id})
		return [Relation(id=doc['_id']) for doc in cursor]

	def resolve_favorite(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.favorite

	def resolve_is_archetype(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.is_archetype

	def resolve_archetype(parent, info):
		# archetype_id = get_doc_by_id('Entities', parent.id).get('archetype_id')
		if not (archetypes := db.collection('Relations').find({'_from': parent.id, 'type': 'archetype'})).empty():
			archetype_id = [archetype.get('_to') for archetype in archetypes][0]
			if archetype_id is not None:
				archetype = get_doc_by_id('Entities', archetype_id)
				if archetype.get('type') == 'character':
					return Character(id=archetype_id)
				elif archetype.get('type') == 'npc':
					return NPC(id=archetype_id)
				elif archetype.get('type') == 'asset':
					return Asset(id=archetype_id)
				elif archetype.get('type') == 'faction':
					return Faction(id=archetype_id)
		else:
			return None

	def resolve_archetypes(parent, info):
		result = []
		archetypes = db.collection('Relations').find({'_from': parent.id, 'type': 'archetype'})
		for archetype in archetypes:
			archetype_id = archetype.get('_to')
			if archetype_id is not None:
				archetype = get_doc_by_id('Entities', archetype_id)
				if archetype.get('type') == 'character':
					result.append(Character(id=archetype_id))
				elif archetype.get('type') == 'npc':
					result.append(NPC(id=archetype_id))
				elif archetype.get('type') == 'asset':
					result.append(Asset(id=archetype_id))
				elif archetype.get('type') == 'faction':
					result.append(Faction(id=archetype_id))
		return result

	def resolve_instances(parent, info):
		"""
		Returns all instances of this entity
		"""
		if not hasattr(parent, '_hydrated'):
			Entity._hydrate_entity(parent, info)
		if not parent.is_archetype:
			return []
		result = []
		# cursor = db.collection('Entities').find({'archetype_id': parent.id})
		query = f"""FOR relation IN Relations
			FILTER relation._to == '{parent.id}'
			FOR e IN Entities
			FILTER e._id == relation._from
			FILTER relation.type == 'archetype'
			SORT relation.favorite DESC, POSITION(['character', 'npc', 'asset', 'faction', 'location'], e.type, true) ASC, e.name ASC

			RETURN e"""
		cursor = db.aql.execute(query)
		for entity in cursor:
			if entity.get('type') == 'character':
				result.append(Character(id=entity.get('_id')))
			elif entity.get('type') == 'npc':
				result.append(NPC(id=entity.get('_id')))
			elif entity.get('type') == 'asset':
				result.append(Asset(id=entity.get('_id')))
			elif entity.get('type') == 'faction':
				result.append(Faction(id=entity.get('_id')))
		return result

	def resolve_active(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.active

	def resolve_hidden(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.hidden or False

	def resolve_known_to(parent, info):
		known_to = get_doc_by_id('Entities', parent.id).get('known_to', [])
		result = []
		changed = False
		for entity_id in known_to:
			entity = get_doc_by_id('Entities', entity_id)
			if entity is None:
				known_to.remove(entity_id)
				changed = True
				continue
			if entity.get('type') == 'character':
				result.append(Character(id=entity_id))
			elif entity.get('type') == 'npc':
				result.append(NPC(id=entity_id))
			elif entity.get('type') == 'asset':
				result.append(Asset(id=entity_id))
			elif entity.get('type') == 'faction':
				result.append(Faction(id=entity_id))
		if changed:
			update_doc('Entities', {'_id': parent.id, 'known_to': known_to})
		return result

class EntityInput(InputObjectType):
	name = String()
	entity_type = String()
	location = ID()
	pp = Int()
	active = Boolean()
	hidden = Boolean()
	show_to = List(ID)
	known_to = List(ID)

class CreateEntity(Mutation):
	class Arguments:
		name = String(required=True)
		entity_type = String(required=True)
		location = ID()

	entity = Field(lambda: Entity)

	def mutate(root, info, name, entity_type, location='Entities/2'):
		entity = db.collection('Entities').insert({'name': name, 'type': entity_type, 'location': location, 'pp': 1, 'favorite': False})

		# create traitset settings
		# query = f"""FOR traitset IN Traitsets
		# 	FILTER '{entity_type}' IN traitset.entity_types
		# 	RETURN traitset"""
		# traitsets = [doc for doc in db.aql.execute(query)]
		# for traitset in traitsets:
		# 	db.collection('TraitsetSettings').insert({
		# 		'_from': entity.get('_id'),
		# 		'_to': traitset.get('_id'),
		# 		'dicepool_limit': traitset.get('dicepool_limit'),
		# 		'sfxs': traitset.get('sfxs')
		# 	})

		if entity_type == 'location':
			result = Location(id=entity.get('_id'))
		elif entity_type in ['character', 'gm']:
			result = Character(id=entity.get('_id'))
		elif entity_type == 'faction':
			result = Faction(id=entity.get('_id'))
		elif entity_type == 'asset':
			result = Asset(id=entity.get('_id'))
		elif entity_type == 'npc':
			result = NPC(id=entity.get('_id'))
		else:
			raise Exception("unknown entity type: ", entity_type)
		return CreateEntity(entity=result)

class UpdateEntity(Mutation):
	class Arguments:
		entity_id = ID(required=True)
		name = String()
		location = ID()
		following = ID()
		favorite = Boolean()
		is_archetype = Boolean()
		active = Boolean()
		entity_input = EntityInput()

	entity = Field(lambda: Entity)

	def mutate(root, info, entity_id, entity_input=None, name=None, location=None, following=None, favorite=None, is_archetype=None, active=None):
		entity = get_doc_by_id('Entities', entity_id)
		# logger.info(f"UpdateEntity.mutate:\t0\tparameters:\t{ locals() }")
		changes = {}
		if name is not None:
			changes['name'] = name
		
		# the entity changes location
		if (location or (entity_input and entity_input.get('location'))) and entity.get('type') != 'location':
			changes['location'] = location or entity_input.pop('location')
			# logger.info(f"UpdateEntity.mutate:\t1\tchanges: { changes }")
			location_doc = get_doc_by_id('Entities', changes.get('location'))
			
			# if the entity changes to a location,
			# especially if that location is 'hidden'
			# the entity henceforth knows about and how to reach this location
			known_to = location_doc.get('known_to') or []
			if entity.get('_id') not in known_to:
				known_to.append(entity.get('_id'))
			location_doc['known_to'] = list(set(known_to))

			update_doc('Entities', location_doc)

		elif (location or (entity_input and entity_input.get('location'))) and entity.get('type') == 'location':
			zones = db.collection('Relations').find({'_from': entity.get('_id'), 'type': 'super'})
			zone = [doc for doc in zones][0]
			zone['_to'] = location or entity_input.pop('location')
			update_doc('Relations', zone)

		# logger.info(f"UpdateEntity.mutate:\t3\tchanges: { changes }")
		if following is not None:
			changes['location'] = following

		if favorite is not None:
			changes['favorite'] = favorite

		if is_archetype is not None:
			changes['is_archetype'] = is_archetype

		if active is not None:
			changes['active'] = active

		# logger.info(f"UpdateEntity.mutate:\t4\tchanges: { changes }")
		if entity_input is not None and entity_input.get('show_to') is not None:
			known_to = set(entity.get('known_to', []) + entity_input.pop('show_to', []))
			changes['known_to'] = list(known_to)

		# logger.info(f"UpdateEntity.mutate:\t5\tchanges: { changes }")
		entity = {
			'_id': entity_id,
			**{key: value for key, value in entity.items() if not key.startswith('_')},
			**changes,
			**(entity_input if entity_input is not None else {})
		}

		# logger.info(f"UpdateEntity.mutate:\t6\tentity: { entity }")

		update_doc('Entities', entity)

		if(entity.get('type') == 'location'):
			return UpdateEntity(entity=Location(id=entity.get('_id'), entity_type=entity.get('type')))
		elif(entity.get('type') in ['character', 'gm']):
			return UpdateEntity(entity=Character(id=entity.get('_id'), entity_type=entity.get('type')))
		elif(entity.get('type') == 'faction'):
			return UpdateEntity(entity=Faction(id=entity.get('_id'), entity_type=entity.get('type')))
		elif(entity.get('type') == 'asset'):
			return UpdateEntity(entity=Asset(id=entity.get('_id'), entity_type=entity.get('type')))
		elif(entity.get('type') == 'npc'):
			return UpdateEntity(entity=NPC(id=entity.get('_id'), entity_type=entity.get('type')))
		else:
			return UpdateEntity(entity=Entity(id=entity.get('_id'), entity_type=entity.get('type')))

class InstantiateArchetype(Mutation):
	# instantiate an archetype entity
	# also copies the traits
	# does not copy the relations
	class Arguments:
		entity_id = ID(required=True)
		name = String(required=False)
		location_id = ID(required=False)

	entity = Field(lambda: Entity)
	message = String()

	def mutate(root, info, entity_id, name=None, location_id=None):
		archetype = get_doc_by_id('Entities', entity_id)
		new_entity = {key: value for key, value in archetype.items() if not key.startswith('_')}
		# new_entity['archetype_id'] = archetype.get('_id')
		new_entity['is_archetype'] = False
		if name is not None:
			new_entity['name'] = name
		else:
			name = list(archetype.get('name'))
			random.SystemRandom().shuffle(name)
			new_entity['name'] = ''.join(name)
			new_entity['name'] = ' '.join(s.capitalize() for s in new_entity['name'].split(' '))
		if location_id is not None:
			new_entity['location'] = location_id
		try:
			new_entity_meta = db.collection('Entities').insert(new_entity)
			new_entity = {**new_entity, **new_entity_meta}
		except:
			return InstantiateArchetype(message="error cloning entity", entity=None)
		
		# link instance with archetype
		db.collection('Relations').insert({ '_from': new_entity.get('_id'), '_to': archetype.get('_id'), 'type': 'archetype' })

		# copy traitset settings
		query = f"""FOR entity IN Entities
						FILTER entity._id == '{ entity_id}'

					LET traitsetsettings = (
						FOR ts IN TraitsetSettings
						FILTER entity._id == ts._from
						RETURN ts
					)

					RETURN {{
						entity: entity,
						traitsetsettings: traitsetsettings
					}}"""
		cursor = db.aql.execute(query)
		result = [doc for doc in cursor][0]
		for traitsetsetting in result.get('traitsetsettings'):
			new_traitsetsetting = {key: value for key, value in traitsetsetting.items() if not key.startswith('_')}
			new_traitsetsetting['_from'] = new_entity.get('_id')
			new_traitsetsetting['_to'] = traitsetsetting.get('_to')
			db.collection('TraitsetSettings').insert(new_traitsetsetting)
		
		# copy relations
		relations = db.collection('Relations').find({'_from': archetype.get('_id'), 'type': 'relation'})
		for relation in relations:
			new_relation = {key: value for key, value in relation.items() if not key.startswith('_')}
			new_relation['_from'] = new_entity.get('_id')
			new_relation['_to'] = relation.get('_to')
			new_relation = db.collection('Relations').insert(new_relation)

			traits = db.collection('TraitSettings').find({'_from': relation.get('_id')})
			for trait in traits:
				new_trait = {key: value for key, value in trait.items() if not key.startswith('_')}
				new_trait['_from'] = new_relation.get('_id')
				new_trait['_to'] = trait.get('_to')
				db.collection('TraitSettings').insert(new_trait)

		if new_entity.get('type') == 'character':
			return InstantiateArchetype(entity=Character(id=new_entity.get('_id')), message="entity cloned")
		elif new_entity.get('type') == 'npc':
			return InstantiateArchetype(entity=NPC(id=new_entity.get('_id')), message="entity cloned")
		elif new_entity.get('type') == 'asset':
			return InstantiateArchetype(entity=Asset(id=new_entity.get('_id')), message="entity cloned")
		elif new_entity.get('type') == 'faction':
			return InstantiateArchetype(entity=Faction(id=new_entity.get('_id')), message="entity cloned")
		elif new_entity.get('type') == 'location':
			return InstantiateArchetype(entity=Location(id=new_entity.get('_id')), message="entity cloned")
		else:
			return InstantiateArchetype(message="entity cloned, but type unknown", entity=None)

class DeleteEntity(Mutation):
	class Arguments:
		entity_id = ID(required=True)
		rmtree = Boolean(required=False)

	success = Boolean()
	message = String()

	def mutate(root, info, entity_id, rmtree=False):

		def remove_entity(entity_id):
			# we don't want any dangling relations, so we need to delete those, but because relations
			# can have traits associated with them we need to delete the trait settings associated with those relations too
			# first from this entity
			relations = db.collection('Relations').find({'_from': entity_id})
			for relation in relations:
				traits = db.collection('TraitSettings').find({'_from': relation.get('_id')})
				for trait in traits:
					db.collection('TraitSettings').delete(trait.get('_id'))
				db.collection('Relations').delete(relation.get('_id'))
			# but also to this entity
			relations = db.collection('Relations').find({'_to': entity_id})
			for relation in relations:
				traits = db.collection('TraitSettings').find({'_from': relation.get('_id')})
				for trait in traits:
					db.collection('TraitSettings').delete(trait.get('_id'))
				db.collection('Relations').delete(relation.get('_id'))

			# now we can delete all traits associated directly to this entity
			traits = db.collection('TraitSettings').find({'_from': entity_id})
			for trait in traits:
				db.collection('TraitSettings').delete(trait.get('_id'))

			# if this entity is a location, also remove it from other traits' locations_enabled/disabled
			query = f"""FOR s IN TraitSettings
						FILTER { entity_id } IN s.locations_enabled
						RETURN s"""
			cursor = db.aql.execute(query)
			for doc in cursor:
				doc['locations_enabled'].remove(entity_id)
				if doc['locations_enabled'] == []:
					# if the locations_enabled list is now empty,
					# that means the trait was only available at this location
					# thus we can delete it
					db.collection('TraitSettings').delete(doc['_id'])
				else:
					update_doc('TraitSettings', doc)
			query = f"""FOR s IN TraitSettings
						FILTER { entity_id } IN s.locations_disabled
						RETURN s"""
			cursor = db.aql.execute(query)
			for doc in cursor:
				doc['locations_disabled'].remove(entity_id)
				update_doc('TraitSettings', doc)
			
			# and all traitset settings
			traitset_settings = db.collection('TraitsetSettings').find({'_from': entity_id})
			for traitset_setting in traitset_settings:
				db.collection('TraitsetSettings').delete(traitset_setting.get('_id'))

			# remove the image folder
			shutil.rmtree(f"{app.config['UPLOAD_FOLDER']}/{current_entity.get('_key')}", ignore_errors=True)

			# now we can delete the entity
			db.collection('Entities').delete(entity_id)

		try:
			current_entity = get_doc_by_id('Entities', entity_id)

			# if the entity is a location and only this location needs removing
			# then all entities in that location need their location updated
			# to the parent of this location
			if current_entity.get('type') == 'location' and not rmtree:
				parent = db.collection('Relations').find({'_from': current_entity.get('_id'), 'type': 'super'})
				parent = [doc for doc in parent][0].get('_to')

				# update presence
				db.collection('Entities').update_match({'location': current_entity.get('_id')}, {'location': parent})

				# update zones
				db.collection('Relations').update_match({'_to': current_entity.get('_id'), 'type': 'super'}, {'_to': parent})

				# remove location
				remove_entity(current_entity.get('_id'))
			
			# if the entity is a location and all entities in that location need removing
			elif current_entity.get('type') == 'location' and rmtree:
				# first get all zones of this location
				query = f"""FOR v, e, p IN 0..100 INBOUND "{ current_entity.get('_id') }" Relations
					FILTER p.edges[*].type ALL == 'super'
					RETURN v"""
				cursor = db.aql.execute(query)
				zones = [doc for doc in cursor]

				# then remove all entities in those zones
				for zone in zones:
					# get all entities in that zone first
					entities = db.collection('Entities').find({'location': zone.get('_id')})
					for entity in entities:
						if int(entity.get('_key')) > 100:
							remove_entity(entity.get('_id'))
					# then remove the zone
					remove_entity(zone.get('_id'))

				# finally remove the location
				remove_entity(current_entity.get('_id'))

			# if the entity is not a location
			else:
				remove_entity(current_entity.get('_id'))

			return DeleteEntity(success=True, message="entity deleted")
		except Exception as e:
			return DeleteEntity(success=False, message=f"DeleteEntity failed: {str(e)}")

class Character(ObjectType):
	class Meta:
		interfaces = (Entity,)

	entity_type = 'character'
	score = Int()
	available = Boolean()
	pp = Int()

	def resolve_score(parent, info):

		# this function throws a 'get_location' error and isn't used in the UI any more.
		logging.error("character\tscore:\tusing deprecated function")

		set_query = f"""LET Scores = [
				{{ 'rating': 'd4', 'score': 1 }},
				{{ 'rating': 'd6', 'score': 2 }},
				{{ 'rating': 'd8', 'score': 3 }},
				{{ 'rating': 'd10', 'score': 4 }},
				{{ 'rating': 'd12', 'score': 5 }}
			]
			RETURN SUM(
				FOR setting IN TraitSettings
					FILTER '{ parent.id }' == setting._from
				FOR trait IN Traits
					FILTER setting._to == trait._id
					FILTER trait.traitset != 'Traitsets/906379'
					FOR r IN setting.rating
						FOR s IN Scores
							FILTER r == s.rating
							RETURN s.score
			)"""
		# logger.info("(005) using query: ", set_query)
		set_cursor = db.aql.execute(set_query)
		result = [doc for doc in set_cursor][0]
		return result

	def resolve_available(parent, info):
		if parent.key is None:
			parent.key = get_doc_by_id('Entities', parent.id).get('_key')
		if parent.is_archetype is None:
			parent.is_archetype = get_doc_by_id('Entities', parent.id).get('is_archetype')
		return parent.key not in [d['character'] for d in session_characters] and not parent.is_archetype

	def resolve_pp(parent, info):
		return get_doc_by_id('Entities', parent.id).get('pp')

class CharacterInput(InputObjectType):
	name = String(required=False)
	description = String(required=False)
	location = ID(required=False)
	pp = Int(required=False)
	type = String(required=False)
	is_archetype = Boolean(required=False)

class CreateOrUpdateCharacter(Mutation):
	class Arguments:
		key = ID(required=False)
		input = CharacterInput(required=True)

	character = Field(Character)

	def mutate(self, info, input, key=None):
		# characters_collection = db.collection('Entities')
		# logger.info("mutating character: ", key, " input: ", input)

		if key:
			character_doc = get_doc_by_id('Entities', 'Entities/' + str(key))
			if character_doc:
				# logger.info("updating character: ", input)
				character_doc.update(input)
				update_doc('Entities', character_doc)
				if (location_id := input.get('location')) is not None:
					# logger.info(f"CreateOrUpdateCharacter:\tlocation_id: { location_id }")
					loc_doc = get_doc_by_id('Entities', location_id)
					loc_doc['known_to'] = list(set((loc_doc.get('known_to') or []) + [character_doc.get('_id')]))
					update_doc('Entities', loc_doc)
			else:
				raise Exception('Character not found')
		else:
			if input.get('name') is not None:
				character_doc = input
				if character_doc.get('pp') is None:
					character_doc['pp'] = 1
				character_doc['description'] = ''
				if input.get('type') is None:
					character_doc['type'] = 'character'
				else:
					character_doc['type'] = input['type']
				character_doc['location'] = None
				character_doc = db.collection('Entities').insert(character_doc)
				key = character_doc['_key']
			else:
				raise Exception('Character name not provided')

		return CreateOrUpdateCharacter(character=Character(id=character_doc.get('_id')))

class NPC(ObjectType):
	class Meta:
		interfaces = (Entity,)

	entity_type = 'npc'

class Faction(ObjectType):
	class Meta:
		interfaces = (Entity,)

	entity_type = 'faction'

class Asset(ObjectType):
	class Meta:
		interfaces = (Entity,)

	entity_type = 'asset'

class Location(ObjectType):
	class Meta:
		interfaces = (Entity,)

	entity_type = 'location'
	parent = Field(lambda: Location)
	parents = List(lambda: Location)
	flavortext = String()
	zones = List(lambda: Location)
	transversables = List(lambda: Location)
	entities = List(lambda: Entity)

	def resolve_parent(parent, info):
		if parent.id == 'Entities/2':
			# the root location
			return None
		query = f"""FOR r IN Relations
			FILTER r._from == '{ parent.id }'
			FILTER r.type == 'super'
			RETURN r._to"""
		cursor = db.aql.execute(query)
		parent_id = [doc for doc in cursor]
		if len(parent_id) == 1:
			return Location(id=parent_id[0])
		else:
			raise Exception("location has none or multiple parents: ", parent_id)

	def resolve_parents(parent, info):
		query = f"""FOR v, e, p IN 0..100 OUTBOUND "{ parent.id }" Relations
			FILTER p.edges[*].type ALL == 'super'
			RETURN v._id"""
		cursor = db.aql.execute(query)
		return [Location(id=doc) for doc in cursor]

	def resolve_flavortext(parent, info):
		return get_doc_by_id('Entities', parent.id).get('description')

	def resolve_zones(parent, info):
		# zones = db.collection('Entities').find({'type': 'location', 'location': parent.id})
		query = f"""FOR r IN Relations
			FILTER r._to == '{ parent.id }'
			FILTER r.type == 'super'
			RETURN r._from"""
		zones = db.aql.execute(query)
		return [Location(id=loc) for loc in zones]

	def resolve_transversables(parent, info):
		query = f"""FOR r IN Relations
			FILTER r._from == '{ parent.id }'
			FILTER r.type == 'transversable'
			RETURN r._to"""
		transversables = db.aql.execute(query)
		return [Location(id=loc) for loc in transversables]

	def resolve_entities(parent, info):
		query = f"""FOR e IN Entities
					FILTER e.location == '{ parent.id }'
					SORT POSITION(['character', 'npc', 'asset', 'faction'], e.type, true) ASC, e.name ASC
					RETURN e"""
		cursor = db.aql.execute(query)
		entities = [doc for doc in cursor]
		# check if any entities are being followed
		new_entities = []
		for entity in entities:
			if entity.get('location') is not None and entity.get('type') != 'location':
				followers = db.collection('Entities').find({'location': entity.get('_id')})
				for follower in followers:
					new_entities.append(follower)
		entities.extend(new_entities)

		# active entities need to be added to each other's known_to list if not already there
		active_entities = [entity for entity in entities if entity.get('active')]
		for entity in active_entities:
			character_entities = [entity for entity in active_entities if entity.get('type') == 'character']
			for other_entity in character_entities:
				if other_entity.get('_id') != entity.get('_id') and (entity.get('known_to') or []).count(other_entity.get('_id')) == 0:
					if entity.get('known_to') is None:
						entity['known_to'] = []
					entity['known_to'].append(other_entity.get('_id'))
			update_doc('Entities', entity)

		result = []
		for entity in entities:
			# entity_type =
			if entity['type'] in ['character', 'gm']:
				result.append(Character(id=entity.get('_id')))
			elif entity['type'] == 'faction':
				result.append(Faction(id=entity.get('_id')))
			elif entity['type'] == 'asset':
				result.append(Asset(id=entity.get('_id')))
			elif entity['type'] == 'npc':
				result.append(NPC(id=entity.get('_id')))
			# else:
			# 	raise Exception("unknown entity type: ", entity_type)
		return result
		# return [Entity(id=ett['_id'], entity_type=ett['type']) for ett in entities]

class LocationInput(InputObjectType):
	id = ID()
	location = ID()
	name = String()
	description = String()

class CreateLocation(Mutation):
	class Arguments:
		location_input = LocationInput(required=True)

	location = Field(Location)

	def mutate(self, info, location_input=None):
		# logger.info("Creating location: ", location_input)
		if(location_input):
			location_input['type'] = 'location'
			if location_input.get('description') is None:
				location_input['description'] = ''
			new_location = db.collection('Entities').insert({
				'name': location_input.get('name'),
				'description': location_input.get('description'),
				'type': 'location'
			})
			parent_location = db.collection('Relations').insert({
				'_from': new_location.get('_id'),
				'_to': location_input.get('location'),
				'type': 'super'
			})
			return CreateLocation(location=Location(id=new_location['_id']))
		else:
			raise Exception("No location input provided")

class UpdateLocation(Mutation):
	class Arguments:
		location_id = ID(required=True)
		location_input = LocationInput(required=False)

	location = Field(Location)

	def mutate(self, info, location_id, location_input=None):
		# id = 'Entities' + key
		loc = get_doc_by_id('Entities', location_id)
		if location_input:
			loc = {
				**loc,
				**location_input
			}
			update_doc('Entities', loc)
		return UpdateLocation(location=Location(id=loc['_id']))



class Relation(ObjectType):
	id = ID()
	from_entity = Field(lambda: Entity)
	to_entity = Field(lambda: Entity)
	traitsets = List(lambda: Traitset)
	favorite = Boolean()

	def resolve_from_entity(parent, info):
		entity_id = get_doc_by_id('Relations', parent.id).get('_from')
		entity_type = get_doc_by_id('Entities', entity_id).get('type')
		# logger.info("Relation.resolve_entity:\tentity_id: ", entity_id, "\tentity_type: ", entity_type)
		if entity_type == 'location':
			return Location(id=entity_id)
		elif entity_type in ['character', 'gm']:
			return Character(id=entity_id)
		elif entity_type == 'faction':
			return Faction(id=entity_id)
		elif entity_type == 'npc':
			return NPC(id=entity_id)
		elif entity_type == 'asset':
			return Asset(id=entity_id)
		else:
			raise Exception("unknown entity type: ", entity_id)

	def resolve_to_entity(parent, info):
		entity_id = get_doc_by_id('Relations', parent.id).get('_to')
		entity_type = get_doc_by_id('Entities', entity_id).get('type')
		# logger.info("Relation.resolve_entity:\tentity_id: ", entity_id, "\tentity_type: ", entity_type)
		if entity_type == 'location':
			return Location(id=entity_id)
		elif entity_type in ['character', 'gm']:
			return Character(id=entity_id)
		elif entity_type == 'faction':
			return Faction(id=entity_id)
		elif entity_type == 'npc':
			return NPC(id=entity_id)
		elif entity_type == 'asset':
			return Asset(id=entity_id)
		else:
			raise Exception("unknown entity type: ", entity_id)

	def resolve_traitsets(parent, info):
		traitset_ids = [ts.get('_id') for ts in db.collection('Traitsets').all() if 'relation' in ts.get('entity_types')]
		result = []
		for traitset_id in traitset_ids:
			query = f"""FOR traitsetting IN TraitSettings
						FILTER traitsetting._from == '{parent.id}'
						FOR trait IN Traits
						FILTER traitsetting._to == trait._id
						FILTER trait.traitset == '{traitset_id}'
						RETURN {{ trait: trait._id, traitsetting: traitsetting._id }}"""
			# logger.info("Relation.resolve_traitsets:\tquery: ", query)
			cursor = db.aql.execute(query)
			traits = [Trait(id=doc.get('trait'), trait_setting_id=doc.get('traitsetting')) for doc in cursor]
			result.append(Traitset(id=traitset_id, traits=traits))
		return result

	def resolve_favorite(parent, info):
		return get_doc_by_id('Relations', parent.id).get('favorite')

class CreateRelation(Mutation):
	class Arguments:
		from_id = ID(required=True)
		to_id = ID(required=True)
		type = String()

	success = Boolean()
	message = String()

	def mutate(root, info, from_id=None, to_id=None, type=None):
		if db.collection('Relations').find({'_from': from_id, '_to': to_id, 'type': type}).empty():
			# if type == 'archetype', remove all other archetypes from entity
			# if type == 'archetype':
			# 	db.collection('Relations').delete_match({'_from': from_id, 'type': 'archetype'})
			db.collection('Relations').insert({ '_from': from_id, '_to': to_id, 'type': type, 'favorite': False })
			return CreateRelation(success=True)
		else:
			errorMessage = f"relation already exists, from: { from_id }, to: { to_id }"
			return CreateRelation(success=False, message=errorMessage)

class UpdateRelation(Mutation):
	class Arguments:
		id = ID(required=True)
		favorite = Boolean(required=True)

	relation = Field(lambda: Relation)

	def mutate(self, info, id, favorite):
		relation = get_doc_by_id('Relations', id)
		relation['favorite'] = favorite
		update_doc('Relations', relation)
		return UpdateRelation(relation=Relation(id=id, favorite=favorite))

class DeleteRelation(Mutation):
	class Arguments:
		relation_id = ID()
		from_id = ID()
		to_id = ID()
		type = String()

	success = Boolean()

	def mutate(self, info, relation_id=None, from_id=None, to_id=None, type=None):
		if relation_id is None and from_id is not None and to_id is not None and type is not None:
			relation = db.collection('Relations').find({'_from': from_id, '_to': to_id, 'type': type})
			if relation.empty():
				return DeleteRelation(success=False)
			relation = [r for r in relation][0]
			relation_id = relation.get('_id')
		if relation_id is not None:
			traits = db.collection('TraitSettings').find({'_from': relation_id})
			for trait in traits:
				db.collection('TraitSettings').delete(trait.get('_id'))
			db.collection('Relations').delete(relation_id)
			return DeleteRelation(success=True)
		else:
			return DeleteRelation(success=False)



class Query(ObjectType):
	players = List(Player, key=ID(required=False), player_id=ID(required=False))
	def resolve_players(parent, info, key=None, player_id=None):
		if player_id:
			return [Player(id = player_id)]
		else:
			return [Player(id = doc['_id']) for doc in db.collection('Players').all()]

	session = Field(Session)
	def resolve_session(parent, info):
		return Session()

	characters = List(Character, key=ID(required=False), available=Boolean(required=False))
	def resolve_characters(parent, info, key=None, available=None):
		# logger.info("character resolver, for key: ", key)
		if not key and not available:
			cursor = db.collection('Entities').find({'type': 'character'})
			return [Character(id = doc['_id']) for doc in cursor]
		elif not key and available:
			cursor = db.collection('Entities').get_many([char.get('character') for char in session_characters])
			return [Character(id = doc['_id']) for doc in cursor]
		else:
			character = get_doc_by_id('Entities', 'Entities/' + str(key))
			info.context['entity_id'] = character['_id']
			return [Character(id = character['_id'])]

	factions = List(Faction, key=ID(required=False))
	def resolve_factions(parent, info, key=None):
		if not key:
			cursor = db.collection('Entities').find({'type': 'faction'})
			return [Faction(id = doc['_id']) for doc in cursor]
		else:
			faction = get_doc_by_id('Entities', 'Entities/' + str(key))
			info.context['entity_id'] = faction['_id']
			return [Faction(id = faction['_id'])]

	assets = List(Asset, key=ID(required=False))
	def resolve_assets(parent, info, key=None):
		if not key:
			cursor = db.collection('Entities').find({'type': 'asset'})
			return [Asset(id = doc['_id']) for doc in cursor]
		else:
			asset = get_doc_by_id('Entities', 'Entities/' + str(key))
			info.context['entity_id'] = asset['_id']
			return [Asset(id = asset['_id'])]

	npcs = List(NPC, key=ID(required=False))
	def resolve_npcs(parent, info, key=None):
		if not key:
			cursor = db.collection('Entities').find({'type': 'npc'})
			return [NPC(id = doc['_id']) for doc in cursor]
		else:
			npc = get_doc_by_id('Entities', 'Entities/' + str(key))
			info.context['entity_id'] = npc['_id']
			return [NPC(id = npc['_id'])]

	entities = List(Entity,
				 key=ID(required=False),
				 entity_id=ID(required=False),
				 entity_type=String(required=False),
				 search=String(required=False),
				 is_archetype=Boolean(required=False),
				 location_id=ID(required=False))
	def resolve_entities(parent, info, key=None, entity_id=None, entity_type=None, search=None, is_archetype=None, location_id=None):
		# logger.info("entity resolver, for key: ", key)
		if location_id is not None:
			hierarchy = retrieve_hierarchy(location_id)
		if not key and not entity_id and not entity_type:
			query = "FOR e IN Entities "
			if search:
				query += "FILTER LOWER(e.name) LIKE LOWER('%" + search + "%') "
			if is_archetype:
				query += "FILTER e.is_archetype == true "
			if location_id is not None:
				query += f"""FILTER e.location IN ['{ "', '".join([loc.get('_id') for loc in hierarchy]) }'] """
			query += """SORT POSITION(['character', 'npc', 'asset', 'faction', 'location'], e.type, true) ASC, e.name ASC
			RETURN e"""
			cursor = db.aql.execute(query)
			entities = [doc for doc in cursor]
			result = []
			for entity in entities:
				if entity['type'] in ['character', 'gm']:
					result.append(Character(id = entity['_id']))
				elif entity['type'] == 'npc':
					result.append(NPC(id = entity['_id']))
				elif entity['type'] == 'asset':
					result.append(Asset(id = entity['_id']))
				elif entity['type'] == 'faction':
					result.append(Faction(id = entity['_id']))
				elif entity['type'] == 'location':
					result.append(Location(id = entity['_id']))
			return result
		elif not key and not entity_id and entity_type is not None:
			query = "FOR e IN Entities "
			if search:
				query += "FILTER LOWER(e.name) LIKE LOWER('%" + search + "%') "
			if is_archetype:
				query += "FILTER e.is_archetype == true "
			if location_id is not None:
				query += f"""FILTER e.location IN ['{ "', '".join([loc.get('_id') for loc in hierarchy]) }'] """
			query += f"""FILTER e.type == '{ entity_type }'
			SORT e.name ASC
			RETURN e"""
			logger.info("resolve_entities:\tquery: ", query)
			entities = db.aql.execute(query)
			if entity_type  in ['character', 'gm']:
				return [Character(id = doc['_id']) for doc in entities]
			elif entity_type == 'location':
				return [Location(id = doc['_id']) for doc in entities]
			elif entity_type == 'faction':
				return [Faction(id = doc['_id']) for doc in entities]
			elif entity_type == 'asset':
				return [Asset(id = doc['_id']) for doc in entities]
			elif entity_type == 'npc':
				return [NPC(id = doc['_id']) for doc in entities]
			else:
				raise Exception("unknown entity type: ", entity_type)
		elif key is not None or entity_id is not None:
			if key is not None:
				entity = get_doc_by_id('Entities', 'Entities/' + str(key))
			else:
				entity = get_doc_by_id('Entities', entity_id)
			info.context['entity_id'] = entity['_id']
			if entity.get('type') in ['character', 'gm']:
				return [Character(id = entity['_id'])]
			elif entity.get('type') == 'location':
				return [Location(id = entity['_id'])]
			elif entity.get('type') == 'faction':
				return [Faction(id = entity['_id'])]
			elif entity.get('type') == 'asset':
				return [Asset(id = entity['_id'])]
			elif entity.get('type') == 'npc':
				return [NPC(id = entity['_id'])]
			else:
				raise Exception("unknown entity type: ", entity['type'])
		else:
			return []

	traitsets = List(Traitset,
		traitset_id=ID(required=False),
		entity_id=ID(required=False),
		entity_type=String(required=False),
		sorting=String(required=False),
		location_restriction=ID(required=False))
	def resolve_traitsets(parent, info, traitset_id=None, entity_id=None, entity_type=None, sorting=None, location_restriction=None):
		query = None
		if traitset_id is not None:
			if entity_id is not None:
				info.context['entity_id'] = entity_id
			if sorting is not None:
				info.context['sorting'] = sorting
			return [Traitset(id=traitset_id)]
		elif entity_type is not None:
			if not location_restriction:
				# return all traitsets of a given entity type
				query = f"""FOR traitsets IN Traitsets
					FILTER '{ entity_type }' IN traitsets.entity_types
					SORT traitsets.order ASC
					RETURN {{ 'id': traitsets._id, 'name': traitsets.name }}"""
				# logger.info("retrieving traitsets for entity type: ", query)
				cursor = db.aql.execute(query)
				result = [
					Traitset(id = doc['id'], name = doc['name'])
					for doc in cursor
				]
				return result
			else:
				result = []
				hierarchy = retrieve_hierarchy(location_restriction)
				traitsets = db.collection('Traitsets').all()
				for traitset in traitsets:
					if not entity_type in traitset.get('entity_types'):
						continue
					logger.info("retrieving traitsets, checking traitset " + traitset.get('name'))
					cursor = db.collection('TraitSettings').find({'_from': traitset.get('_id'), '_to': 'Traits/1'})
					if not cursor.empty():
						default_settings = cursor.next()
						if default_settings is not None:
							if default_settings.get('locations_disabled') is not None and len(default_settings.get('locations_disabled')) > 0:
								for location in hierarchy:
									logger.info("retrieving traitsets, checking location " + location.get('name'))
									if location.get('_id') in default_settings.get('locations_enabled'):
										logger.info("adding traitset " + traitset.get('_id') + " from " + str(default_settings.get('locations_enabled')))
										result.append(Traitset(id = traitset.get('_id'), name = traitset.get('name')))
										break
									elif location.get('_id') in default_settings.get('locations_disabled'):
										logger.info("skipping traitset " + traitset.get('_id') + " since disabled: " + str(default_settings.get('locations_disabled')))
										break
							else:
								logger.info("adding traitset " + traitset.get('name'))
								result.append(Traitset(id = traitset.get('_id'), name = traitset.get('name')))
					else:
						result.append(Traitset(id = traitset.get('_id'), name = traitset.get('name')))
					logger.info("updated result to " + str(result))
				logger.info("returning " + str(len(result)) + " traitsets", result)
				return result
		else:
			query = f"""FOR traitsets IN Traitsets
				SORT traitsets.order ASC, traitsets.name ASC
				RETURN {{ 'id': traitsets._id, 'name': traitsets.name }}"""
			cursor = db.aql.execute(query)
			result = [
				Traitset(id = doc['id'], name = doc['name'])
				for doc in cursor
			]
			return result

	traits = List(Trait,
		trait_id=ID(required=False),
		entity_id=ID(required=False),
		trait_setting_id=ID(required=False),
		traitset_id=ID(required=False),
		potential_only=Boolean(required=False))
	def resolve_traits(parent, info, trait_id=None, entity_id=None, trait_setting_id=None, traitset_id=None, potential_only=False):
		if entity_id is not None:
			info.context['entity_id'] = entity_id

		# retrieve a specific trait
		if trait_setting_id is not None:
			info.context['trait_setting_id'] = trait_setting_id
			trait_setting = get_doc_by_id('TraitSettings', trait_setting_id)
			# check if it is a trait default
			if trait_setting is not None and trait_id is not None and trait_setting.get('_from') == trait_id and trait_setting.get('_to') == 'Traits/1':
				return [Trait(id=trait_id, trait_setting_id=trait_setting_id)]
			return [Trait(id=trait_setting.get('_to'), trait_setting_id=trait_setting_id)]

		# retrieve a trait for an entity
		elif trait_id is not None and entity_id is not None:
			trait_setting = db.collection('TraitSettings').find({'_from': entity_id, '_to': trait_id})
			return [Trait(id=trait_id, trait_setting_id = doc.get('_id')) for doc in trait_setting]

		# retrieve a generic trait
		elif trait_id is not None:
			return [Trait(id=trait_id)]

		# retrieve all traits of a traitset
		elif traitset_id is not None and entity_id is None:
			# return all traits of a given traitset
			cursor = db.collection('Traits').find({'traitset': traitset_id})
			return [Trait(id=doc.get('_id')) for doc in cursor]

		# return all of an entity's traits of a given traitset
		elif traitset_id is not None and entity_id is not None and potential_only is False:
			query = f"""FOR traitsetting IN TraitSettings
			FILTER traitsetting._from == '{ entity_id }'
			FOR trait IN Traits
			FILTER traitsetting._to == trait._id
			FILTER trait.traitset == '{ traitset_id }'
			RETURN trait
			"""
			set_cursor = db.aql.execute(query)
			return [Trait(id=doc.get('_id')) for doc in set_cursor]

		# return all of a traitset's traits that the given entity doesn't already have
		# and only ones they can learn (this needs work like the traitset traits logic)
		elif traitset_id is not None and entity_id is not None and potential_only is True:
			trait_settings = db.collection('TraitSettings').find({'_from': entity_id})
			archetype_ids = [doc.get('_to') for doc in db.collection('Relations').find({'_from': entity_id, 'type': 'archetype'})]
			traitset = get_doc_by_id('Traitsets', traitset_id)
			query = f"""LET entity_id = '{ entity_id }'

				LET location = (
					FOR e IN Entities
					FILTER e._id == entity_id
					RETURN e.location
				)
				LET location_hierarchy = (
					FOR v, e, p IN 0..20 OUTBOUND location[0] Relations
					FILTER p.edges[*].type ALL == 'super'
					RETURN v._id
				)

				LET traitset_id = '{ traitset_id }'

				LET connected_traits = (
					FOR traitsetting IN TraitSettings
						FILTER traitsetting._from == entity_id
						RETURN traitsetting._to
				)

				FOR t IN Traits
					FILTER t.traitset == traitset_id
					{"FILTER t._id NOT IN connected_traits" if traitset.get('duplicates') == False else ""}
					FILTER LENGTH(t.required_traits) == 0
						OR LENGTH(MINUS(t.required_traits, connected_traits)) == 0

				LET default_trait = (
					FOR def_setting IN TraitSettings
						FILTER def_setting._from == t._id
						FILTER def_setting._to == 'Traits/1'
						RETURN def_setting
				)

					SORT t.name, TO_NUMBER(SUBSTRING(default_trait[0].rating[0], 1)) ASC
					RETURN {{ location_hierarchy: location_hierarchy, trait: t, default: default_trait }}"""
			# logger.info("resolve_traits\tpotential traits query\n", query)
			cursor = db.aql.execute(query)
			result = []
			for doc in cursor:
				if doc['default']:
					determined = False
					for location in doc['location_hierarchy']:
						if location in doc['default'][0].get('locations_enabled', []):
							result.append(Trait(
								id=doc['trait'].get('_id'),
								rating=doc['default'][0].get('rating')
							))
							determined = True
							break
						elif location in doc['default'][0].get('locations_disabled', []):
							determined = True
							break
					if not determined:
						result.append(Trait(
							id=doc['trait'].get('_id'),
							rating=doc['default'][0].get('rating')
						))
				else:
					result.append(Trait(
						id=doc['trait'].get('_id')
					))
			return result
			# return [Trait(id=doc['_id']) for doc in set_cursor]
		else:
			# return all traits
			cursor = db.collection('Traits').all()
			return [Trait(id=doc.get('_id')) for doc in cursor]

	sfxs = List(SFX, sfx_id=ID(required=False))
	def resolve_sfxs(parent, info, sfx_id=None):
		if sfx_id is not None:
			doc = get_doc_by_id('SFXs', sfx_id)
			return [SFX(id=sfx_id, name = doc['name'], description = doc['description'])]
		else:
			# cursor = db.collection('SFXs').all()
			query = f"""FOR sfx IN SFXs
				SORT sfx.name ASC
				RETURN sfx"""
			cursor = db.aql.execute(query)
			return [
				SFX(id=doc['_id'], name = doc['name'], description = doc['description'])
				for doc in cursor
			]

	locations = List(Location, location_id=ID(required=False))
	def resolve_locations(parent, info, location_id=None):
		# logger.info("Query.resolve_locations:\tkey: ", key)
		if not location_id:
			cursor = db.collection('Entities').find({'type': 'location'})
			return [
				Location(id=doc['_id'], name = doc['name'])
				for doc in cursor
			]
		else:
			info.context['entity_id'] = location_id
			result = Location(id=location_id)
			# logger.info(result)
			return [result]

	relations = List(Relation, relation_id=ID(required=False))
	def resolve_relations(parent, info, relation_id=None):
		info.context['entity_id'] = relation_id
		if relation_id is not None:
			return [Relation(id=relation_id)]
		else:
			cursor = db.collection('Relations').all()
			return [
				Relation(id=doc['_id'])
				for doc in cursor
			]

class Mutation(ObjectType):
	update_session = UpdateSession.Field()

	update_trait_default = UpdateTraitDefault.Field()
	create_trait = CreateTrait.Field()
	mutate_trait = MutateTrait.Field()
	assign_trait = AssignTrait.Field()
	assign_sub_trait = AssignSubTrait.Field()
	unassign_sub_trait = UnassignSubTrait.Field()
	assign_trait_rating = AssignTraitRating.Field()
	mutate_trait_setting = MutateTraitSetting.Field()
	unassign_trait = UnassignTrait.Field()
	delete_trait = DeleteTrait.Field()
	clone_trait_setting = CloneTraitSetting.Field()

	create_traitset = CreateTraitset.Field()
	mutate_traitset = MutateTraitset.Field()
	delete_traitset = DeleteTraitset.Field()
	update_traitset_default = UpdateTraitsetDefault.Field()
	update_traitset_setting = UpdateTraitsetSetting.Field()

	create_sfx = CreateSFX.Field()
	mutate_sfx = UpdateSFX.Field()
	delete_sfx = DeleteSFX.Field()

	create_location = CreateLocation.Field()
	update_location = UpdateLocation.Field()

	create_relation = CreateRelation.Field()
	update_relation = UpdateRelation.Field()
	delete_relation = DeleteRelation.Field()

	create_entity = CreateEntity.Field()
	update_entity = UpdateEntity.Field()
	instantiate_archetype = InstantiateArchetype.Field()
	delete_entity = DeleteEntity.Field()
	create_or_update_character = CreateOrUpdateCharacter.Field()

	create_player = CreatePlayer.Field()
	delete_player = DeletePlayer.Field()
	activate_entity = ActivateEntity.Field()

schema = Schema(query=Query, mutation=Mutation)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
	'graphql',
	schema=schema,
	graphiql=True,
))

# REST API

from pyArango.connection import Connection

class ADB:
	def __init__(self):
		conn = Connection(
			arangoURL = f"http://{arango_host}:{arango_port}",
			username = arango_username,
			password = arango_password
		)
		self.db = conn[arango_db]

@app.route("/gmc")
def get_gmcs():
	adb = ADB()
	result = adb.db.fetch_list("FOR e in Entities FILTER e.type == 'GMC' RETURN e")
	return result

@app.route("/entity/<id>")
def get_gmc(id):
	adb = ADB()
	result = adb.db.fetchDocument(f"Entities/{id}").getStore()
	return result

@app.route("/entities/<type>")
def get_entities(type):
	adb = ADB()
	result = adb.db.fetch_list(f"FOR e in Entities FILTER e.type == '{type}' RETURN e")
	return result

@app.route("/location")
def get_locations():
	adb = ADB()
	result = adb.db.fetch_list("FOR e in Entities FILTER e.type == 'Location' RETURN e")
	return result

@app.route("/location/<id>")
def get_location(id):
	adb = ADB()
	result = adb.db.fetchDocument(f"Entities/{id}").getStore()
	return result

@app.route("/pick-character/<uuid>/<characterkey>", methods = ['POST'])
def pick_character(uuid, characterkey):
	if uuid not in [d['player'] for d in session_characters] and characterkey not in [d['character'] for d in session_characters]:
		session_characters.append({
			"player": uuid,
			"character": 'Entities/' + characterkey
		})
		return { "success": True }

	elif 'Entities/' + characterkey not in [d['character'] for d in session_characters]:
		for sc in session_characters:
			if sc["player"] == uuid:
				sc["character"] = 'Entities/' + characterkey
				return { "success": True }
	
	character_doc = get_doc_by_id('Entities', str(characterkey))
	character_doc['active'] = True
	update_doc('Entities', character_doc)

	return { "success": False }

@app.route("/deactivate-character/<character_key>", methods = ['POST'])
def deactivate_character(character_key):
	if 'Entities/' + character_key in [d['character'] for d in session_characters]:
		for sc in session_characters:
			if sc["character"] == 'Entities/' + character_key:
				session_characters.remove(sc)
				return { "success": True }
	return { "success": False }

# dicepool: { character: ID, player: ID, gm: Boolean, result: Number, effect: Die[] }
@app.route("/set-dicepool/<uuid>", methods = ['POST'])
def set_dicepool(uuid):
	global resolutions
	global resolutions_rev

	if not request.json:
		return jsonify({ "error": "no JSON provided" })

	new_resolution = request.json

	# is_new = False
	# if len(resolutions) == 0 or not any([dicepool.get('player').get('uuid') == uuid for dicepool in resolutions]):
	# 	is_new = True
	if any([dicepool.get('player').get('uuid') == uuid for dicepool in resolutions]):
		resolutions.pop([dicepool.get('player').get('uuid') == uuid for dicepool in resolutions].index(True))

	if len(new_resolution.get('dice')) > 0:

	# 	# add complications to new resolutions
	# 	for cp in complication_pool:
	# 		if cp.get('player') != uuid:
	# 			# new_resolution['dice'] = [d for d in new_resolution.get('dice') if d.get('complication_source') != cp.get('player')]
	# 			for comp in cp.get('complications'):
	# 				if comp.get('id') not in [d.get('id') for d in new_resolution.get('dice')]:
	# 					comp['complication_source'] = cp.get('player')
	# 					new_resolution['dice'].append(comp)

		resolutions.append(new_resolution)

	result = { "resolutions": resolutions }

	resolutions_rev = uuid4()

	return jsonify(result)

@app.route("/add-complications/<uuid>", methods = ['POST'])
def add_complications(uuid):
	"""this method completely removes all complications of the given user and replaces them with supplied complications"""
	global complication_pool
	global resolutions
	global resolutions_rev

	if not request.json:
		return jsonify({ "error": "no JSON provided" })

	new_complications = request.json.get('complications')

	# the player has already suggested complications
	if uuid in [comp.get('player') for comp in complication_pool]:
		player_complication_pool = complication_pool.pop([comp.get('player') == uuid for comp in complication_pool].index(True))
		player_complication_pool['complications'] = new_complications
		complication_pool.append(player_complication_pool)

	elif len(new_complications) > 0:
		complication_pool.append({
			"player": uuid,
			"complications": new_complications
		})

	# add complication to opposing resolutions
	for res in resolutions:
		if res.get('player').get('uuid') != uuid:
			res['dice'] = [d for d in res.get('dice') if d.get('complication_source') != uuid]
			for comp in new_complications:
				comp['complication_source'] = uuid
				res['dice'].append(comp)

	resolutions_rev = uuid4()

	return jsonify({ "success": True })

@app.route("/get-resolutions/")
@app.route("/get-resolutions/<res_rev>")
def get_resolutions(res_rev = None):
	# returns the results of different players' dicepools
	global resolutions
	global resolutions_rev

	# first check if it's needed, to save performance
	if res_rev is not None and str(resolutions_rev) == res_rev:
		return jsonify({
			"message": "no new resolutions",
			"resolutions_rev": resolutions_rev
		})

	else:
		# set variables to determine winner
		highest_sum = 0
		second_highest_sum = 0

		for r in resolutions:
			if r.get('player').get('phase') == "resolving dicepools":
				result = 0

				for die in r.get('dice'):
					if die.get('isResultDie'):
						result += die.get('result')
					if result > highest_sum:
						second_highest_sum = highest_sum
						highest_sum = result

				for r in resolutions:
					result_dice = [d for d in r.get('dice') if d.get('isResultDie')]
					r['result'] = sum([d.get('result') for d in result_dice])
					if r.get('result') == highest_sum:
						r['winner'] = True
					else:
						r['winner'] = False
			else:
				r['winner'] = False
				r['result'] = 0

		return jsonify({
			"resolutions": resolutions,
			"complication_pool": complication_pool,
			"resolutions_rev": resolutions_rev,
			"heroic": math.floor((highest_sum - second_highest_sum) / 5),
			"highest_sum": highest_sum
		})

@app.route("/reset-dicepool", methods=['POST'])
def reset_dicepool():
	# when GM resets gamestate
	global resolutions
	global resolutions_rev
	resolutions = []
	resolutions_rev = uuid4()
	return jsonify({ "success": True })

@app.route("/session-characters")
def get_session_characters():
	return { "characters": session_characters }

@app.route("/upload/<entity_key>", methods = ['POST'])
def upload_file(entity_key):
	# logger.info("received request to upload file")
	file = request.files['file']
	file_extension = os.path.splitext(file.filename)[1]
	entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key))
	# logger.info("entity_folder: ", entity_folder)
	if not os.path.exists(entity_folder):
		# logger.info("creating folder: ", entity_folder)
		os.makedirs(entity_folder)
	# filename = f"{ entity_id }{ file_extension }"
	# filename = secure_filename(file.filename)
	image = Image.open(file)
	image_mini = image.copy()
	image_large = image.copy()
	data = list(image.getdata())
	image_without_exif = Image.new(image.mode, image.size)
	image_without_exif.putdata(data)
	width, height = image.size
	max_size_mini = 48
	max_size_small = 240
	max_size_large = 1024
	if width > height:
		new_width_small = max_size_small
		new_height_small = int((new_width_small / width) * height)
		image_small = image.resize((new_width_small, new_height_small))
		new_width_mini = max_size_mini
		new_height_mini = int((new_width_mini / width) * height)
		image_mini = image_mini.resize((new_width_mini, new_height_mini))
		new_width_large = max_size_large
		new_height_large = int((new_width_large / width) * height)
		image_large = image_large.resize((new_width_large, new_height_large))

	else:
		new_height_small = max_size_small
		new_width_small = int((new_height_small / height) * width)
		image_small = image.resize((new_width_small, new_height_small))
		new_height_mini = max_size_mini
		new_width_mini = int((new_height_mini / height) * width)
		image_mini = image_mini.resize((new_width_mini, new_height_mini))
		new_height_large = max_size_large
		new_width_large = int((new_height_large / height) * width)
		image_large = image_large.resize((new_width_large, new_height_large))
	image_small.save(os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key), f"small{ file_extension.lower() }"))
	image_mini.save(os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key), f"mini{ file_extension.lower() }"))
	image_large.save(os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key), f"large{ file_extension.lower() }"))
	image_without_exif.save(os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key), f"original{ file_extension.lower() }"))
	return jsonify({ "success": True })

@app.route("/upload/<entity_key>/<location_key>", methods = ['POST'])
def upload_file_location(entity_key, location_key):
	logger.info("received request to upload file")
	file = request.files['file']
	file_extension = os.path.splitext(file.filename)[1]
	entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key), str(location_key))
	logger.info("entity_folder: " + entity_folder)
	if not os.path.exists(entity_folder):
		logger.info("creating folder: " + entity_folder)
		os.makedirs(entity_folder)
	# filename = f"{ entity_id }{ file_extension }"
	# filename = secure_filename(file.filename)
	image = Image.open(file)
	hierarchy = retrieve_hierarchy('Entities/' + str(location_key))
	logger.info("hierarchy: " + str(hierarchy))
	location_key = hierarchy[-2].get('_key')
	path = os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key), location_key, f"original{ file_extension.lower() }")
	logger.info("image path: " + path)
	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))
	image.save(path)
	save_image(path, str(entity_key), str(location_key))
	return jsonify({ "success": True })

@app.route("/imagen/<entity_key>/<force>", methods = ['POST'])
def imagegen(entity_key, force):
	"""call comfyui API to generate image"""
	rating_weights = [
		0.6,
		0.7,
		0.8,
		0.9,
		1.0,
	]
	genre_loras = {
		"wuxia": "setting/ChineseWuXia",
		"anime": "style/Anime art",
		"modern": "import/ModernCartoon-Gudarzi",
		"fantasy": "import/FantasyIllustration",
		"scifi": "setting/SydMead-v1",
		"alien": "setting/PaintedWorld-v2",
		"space": "setting/LauraSpaceXploration",
		"urban": "import/arcstyle",
		"magic": "feature/material/GlowingRunes",
		"natural": "setting/Vegetation",
		# "realistic": "style/amateurphoto-v6-forcu",
		"realistic": "style/RealisticScenePhotography",
		"cyberpunk": "setting/CyberpunkAnime",
		"oceanic": "setting/ElementalWaterPlane",
		"colorful": "colors/ColorPop",
		"primitive": "setting/Hyperborea-v2",
		"comic": "style/ComicStyle"
	}

	# variables used in the generation
	width = 832
	height = 1216
	lora1 = "import/DigitalFantasyIllustration"
	lora1_weight = 0.0
	lora2 = "style/Anime art"
	lora2_weight = 0.4
	genres = []

	entity = get_doc_by_id('Entities', 'Entities/' + str(entity_key))

	if not entity.get('imagening') or force == "true":

		entity_type = entity.get('type')
		location_key = None
		if entity_type != "location":
			location_id = entity.get('location')
			location = get_doc_by_id('Entities', location_id)
			if entity.get('type') != 'location':
				if location.get('type') == 'location':
					location_key = location.get('_key')
				else:
					# if entity is following
					location_id = location.get('location')
					location = get_doc_by_id('Entities', location_id)
					location_key = location.get('_key')
				hierarchy = retrieve_hierarchy(location_id)
				if len(hierarchy) > 1:
					location_key = hierarchy[-2].get('_key')
		name = entity.get('name')
		description = entity.get('description')
		negative = "cgi, 3d, bad quality, watermark, signature, text"

		if entity_type in ["character", "npc"]:
			# prompt = f"(a solo upper body character portrait of { name }:1.2), head, shoulders, "
			# negative += ", full body, legs, cropped head"
			prompt = ""
			genre_loras['realistic'] = "frame/RealFaceji"
		elif entity_type == "asset":
			prompt = f"(an image of { name }:1.2), "
			negative += ", person"
			# width = 1216
			# height = 832
		elif entity_type == "faction":
			prompt = f"(a symbol or logo or flag or shield or emblem:1.2) representing the faction called { name }. "
			negative += ", photo, person, environment"
			width = 1024
			height = 1024
		elif entity_type == "location":
			prompt = f"(location background image, a humanless atmospheric image focusing on { name }:1.2), "
			negative += ", person"
		else:
			prompt = ""

		if entity_type in ["character", "npc", "asset", "gm"]:
			entity = get_doc_by_id('Entities', 'Entities/' + str(entity_key))
			location = retrieve_location(entity)
			trait_settings = [doc for doc in db.collection('TraitSettings').find({'_from': entity.get('_id')})]
			archetype_trait_settings = []

			archetype_ids = [archetype.get('_to') for archetype in db.collection('Relations').find({'_from': entity.get('_id'), 'type': 'archetype'})]
			visited_archetypes = set()
			while archetype_ids:
				current_id = archetype_ids.pop(0)
				if current_id in visited_archetypes:
					continue
				visited_archetypes.add(current_id)
				archetype = get_doc_by_id('Entities', current_id)
				archetype_trait_settings += [doc for doc in db.collection('TraitSettings').find({'_from': archetype.get('_id')})]
				archetype_ids.extend([archetype.get('_to') for archetype in db.collection('Relations').find({'_from': archetype.get('_id'), 'type': 'archetype'})])

			trait_settings += archetype_trait_settings
			trait_settings = filter_trait_settings_by_location(trait_settings, location.get('_id'))
			traits = []
			for trait_setting in trait_settings:
				trait_id = trait_setting.get('_to')
				trait = get_doc_by_id('Traits', trait_id)
				subtrait_ids = db.collection('TraitSettings').find({'_from': trait_setting.get('_id')})
				subtraits = []
				for subtrait_id in subtrait_ids:
					subtrait = get_doc_by_id('Traits', subtrait_id.get('_to'))
					subtraits.append(subtrait)
				trait['subtraits'] = subtraits
				traitset_id = trait.get('traitset')
				traitset = get_doc_by_id('Traitsets', traitset_id)
				traits.append((traitset, trait, trait_setting))

			prompt += "("
			prompt += f"portrait of {entity.get('name')}" if entity.get('name') else ""
			prompt += f", {entity.get('description')}" if entity.get('description') else ""
			for traitset, trait, trait_setting in traits:
				if traitset.get('name') == 'tutorial':
					continue
				if trait.get('name') == 'appearance':
					prompt += ", ("
					prompt += trait_setting.get('statement') if trait_setting.get('statement') else ""
					prompt += ", " if trait_setting.get('statement') and trait_setting.get('notes') else ""
					prompt += trait_setting.get('notes') if trait_setting.get('notes') else ""
					prompt += ":1.4)"
				elif trait.get('name') == 'negative imagen':
					# negative += f"{', '.join([trait_setting.get('statement'), trait_setting.get('notes')])}"
					negative += ", " + trait_setting.get('statement') if trait_setting.get('statement') else ""
					negative += ", " + trait_setting.get('notes') if trait_setting.get('notes') else ""
				elif trait_setting.get('rating_type') != 'challenge':
					# prompt += f"({', '.join([trait.get('name'),trait_setting.get('statement'),trait_setting.get('notes')])}:{ str(rating_weights[abs(t[3]) - 1]) })"
					prompt += ", ("
					# prompt += traitset.get('prompt_prefix') if traitset.get('prompt_prefix') else traitset.get('name') + " "
					prompt += trait.get('name')
					prompt += " is " if trait.get('name') and trait_setting.get('statement') else ""
					prompt += re.sub(r'\([^)]*\)', '', trait_setting.get('statement')) if trait_setting.get('statement') else ""
					prompt += " of (" + ",".join([subtrait.get('name') for subtrait in trait.get('subtraits')]) + ")" if trait.get('subtraits') else ""
					prompt += ", (" if trait_setting.get('notes') else ""
					prompt += trait_setting.get('notes') + ":0.4)" if trait_setting.get('notes') else ""
					# prompt += ":"
					prompt += ":" if trait_setting.get('rating') and trait_setting.get('rating_type') != "empty" else ""
					prompt += str(rating_weights[abs(trait_setting.get('rating')[0]) - 1]) if trait_setting.get('rating') and trait_setting.get('rating_type') != "empty" else ""
					prompt += ")"
				# prompt += ", "

			# prompt = prompt[:-2] # remove the last comma
			prompt += ":1.2), "
			
			positive_imagen = []

			hierarchy = retrieve_hierarchy(location.get('_id'))[:-1]
			for loc in hierarchy:
				if entity_type in ["npc"]:
					prompt += f" (located in { loc.get('name') }, " + re.sub(r'\([^)]*\)', '', loc.get('description'))
				loc_trait_settings = db.collection('TraitSettings').find({'_from': loc.get('_id')})
				for lts in loc_trait_settings:
					trait_id = lts.get('_to')
					trait = get_doc_by_id('Traits', trait_id)
					if trait.get('name') == 'genre':
						genres.append(lts.get('statement'))
					elif trait.get('name') == 'positive imagen':
						positive_imagen.append(lts.get('statement')) if lts.get('statement') else ""
						positive_imagen.append(lts.get('notes')) if lts.get('notes') else ""
					elif trait.get('name') == 'negative imagen':
						negative += ", " + lts.get('statement') if lts.get('statement') else ""
						negative += ", " + lts.get('notes') if lts.get('notes') else ""
					elif trait.get('name') == 'appearance' and entity_type in ["npc", "asset"]:
						prompt += ", " + lts.get('statement') if lts.get('statement') else ""
						prompt += ", " + lts.get('notes') if lts.get('notes') else ""
			strength = 1.4
			strength_list = []
			for loc in hierarchy:
				strength *= 0.6
				strength_list.append(strength)
			strength_list.reverse()
			if entity_type in ["npc", "asset"]:
				for i in range(len(strength_list)):
					prompt += f":{str(strength_list[i])}"
					if i < len(strength_list) - 1:
						prompt += ")"
				prompt += ")"
			# prompt += "), "
			if len(positive_imagen) > 0:
				prompt += ", (" + ", ".join(positive_imagen) + ":0.8)"



		# location
		elif entity_type == "location":
			query = f"""FOR entity IN Entities
				FILTER entity._id == 'Entities/{ entity_key }'
			LET traits = (
				FOR s IN TraitSettings
					FILTER entity._id == s._from
				FOR t IN Traits
					FILTER s._to == t._id
				RETURN [t.name, s.statement, s.rating[0], s.notes, s.rating_type]
			)
			LET hierarchy = (
				FOR v, e, p IN 0..20 OUTBOUND entity Relations
				FILTER p.edges[*].type ALL == 'super'
				LET hierarchy_traits = (
					FOR s IN TraitSettings
						FILTER v._id == s._from
						FILTER s.rating_type != 'resource'
					FOR t IN Traits
						FILTER s._to == t._id
					RETURN [t.name, s.statement, s.notes, s.rating[0]]
				)
				RETURN [v.name, v.description, hierarchy_traits]
			)
			LET zones = (
				FOR v, e, p IN 0..1 INBOUND entity Relations
				FILTER p.edges[*].type ALL == 'super'
				RETURN [v.name, v.description]
			)
			RETURN {{
				entity: entity.name,
				description: entity.description,
				traits: traits,
				hierarchy: hierarchy,
				zones: zones
			}}"""

			# there should only be one result
			cursor = db.aql.execute(query)

			traits = []

			for doc in cursor:
				if doc['description']:
					prompt = f"({ doc['description'] }), "

				if len(doc.get('zones')) > 1:
					prompt += f"the different zones in { name } are ((" + ":0.4) and (".join([zone[0] + ", " + zone[1] for zone in doc['zones'][1:]]) + "):0.8), "

				if len(doc['traits']) > 0:
					prompt += " with the following traits: "
					for t in doc['traits']:
						if t[0] == "appearance":
							traits.append(f"({(t[1] if t[1] else '') + (', ' if t[1] and t[3] else '') + (t[3] if t[3] else '')}:1.4)")
						elif t[0] == "negative imagen":
							negative += ", " + t[1]
						else:
							traits.append(f"({t[0]}{' is ' + t[1] if t[1] else ''}{' ' + t[3] if t[3] else ''}{':' + str(rating_weights[abs(t[2]) - 1]) if t[2] and t[4] != 'empty' else ''})")
					prompt += ", ".join(traits)

				if len(doc['hierarchy']) > 1:
					multiplier = 0.6
					location_strength = 1.6
					for l in doc['hierarchy'][1:]:
						location_strength = location_strength * multiplier
						if location_strength >= multiplier:
							location_name = l[0]
							location_description = l[1]
							lts = l[2]
							for lt in lts:
								if lt[0].startswith("genre"):
									genres.append(lt[1])
								elif lt[0] == "negative imagen":
									negative += ", " + lt[1]
								elif lt[0] == "appearance":
									location_name += ", " + lt[1] if lt[1] else "" # name
									location_name += ", " + lt[2] if lt[2] else "" # statement
									location_name += ", " + lt[3] if lt[3] else "" # notes
							prompt += " (" + location_name
							# prompt += ", " + location_description
						else:
							lts = l[2]
							for lt in lts:
								if lt[0].startswith("genre"):
									genres.append(lt[1])
					location_strength = 1.6
					strengths = []
					for l in doc['hierarchy'][1:]:
						location_strength = location_strength * multiplier
						if location_strength >= multiplier:
							strengths.append(location_strength)
					strengths.reverse()
					for i in range(len(strengths)):
						prompt += ":" + str(strengths[i]) + "), "

		# faction
		elif entity_type == "faction":
			query = f"""FOR entity IN Entities
				FILTER entity._id == 'Entities/{ entity_key }'
			LET traits = (
				FOR s IN TraitSettings
					FILTER entity._id == s._from
				FOR t IN Traits
					FILTER s._to == t._id
				RETURN [t.name, s.statement, s.notes, s.rating[0]]
			)
			LET genres = (
				FOR v, e, p IN 0..20 OUTBOUND entity.location Relations
				FILTER p.edges[*].type ALL == 'super'
				LET hierarchy_traits = (
					FOR s IN TraitSettings
						FILTER v._id == s._from
					FOR t IN Traits
						FILTER s._to == t._id
						FILTER t.name == 'genre'
					RETURN s.statement
				)
				RETURN hierarchy_traits
			)
			RETURN {{
				entity: entity.name,
				description: entity.description,
				traits: traits,
				genres: FLATTEN(genres)
			}}"""

			# there should only be one result
			cursor = db.aql.execute(query)

			traits = []

			for doc in cursor:
				if doc.get('description'):
					prompt += f"({ doc.get('description') }:1.0), "
				if len(doc.get('traits')) > 0:
					prompt += "with the following traits: "
					for t in doc.get('traits'):
						if t[0] == "appearance":
							traits.append(f"({t[0]}{' is ' + t[1] if t[1] else ''}{t[2] if t[2] else ''}:1.4), ")
						elif t[2]:
							traits.append(f"({t[0]}{' is ' + t[1] if t[1] else ''}:{ str(rating_weights[abs(t[2]) - 1]) }), ")
					prompt += ", ".join(traits)

				if len(doc.get('genres')) > 0:
					for g in doc.get('genres'):
						genres.append(g)

		# if entity_type in ['character', 'npc', 'location']:
		# 	prompt += ". In the styles of Donato Giancola and Noah Bradley and AquaSixio and Charlie Bowater and Yuumei and Jeremy Fenske and Amy Sol and Greg Tocchini and Carne Griffiths and Wadim Kashin"

		prompt = "".join(prompt.splitlines())

		
		genres = list(set(genres))
		if len(genres) > 0:
			if genres[0] in genre_loras.keys():
				lora1 = genre_loras.get(genres[0])
				lora1_weight = 0.8
			if len(genres) > 1 and genres[1] in genre_loras.keys():
				lora2 = genre_loras.get(genres[1])
				lora2_weight = 0.4
			# elif entity_type in ['character', 'npc']:
			# 	lora2 = "frame/CharacterPortraitsCaith"
			# 	lora2_weight = 0.4
		
		negative += ", watermark, signature"
		
		generate_image(
			prompt,
			negative,
			entity_key,
			location_key = location_key,
			lora1 = lora1,
			lora1_weight = lora1_weight,
			lora2 = lora2,
			lora2_weight = lora2_weight,
			width = width,
			height = height
		)
		entity['imagening'] = True
		entity['imagened'] = False
		update_doc('Entities', entity)
		return jsonify({ "success": True })
	else:
		return jsonify({ "success": False })

def save_image(filepath, entity_key, location_key=None):
	# Open the original image
	image = Image.open(filepath)
	image_mini = image.copy()
	image_large = image.copy()
	data = list(image.getdata())
	image_without_exif = Image.new(image.mode, image.size)
	image_without_exif.putdata(data)

	# Determine image dimensions
	width, height = image.size

	# Define size thresholds
	max_size_mini = 48
	max_size_small = 240
	max_size_large = 1024

	# Calculate new dimensions and resize images
	if width > height:
		new_width_small = max_size_small
		new_height_small = int((new_width_small / width) * height)
		image_small = image.resize((new_width_small, new_height_small))

		new_width_mini = max_size_mini
		new_height_mini = int((new_width_mini / width) * height)
		image_mini = image_mini.resize((new_width_mini, new_height_mini))

		new_width_large = max_size_large
		new_height_large = int((new_width_large / width) * height)
		image_large = image_large.resize((new_width_large, new_height_large))
	else:
		new_height_small = max_size_small
		new_width_small = int((new_height_small / height) * width)
		image_small = image.resize((new_width_small, new_height_small))

		new_height_mini = max_size_mini
		new_width_mini = int((new_height_mini / height) * width)
		image_mini = image_mini.resize((new_width_mini, new_height_mini))

		new_height_large = max_size_large
		new_width_large = int((new_height_large / height) * width)
		image_large = image_large.resize((new_width_large, new_height_large))

	# Get file extension
	file_extension = os.path.splitext(filepath)[1]

	# Create entity folder for saving if it doesn't exist
	if not location_key:
		entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key))
	else:
		entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(entity_key), str(location_key))
	if not os.path.exists(entity_folder):
		os.makedirs(entity_folder)

	# Save images
	image_small.save(os.path.join(entity_folder, f"small{file_extension.lower()}"))
	image_mini.save(os.path.join(entity_folder, f"mini{file_extension.lower()}"))
	image_large.save(os.path.join(entity_folder, f"large{file_extension.lower()}"))
	image_without_exif.save(os.path.join(entity_folder, f"original{file_extension.lower()}"))

	entity = get_doc_by_id('Entities', 'Entities/' + str(entity_key))
	entity['imagening'] = False
	entity['imagened'] = True
	update_doc('Entities', entity)

	return jsonify({"success": True})

# example url: http://localhost:5000/get-t2i-models?model_type=loras
@app.route("/get-t2i-models", methods=["GET"])
def get_t2i_models():
	model_type = request.args.get("model_type", default=None)
	t2i_models = {}
	if model_type is None or model_type == "checkpoints":
		for root, dirs, files in os.walk(os.path.join(app.config['T2I_MODELS_FOLDER'], "diffusion_models", "FLUX1")):
			current_folder = t2i_models
			for part in os.path.relpath(root, os.path.join(app.config['T2I_MODELS_FOLDER'], "diffusion_models", "FLUX1")).split(os.sep):
				if part not in current_folder:
					current_folder[part] = {}
				current_folder = current_folder[part]
			for file in files:
				if file.endswith(".safetensors"):
					name = re.sub(r'\.safetensors$', '', file)
					name = re.sub(r'_[0-9]+$', '', name)
					current_folder[name] = file
	if model_type is None or model_type == "loras":
		for root, dirs, files in os.walk(os.path.join(app.config['T2I_MODELS_FOLDER'], "loras", "flux")):
			current_folder = t2i_models
			for part in os.path.relpath(root, os.path.join(app.config['T2I_MODELS_FOLDER'], "loras", "flux")).split(os.sep):
				if part not in current_folder:
					current_folder[part] = {}
				current_folder = current_folder[part]
			for file in files:
				if file.endswith(".safetensors"):
					name = re.sub(r'\.safetensors$', '', file)
					name = re.sub(r'_[0-9]+$', '', name)
					current_folder[name] = file
	return jsonify(t2i_models)

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=5000)
