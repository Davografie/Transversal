"""
	Flask and GraphQL endpoints
"""
from uuid import uuid4
import pandas as pd
import datetime
import random

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import shutil
import math
from PIL import Image

# https://github.com/graphql-python/graphql-server/blob/master/docs/flask.md
from graphql_server.flask import GraphQLView

# https://docs.graphene-python.org/en/latest/
from graphene import Interface, ObjectType, InputObjectType, Mutation, Field, ID, String, Int, Boolean, Schema, List, JSONString

# https://docs.python-arango.com/en/main/
from arango import ArangoClient

import transversal as tv
from imagegen import generate_image

app = Flask(__name__)
CORS(app)

logging.getLogger("werkzeug").setLevel(logging.WARNING)

app.config['UPLOAD_FOLDER'] = '/media/uploads'
app.config['IMAGEN_FOLDER'] = '/media/imagens'

arango_host = "tv_adb"
arango_port = "8529"
arango_username = "root"
arango_password = os.environ.get("ARANGO_ROOT_PASSWORD")
arango_db = "transversal"

# session variables
dicepool_limit = -1
result_limit = 2
effect_limit = 1
session_characters = []
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
print("ArangoDB connection established")

class Player(ObjectType):
	uuid = ID()
	name = String()
	is_gm = Boolean()
	character = Field(lambda: Character)

	def resolve_character(parent, info):
		return next((char for char in session_characters if char['uuid'] == parent.uuid), None)

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
		return [Character(id='Entities/' + char.get('character')) for char in session_characters]

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

			active_entities = db.collection('Entities').find({'active': True, 'type': 'character'})
			for entity in active_entities:
				entity['active'] = False
				db.collection('Entities').update(entity)

			stuck_on_imagening = db.collection('Entities').find({'imagening': True})
			for entity in stuck_on_imagening:
				entity['imagening'] = False
				db.collection('Entities').update(entity)

		if session_input.new_session or session_input.next_scene:
			scene_rev = uuid4()
			
			active_entities = db.collection('Entities').find({'active': True, 'type': 'npc'})
			for entity in active_entities:
				entity['active'] = False
				db.collection('Entities').update(entity)

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

	def resolve_name(parent, info):
		return db.collection('SFXs').get(parent.id)['name']

	def resolve_description(parent, info):
		return db.collection('SFXs').get(parent.id)['description']

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
		return CreateSFX(sfx=SFX(id=sfx['id'], name=name, description=description))

class UpdateSFX(Mutation):
	class Arguments:
		id = ID(required=True)
		name = String()
		description = String()

	sfx = Field(lambda: SFX)

	def mutate(self, info, id, name=None, description=None):
		sfx = db.collection('SFXs').get(id)
		if name:
			sfx['name'] = name
		if description:
			sfx['description'] = description
		db.collection('SFXs').update(sfx)
		return UpdateSFX(sfx=SFX(id=id, name=name, description=description))

class DeleteSFX(Mutation):
	class Arguments:
		id = ID(required=True)

	success = Boolean()
	message = String()

	def mutate(self, info, id):
		try:
			query = f"""FOR ts IN TraitSettings
				FILTER '{ id }' IN ts.sfxs
				RETURN ts"""
			results = db.aql.execute(query)
			for result in results:
				new_sfxs = result.get('sfxs')
				new_sfxs.remove(id)
				db.collection('TraitSettings').update(result, {'sfxs': new_sfxs})
			db.collection('SFXs').delete(id)
			return DeleteSFX(success=True)
		except Exception as e:
			return DeleteSFX(success=False, message=str(e))


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
	statement = String()
	notes = String()
	rating_type = String()
	rating = List(String)
	locations_enabled = List(String)
	locations_disabled = List(String)
	sfxs = List(lambda: SFX)
	sfxs_ids = List(String)
	known_to = List(lambda: Character) # characters who have learned about this trait
	hidden = Boolean()

	@classmethod
	def _hydrate_traitsetting(cls, parent, info):
		if parent.id:
			traitsetting = db.collection('TraitSettings').get(parent.id)
			parent.statement = traitsetting.get('statement')
			parent.notes = traitsetting.get('notes')
			parent.rating_type = traitsetting.get('rating_type')
			parent.rating = traitsetting.get('rating')
			parent.locations_enabled = traitsetting.get('locations_enabled')
			parent.locations_disabled = traitsetting.get('locations_disabled')
			parent.sfxs_ids = traitsetting.get('sfxs')
			parent.hidden = traitsetting.get('hidden')

	def resolve_trait(parent, info):
		if parent.trait:
			return parent.trait
		elif parent.id:
			return Trait(id=db.collection('TraitSettings').get(parent.id)['_to'])
		else:
			return None

	def resolve_from_entity(parent, info):
		if parent.from_entity and parent.from_entity.id is not None:
			return parent.from_entity
		elif parent.id:
			entity_id = db.collection('TraitSettings').get(parent.id).get('_from')
			if entity_id.startswith('Entities/'):
				entity_type = db.collection('Entities').get(entity_id).get('type')
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
				entity_id = db.collection('Relations').get(entity_id).get('_from')
				if entity_id.startswith('Entities/'):
					entity_type = db.collection('Entities').get(entity_id).get('type')
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
			return db.collection('TraitSettings').get(parent.id).get('statement')
		else:
			return None

	def resolve_notes(parent, info):
		if parent.notes:
			return parent.notes
		elif parent.id:
			return db.collection('TraitSettings').get(parent.id).get('notes')
		else:
			return None

	def resolve_rating_type(parent, info):
		if parent.rating_type:
			return parent.rating_type
		if parent.id:
			return db.collection('TraitSettings').get(parent.id).get('rating_type')
		else:
			return None

	def resolve_rating(parent, info):
		if parent.rating != None:
			return parent.rating
		if parent.id:
			return db.collection('TraitSettings').get(parent.id).get('rating')
		else:
			return None

	def resolve_locations_enabled(parent, info):
		if parent.locations_enabled != None:
			return parent.locations_enabled
		if parent.id:
			return db.collection('TraitSettings').get(parent.id).get('locations_enabled')
		else:
			return None
		
	def resolve_locations_disabled(parent, info):
		if parent.locations_disabled != None:
			return parent.locations_disabled
		if parent.id:
			return db.collection('TraitSettings').get(parent.id).get('locations_disabled')
		else:
			return None

	def resolve_sfxs(parent, info):
		if parent.sfxs != None:
			return parent.sfxs
		if parent.id:
			sfxs = db.collection('TraitSettings').get(parent.id).get('sfxs')
			if sfxs is not None:
				return [SFX(id=sfx) for sfx in sfxs]
		else:
			return []

	def resolve_sfxs_ids(parent, info):
		if db.collection('TraitSettings').get(parent.id).get('sfxs') is not None:
			return db.collection('TraitSettings').get(parent.id).get('sfxs')

	def resolve_known_to(parent, info):
		if parent.id:
			characters = db.collection('TraitSettings').get(parent.id).get('known_to')
			if characters is None:
				return []
			return [Character(id=character) for character in characters]
		else:
			return []

	def resolve_hidden(parent, info):
		if parent.id and parent.hidden is None:
			return db.collection('TraitSettings').get(parent.id).get('hidden')
		else:
			return False

class TraitSettingInput(InputObjectType):
	rating_type = String(required=False)
	rating = List(Int, required=False)
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

	trait = Field(lambda: Trait)
	message = String()

	def mutate(self, info, trait_setting_id=None, trait_setting_input=None, entity_id=None, die_type=None):
		"""
		trait_setting_id: ID of trait setting to update, if not provided, trait will be created
		entity_id: ID of entity to add trait setting to
		die_type: for transferring resources
		"""
		try:
			trait_setting = db.collection('TraitSettings').get(trait_setting_id)
			if trait_setting is None and entity_id is not None:
				trait_setting = db.collection('TraitSettings').insert({**trait_setting_input, '_from': entity_id})
			elif trait_setting is not None and trait_setting.get('_from').startswith('Entities/'):
				# check if the setting is for an archetype,
				# in which case, all instances of that archetype with the same settings
				# should also be updated
				# entity = db.collection('Entities').get(trait_setting.get('_from'))
				# if entity is not None \
				# 		and entity.get('_id').startswith('Entities/') \
				# 		and db.collection('Entities').get(entity.get('_id')).get('is_archetype'):
				# 	# print(f"MutateTraitSetting:\tentity is archetype, updating instances")
				# 	instances = db.collection('Entities').find({'is_archetype': False, 'archetype_id': entity.get('_id')})
				# 	for instance in instances:
				# 		old_trait_setting = db.collection('TraitSettings').find({'_from': instance.get('_id'), '_to': trait_setting.get('_to')})
				# 		if not old_trait_setting.empty():
				# 			old_trait_setting = [doc for doc in old_trait_setting][0]
				# 			db.collection('TraitSettings').update_match({
				# 				'_from': instance.get('_id'),
				# 				'_to': trait_setting.get('_to'),
				# 				'rating_type': old_trait_setting.get('rating_type'),
				# 				'rating': old_trait_setting.get('rating'),
				# 				'statement': old_trait_setting.get('statement'),
				# 				'notes': old_trait_setting.get('notes'),
				# 				'locations_enabled': old_trait_setting.get('locations_enabled'),
				# 				'locations_disabled': old_trait_setting.get('locations_disabled'),
				# 				'sfxs': old_trait_setting.get('sfxs')
				# 			}, trait_setting_input)
				# 		else:
				# 			db.collection('TraitSettings').insert({
				# 				'_from': instance.get('_id'),
				# 				'_to': trait_setting.get('_to'),
				# 				**trait_setting_input
				# 			})


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
							# print(f"MutateTraitSetting:\tto_pocket: { to_pocket }")
							db.collection('TraitSettings').update(to_pocket)
						else:
							new_doc = {
								'_from': entity_id,
								'_to': trait_setting.get('_to'),
								**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
								'rating': [die_type]
							}
							# print(f"MutateTraitSetting:\tnew pocket: { new_doc }")
							db.collection('TraitSettings').insert(new_doc)

					# if it's not a resource, but instead an asset, the entire asset is transferred at once
					elif db.collection('Traits').get(trait_setting.get('_to')).get('traitset') == 'Traitsets/3':
						trait_setting = { **trait_setting, '_from': entity_id }

				# then update the actual setting
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
						and db.collection('Entities').get(trait_setting_input.get('teach_to')).get('type') == 'character':
					trait_setting = {
						'_id': trait_setting.get('_id'),
						'_from': trait_setting.get('_from'),
						'_to': trait_setting.get('_to'),
						**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
						'known_to': list(set(trait_setting.get('known_to', []) + [trait_setting_input.get('teach_to')]))
					}
				db.collection('TraitSettings').update(trait_setting)
			else:
				if trait_setting_input is not None:
					trait_setting = {**trait_setting, **trait_setting_input}
				db.collection('TraitSettings').update(trait_setting)
			return MutateTraitSetting(trait=Trait(trait_setting_id=trait_setting.get('_id')))
		except Exception as e:
			# print(e)
			return MutateTraitSetting(message=str(e))

class CloneTraitSetting(Mutation):
	class Arguments:
		trait_setting_id = ID(required=True)
	
	trait = Field(lambda: Trait)

	def mutate(root, info, trait_setting_id=None):
		trait_setting = db.collection('TraitSettings').get(trait_setting_id)
		new_trait_setting = db.collection('TraitSettings').insert({
			'_from': trait_setting.get('_from'),
			'_to': trait_setting.get('_to'),
			**{ key: value for key, value in trait_setting.items() if not key.startswith('_') },
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
			trait = db.collection('Traits').get(parent.id)
		if parent.trait_setting_id:
			trait_id = db.collection('TraitSettings').get(parent.trait_setting_id).get('_to')
			trait = db.collection('Traits').get(trait_id)
		parent.traitset_id = trait.get('traitset')
		parent.id = trait.get('_id')
		parent.name = trait.get('name')
		parent.explanation = trait.get('explanation')
		parent.location_restricted = trait.get('location_restricted')
		parent.inheritable = trait.get('inheritable')
	
	@classmethod
	def _hydrate_traitsetting(cls, parent, info):
		if parent.trait_setting_id:
			traitsetting = db.collection('TraitSettings').get(parent.trait_setting_id)
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
			parent.id = db.collection('TraitSettings').get(parent.trait_setting_id).get('_to')
			return parent.id
		else:
			raise Exception("trait_setting is None 1")

	def resolve_name(parent, info):
		# print(f"resolve_name:\ttrait: '{ parent.id }'")
		result = db.collection('Traits').get(parent.id).get('name')
		return result

	def resolve_explanation(parent, info):
		# print(f"resolve_explanation:\ttrait: '{ parent.id }'")
		result = db.collection('Traits').get(parent.id).get('explanation')
		return result

	def resolve_traitset_id(parent, info):
		return db.collection('Traits').get(parent.id).get('traitset')

	def resolve_traitset(parent, info):
		# print("resolving traitset for trait: ", parent.id)
		return Traitset(id=db.collection('Traits').get(parent.id).get('traitset'))

	def resolve_required_traits(parent, info):
		# print("resolve_required_traits:\ttrait: ", parent.id)
		if parent.id is None and parent.trait_setting_id:
			parent.id = db.collection('TraitSettings').get(parent.trait_setting_id).get('_to')
		required_traits = db.collection('Traits').get(parent.id).get('required_traits') or []
		return [Trait(id=trait) for trait in required_traits]

	def resolve_location_restricted(parent, info):
		if not parent.location_restricted:
			Trait._hydrate_trait(parent, info)
		return parent.location_restricted or db.collection('Traitsets').get(parent.traitset_id).get('location_restricted')

	def resolve_trait_setting(parent, info):
		if parent.trait_setting_id:
			return TraitSetting(id=parent.trait_setting_id)
		elif parent.id is not None and info.context.get('entity_id') is not None:
			# print("resolve_trait_setting:\ttrait: ", parent.id, "\tentity_id: ", info.context.get('entity_id'))
			cursor = db.collection('TraitSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			# print("cursor count: ", cursor.count())
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
			trait_setting = db.collection('TraitSettings').get(parent.trait_setting_id)
			parent.statement = trait_setting.get('statement')
			parent.rating_type = trait_setting.get('rating_type')
			parent.rating = trait_setting.get('rating')
			return parent.statement
		elif parent.id is not None and info.context.get('entity_id') is not None:
			# print("resolve_statement:\ttrait: ", parent.id, "\tentity_id: ", info.context.get('entity_id'))
			cursor = db.collection('TraitSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			# print("cursor count: ", cursor.count())
			if cursor.count() > 0:
				# print('skibedob')
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
			trait_setting = db.collection('TraitSettings').get(parent.trait_setting_id)
			parent.statement = trait_setting.get('statement')
			parent.notes = trait_setting.get('notes')
			parent.rating_type = trait_setting.get('rating_type')
			parent.rating = trait_setting.get('rating')
			return parent.notes

	def resolve_rating_type(parent, info):
		if parent.rating_type:
			return parent.rating_type
		elif parent.trait_setting_id:
			trait_setting = db.collection('TraitSettings').get(parent.trait_setting_id)
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
			trait_setting = db.collection('TraitSettings').get(parent.trait_setting_id)
			parent.statement = trait_setting.get('statement')
			parent.rating_type = trait_setting.get('rating_type')
			parent.rating = trait_setting.get('rating')
			return parent.rating
		else:
			raise Exception("trait_setting is None 5")

	def resolve_sfxs(parent, info):
		if parent.trait_setting_id:
			# print("resolve_sfxs:\ttrait_setting: ", parent.trait_setting_id)
			sfxs = db.collection('TraitSettings').get(parent.trait_setting_id).get('sfxs')
			if sfxs is not None:
				return [SFX(id=sfx) for sfx in sfxs]
		return []

	def resolve_possible_sfxs(parent, info):
		trait = db.collection('Traits').get(parent.id)
		return [SFX(id=sfx) for sfx in trait.get('possible_sfxs') or []]

	def resolve_inheritable(parent, info):
		return db.collection('Traits').get(parent.id).get('inheritable')

	def resolve_default_trait_setting(parent, info):
		global absolute_default_trait_setting
		if parent.id:
			default_trait_settings = db.collection('TraitSettings').find({'_from': parent.id, '_to': 'Traits/1'})
			default_trait_setting = [doc for doc in default_trait_settings][0] if default_trait_settings.count() == 1 else None
			if default_trait_setting:
				return TraitSetting(id=default_trait_setting.get('_id'))
			else:
				traitset_id = db.collection('Traits').get(parent.id).get('traitset')
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
			entity_id = db.collection('TraitSettings').get(parent.trait_setting_id).get('_from')
			if entity_id.startswith('Entities/'):
				entity_type = db.collection('Entities').get(entity_id).get('type')
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
					entity_type = db.collection('Entities').get(entity_id).get('type')
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
		if possible_sub_traits := db.collection('Traits').get(parent.id).get('possible_sub_traits'):
			result = []
			for sub_trait in possible_sub_traits:
				traitset_id = db.collection('Traits').get(sub_trait).get('traitset')
				# sub-traitsets
				if 'subtrait' in db.collection('Traitsets').get(traitset_id).get('entity_types'):
					result.append(Trait(id=sub_trait))
				# entity traits
				elif info.context.get('entity_id'):
					traits = db.collection('TraitSettings').find({ '_from': info.context.get('entity_id'), '_to': sub_trait })
					entity = db.collection('Entities').get(info.context.get('entity_id'))
					traits = filter_trait_settings_by_location(traits, retrieve_location(entity).get('_id'))
					for trait in traits:
						result.append(Trait(id=trait.get('_to'), trait_setting_id=trait.get('_id')))
				elif info.context.get('trait_setting_id'):
					entity_id = db.collection('TraitSettings').get(info.context.get('trait_setting_id')).get('_from')
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
		trait = db.collection('Traits').get(trait_id)
		if trait_input is not None:
			if trait_input.get('required_traits') is not None:
				for required_trait in trait_input.get('required_traits'):
					try:
						db.collection('Traits').has(required_trait)
					except:
						if(setting := db.collection('TraitSettings').get(required_trait)):
							trait_input['required_traits'].remove(required_trait)
							trait_input['required_traits'].append(setting['_to'])
			
			if trait_input.get('traitset_id') is not None:
				trait_input['traitset'] = trait_input.pop('traitset_id')

			trait = {**trait, **trait_input}

		db.collection('Traits').update(trait)
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
						"'known_to': ['" + "', '".join(trait_setting_input.get('known_to', [])) + "']" if trait_setting_input.get('known_to') else ''
					}
				}}"""
		cursor = db.aql.execute(query)
		# retrieving default traitset setting
		if cursor.empty():
			query = f"""FOR traitsetting IN TraitSettings
				FILTER traitsetting._from == '{ db.collection('Traits').get(trait_id)['traitset'] }'
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
						"'known_to': ['" + "', '".join(trait_setting_input.get('known_to', [])) + "']" if trait_setting_input.get('known_to') else ''
					}
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
							"'known_to': ['" + "', '".join(trait_setting_input.get('known_to', [])) + "']" if trait_setting_input.get('known_to') else ''
						}
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
		# print(f"AssignTrait:\tassigning subtraits for { new_traitsetting.get('_id') } from { old_traitsetting_id }")
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
		trait = db.collection('Traits').get(trait_id)
		traitset_settings = db.collection('TraitsetSettings').find({ '_from': entity_id, '_to': trait.get('traitset') })
		if traitset_settings.empty():
			traitset = db.collection('Traitsets').get(trait.get('traitset'))
			db.collection('TraitsetSettings').insert({
				'_from': entity_id,
				'_to': trait.get('traitset'),
				**{k: v for k, v in traitset.items() if not k.startswith('_')}
			})

		# if the entity was an archetype,
		# also add the trait to entities based on that archetype
		# that don't yet have the trait
		# if entity_id.startswith('Entities/') and db.collection('Entities').get(entity_id).get('is_archetype'):
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
		# 			traitset = db.collection('Traitsets').get(trait.get('traitset'))
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

	trait = Field(Trait)

	def mutate(self, info, trait_setting_id=None, subtrait_id=None):
		global absolute_default_trait_setting

		traitset_id = db.collection('Traits').get(subtrait_id).get('traitset')
		traitset = db.collection('Traitsets').get(traitset_id)

		if 'subtrait' in traitset.get('entity_types'):
			default_trait_setting = absolute_default_trait_setting

			default_trait_settings = db.collection('TraitSettings').find({ '_from': subtrait_id, '_to': 'Traits/1' })
			if not default_trait_settings.empty():
				default_trait_setting = [doc for doc in default_trait_settings][0]
				default_trait_setting = {k: v for k, v in default_trait_setting.items() if not k.startswith('_')}
			else:
				traitset_id = db.collection('Traits').get(subtrait_id).get('traitset')
				traitset_settings = db.collection('TraitsetSettings').find({ '_from': traitset_id, '_to': 'Traits/1' })
				if not traitset_settings.empty():
					default_trait_setting = [doc for doc in traitset_settings][0]
					default_trait_setting = {k: v for k, v in default_trait_setting.items() if not k.startswith('_')}
				else:
					default_trait_settings = db.collection('TraitSettings').find({ '_from': 'Traits/1', '_to': 'Traits/1' })
					if not default_trait_settings.empty():
						default_trait_setting = [doc for doc in default_trait_settings][0]
						default_trait_setting = {k: v for k, v in default_trait_setting.items() if not k.startswith('_')}
					else:
						default_trait_setting = absolute_default_trait_setting

			if db.collection('TraitSettings').find({
				'_from': trait_setting_id,
				'_to': subtrait_id
			}).empty():
				new_subtrait = db.collection('TraitSettings').insert({
					'_from': trait_setting_id,
					'_to': subtrait_id,
					**default_trait_setting
				})

				# check if entity was archetype, if so; add subtrait to entities based on that archetype
				traitsetting = db.collection('TraitSettings').get(trait_setting_id)
				entity_id = traitsetting.get('_from')
				if entity_id.startswith('Entities/') and db.collection('Entities').get(entity_id).get('is_archetype'):
					for entity in db.collection('Entities').find({'archetype_id': entity_id}):
						if not (entity_traitsettings := db.collection('TraitSettings').find({
							'_from': entity.get('_id'),
							'_to': traitsetting.get('_to'),
						})).empty():
							for entity_traitsetting in entity_traitsettings:
								if db.collection('TraitSettings').find({
									'_from': entity_traitsetting.get('_id'),
									'_to': subtrait_id
								}).empty():
									db.collection('TraitSettings').insert({
										'_from': entity_traitsetting.get('_id'),
										'_to': subtrait_id,
										**default_trait_setting
									})

				return AssignSubTrait(trait=Trait(id=new_subtrait.get('_to'), trait_setting_id=new_subtrait.get('_id')))
			else:
				raise Exception("Subtrait already assigned")
		else:
			# maybe assign entity trait as shortcut subtrait
			entity_id = info.context.get('entity_id') or (trait := db.collection('TraitSettings').get(trait_setting_id)).get('_from')
			if not (shortcut_traits := db.collection('TraitSettings').find({
				'_from': entity_id,
				'_to': subtrait_id
			})).empty():
				if trait.get('shortcut_traits') is None:
					trait['shortcut_traits'] = []
				for shortcut_trait in shortcut_traits:
					trait['shortcut_traits'].append(shortcut_trait.get('_id'))
				trait['shortcut_traits'] = list(set(trait.get('shortcut_traits')))
				db.collection('TraitSettings').update(trait)
				return AssignSubTrait(trait=Trait(id=subtrait_id, trait_setting_id=trait_setting_id))

class UnassignSubTrait(Mutation):
	class Arguments:
		trait_setting_id = ID()
		subtrait_setting_id = ID(required=True)

	success = Boolean()
	message = String()

	def mutate(root, info, trait_setting_id=None, subtrait_setting_id=None):
		# print(f"UnassignSubTrait:\t{ trait_setting_id }")
		if trait_setting_id is not None:
			trait = db.collection('TraitSettings').get(trait_setting_id)

			if trait is not None and 'shortcut_traits' in trait and subtrait_setting_id in trait.get('shortcut_traits'):
				# print(f"UnassignSubTrait:\t{ trait }")
				trait['shortcut_traits'].remove(subtrait_setting_id)
				db.collection('TraitSettings').update(trait)
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
		# print(f"UnassignTrait:\t{ trait_setting_id }")
		trait_setting = db.collection('TraitSettings').get(trait_setting_id)
		# check the instances of the archetype
		if trait_setting.get('_from').startswith('Entities/'):
			archetype = db.collection('Entities').get(trait_setting.get('_from'))
			if archetype.get('is_archetype'):
				for instance in db.collection('Entities').find({'archetype_id': archetype.get('_id')}):
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
		# print(f"arguments; trait_id: { trait_id }, character_id: { character_id }, rating: { ', '.join(rating) }")
		if not (trait_id and character_id and rating):
			errorMessage = f"missing argument(s), trait_id: { trait_id }, character_id: { character_id }, rating: { rating }"
			# print(errorMessage)
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
			return DeleteTrait(success=False, error=str(e))


class Traitset(ObjectType):
	key = ID()
	id = ID(id=String())
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
	traitset_setting = Field(lambda: TraitsetSetting)

	@classmethod
	def _hydrate(cls, parent, info):
		traitset = db.collection('Traitsets').get(parent.id)
		parent.key = traitset.get('_key')
		parent.name = traitset.get('name')
		parent.explainer = traitset.get('explainer')
		parent.entity_types = traitset.get('entity_types')
		parent.location_restricted = traitset.get('location_restricted')
		parent.limit = traitset.get('limit')
		parent.order = traitset.get('order')
		parent.duplicates = traitset.get('duplicates')

	def resolve_key(parent, info):
		if not parent.key:
			Traitset._hydrate(parent, info)
		if parent.key:
			return parent.key
		return db.collection('Traitsets').get(parent.id).get('_key')

	def resolve_name(parent, info):
		if not parent.name:
			Traitset._hydrate(parent, info)
		if parent.name:
			return parent.name
		return db.collection('Traitsets').get(parent.id).get('name')

	def resolve_explainer(parent, info):
		if not parent.explainer:
			Traitset._hydrate(parent, info)
		if parent.explainer:
			return parent.explainer
		return db.collection('Traitsets').get(parent.id).get('explainer')

	def resolve_entity_types(parent, info):
		if not parent.entity_types:
			Traitset._hydrate(parent, info)
		if parent.entity_types:
			return parent.entity_types
		return db.collection('Traitsets').get(parent.id).get('entity_types')

	def resolve_location_restricted(parent, info):
		if not parent.location_restricted:
			Traitset._hydrate(parent, info)
		if parent.location_restricted is not None:
			return parent.location_restricted
		return db.collection('Traitsets').get(parent.id).get('location_restricted') or False

	def resolve_limit(parent, info):
		if info.context.get('entity_id') is not None:
			# check in traitset settings if limit is overridden
			traitset_settings = db.collection('TraitsetSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			for traitset_setting in traitset_settings:
				if traitset_setting.get('dicepool_limit') is not None:
					return traitset_setting.get('dicepool_limit')
		if parent.limit:
			return parent.limit
		return db.collection('Traitsets').get(parent.id).get('dicepool_limit')

	def resolve_order(parent, info):
		if parent.order:
			return parent.order
		return db.collection('Traitsets').get(parent.id).get('order')

	def resolve_duplicates(parent, info):
		if parent.duplicates:
			return parent.duplicates
		return db.collection('Traitsets').get(parent.id).get('duplicates')

	def resolve_traits(parent, info):
		if parent.traits:
			return parent.traits
		elif info.context.get('entity_id') is not None and info.context.get('entity_id').startswith('Entities/'):
			# print(f"Traitset.resolve_traits:\tentity_id: { info.context.get('entity_id') }")
			entity = db.collection('Entities').get(info.context.get('entity_id'))

			# traits for location are inherited, so special query
			if entity is not None and entity.get('type') == 'location':
				if info.context.get('sorting') is not None and info.context.get('sorting') == 'NAME':
					sorting = "SORT t.name, setting.statement, MAX(setting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], setting.rating_type, true) ASC"
				else:
					sorting = "SORT MAX(setting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], setting.rating_type, true) ASC, t.name, setting.statement"
				# print(f"Traitset.resolve_traits:\treturning location traits")
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
				trait_settings = [doc for doc in db.aql.execute(query)]
				# print(f"Traitset.resolve_traits:\tentity trait_settings: { trait_settings }")
				result = filter_trait_settings_by_location(trait_settings, location_id)

				# inherited traits
				if info.context.get('sorting') is not None and info.context.get('sorting') == 'NAME':
					sorting = "SORT t.name, traitsettings[0].traitsetting.statement, MAX(traitsettings[0].traitsetting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], traitsettings[0].traitsetting.rating_type, true) ASC"
				else:
					sorting = "SORT MAX(traitsettings[0].traitsetting.rating) DESC, POSITION(['empty', 'challenge', 'static', 'resource'], traitsettings[0].traitsetting.rating_type, true) ASC, t.name"
				inherited_traits = [ts.get('inherited_as') for ts in trait_settings if ts.get('inherited_as') is not None]
				# print(f"Traitset.resolve_traits:\tinherited_traits: { inherited_traits }")
				query = f"""LET archetypes = (
						FOR v, e, p IN 0..5 OUTBOUND '{ entity.get('_id') }' Relations
						FILTER p.edges[*].type ALL == 'archetype'
						FILTER v._id != '{ entity.get('_id') }'
						RETURN v._id
					)
					FOR entity IN archetypes
						FOR trait, traitsetting IN OUTBOUND entity TraitSettings
						FILTER traitsetting._id NOT IN { inherited_traits }
						COLLECT traitId = traitsetting._to INTO traitsettings
					FOR t IN Traits
						FILTER traitsettings[0].traitsetting._to == t._id
						FILTER t.traitset == '{ parent.id }'
						{ sorting }
					FOR ts IN traitsettings
					RETURN ts.traitsetting"""
				# print(f"Traitset.resolve_traits:\tarchetype query: { query }")
				trait_settings = [doc for doc in db.aql.execute(query)]
				# print(f"Traitset.resolve_traits:\tarchetype trait_settings: { trait_settings }")
				trait_settings = filter_trait_settings_by_location(trait_settings, location_id)
				result = result + trait_settings

				return [Trait(id=trait_setting.get('_to'), trait_setting_id=trait_setting.get('_id')) for trait_setting in result]


			# neither entity nor relation
			else:
				# print(f"Traitset.resolve_traits:\tNo entity or relation found")
				return []

		# traits for relations
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

		elif info.context.get('entity_id') is None:
			# print(f"Traitset.resolve_traits:\tResolving traits for traitsets irrespective of entity")
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

	def resolve_sfxs(parent, info):
		sfxs = db.collection('Traitsets').get(parent.id).get('sfxs')
		if sfxs is not None:
			return [SFX(id=sfx) for sfx in sfxs]
		else:
			return []

	def resolve_default_trait_setting(parent, info):
		setting = db.collection('TraitSettings').find({'_from': parent.id, '_to': 'Traits/1'})
		if setting.count() == 0:
			# print("resolve_default_trait_setting:\tdefault trait")
			setting = db.collection('TraitSettings').find({'_from': 'Traits/1', '_to': 'Traits/1'})
		return [TraitSetting(id=setting['_id']) for setting in setting][0]

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
			# print("(005) using query: ", set_query)
			set_cursor = db.aql.execute(set_query)
			result = [doc for doc in set_cursor][0]
			return result
		return 0

	def resolve_traitset_setting(parent, info):
		# print(f"Traitset.resolve_traitset_settings")
		if info.context.get('entity_id') is not None:
			# print(f"Traitset.resolve_traitset_settings:\tentity_id: { info.context.get('entity_id') }")
			traitset_settings = db.collection('TraitsetSettings').find({'_from': info.context.get('entity_id'), '_to': parent.id})
			if not traitset_settings.empty():
				traitset_setting = [doc for doc in traitset_settings][0]
				# print(f"Traitset.resolve_traitset_settings:\ttraitset_setting: { traitset_setting }")
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
		ts = db.collection('Traitsets').get(traitset_id)
		traitset_settings = db.collection('TraitsetSettings').find({'_to': traitset_id}) if traitset_id is not None else None

		# rename limit to dicepool_limit
		if 'limit' in traitset_input:
			traitset_input['dicepool_limit'] = traitset_input.pop('limit')
			if traitset_settings is not None:
				for setting in traitset_settings:
					if setting.get('dicepool_limit') < traitset_input.get('dicepool_limit'):
						db.collection('TraitsetSettings').update(setting, {'dicepool_limit': traitset_input.get('dicepool_limit')})
		
		if 'sfxs' in traitset_input:
			# remove old sfxs from traitset settings if removed from traitset
			# first check which sfxs have been removed from the traitset
			if traitset_settings is not None and ts.get('sfxs') is not None:
				for sfx in ts.get('sfxs'):
					if sfx not in traitset_input.get('sfxs'):
						# then remove them from the traitset settings
						for setting in traitset_settings:
							if sfx in setting.get('sfxs'):
								db.collection('TraitsetSettings').update(setting, {'sfxs': [s for s in setting.get('sfxs') if s != sfx]})

			# add new sfxs to traitset settings if added to traitset and not yet present in traitset settings
			if traitset_settings is not None and ts.get('sfxs') is not None:
				for sfx in traitset_input.get('sfxs'):
					if sfx not in ts.get('sfxs'):
						for setting in traitset_settings:
							if sfx not in setting.get('sfxs'):
								db.collection('TraitsetSettings').update(setting, {'sfxs': setting.get('sfxs') + [sfx]})

		ts = {**ts, **traitset_input}
		db.collection('Traitsets').update(ts)
		return MutateTraitset(traitset=Traitset(id=ts.get('_id')), message="Traitset updated")

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
					db.collection('TraitSettings').update(default_trait_setting)
		# print("Updating default trait setting for traitset: ", traitset_id, " to: ", default_settings)
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
		entity_id = db.collection('TraitsetSettings').get(parent.id).get('_from')
		if entity_id.startswith('Entities/'):
			entity = db.collection('Entities').get(entity_id)
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
		traitset_id = db.collection('TraitsetSettings').get(parent.id).get('_to')
		return Traitset(id=traitset_id)

	def resolve_limit(parent, info):
		return db.collection('TraitsetSettings').get(parent.id).get('dicepool_limit')

	def resolve_sfxs(parent, info):
		sfx_ids = db.collection('TraitsetSettings').get(parent.id).get('sfxs')
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
			tss = db.collection('TraitsetSettings').get(traitset_setting_id)

		# rename limit to dicepool_limit
		if 'limit' in traitset_setting_input:
			traitset_setting_input['dicepool_limit'] = traitset_setting_input.pop('limit')

		if tss:
			tss = { **tss, **traitset_setting_input }
			db.collection('TraitsetSettings').update(tss)
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
		
		entity = db.collection('Entities').get(parent.id)
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
		return parent.key

	def resolve_name(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.name

	def resolve_description(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.description

	def resolve_image(parent, info):
		# print("Resolving image: ", parent.key)
		if not parent.key:
			Entity._hydrate_entity(parent, info)
		
		try:
			location_key = None
			if not parent.location:
				if parent.entity_type != 'location':
					location_id = db.collection('Entities').get(parent.id).get('location')
					location = db.collection('Entities').get(location_id)
					if location.get('type') != 'location':
						# if following
						location_id = location.get('location')
						location = db.collection('Entities').get(location_id)
					parent.location = Location(id=location.get('_id'), key=location.get('_key'))
					location_hierarchy = tv.retrieve_hierarchy(parent.location.id)
					if len(location_hierarchy) > 1:
						location_key = location_hierarchy[-2].get('_key')
				else: # if location
					parents = [rel.get('_to') for rel in db.collection('Relations').find({ '_from': parent.id, 'type': 'super' })]
					if len(parents) > 0:
						location_id = parents[0]
						location = db.collection('Entities').get(location_id)
						parent.location = Location(id=location.get('_id'), key=location.get('_key'))
						location_hierarchy = tv.retrieve_hierarchy(parent.location.id)
						if len(location_hierarchy) > 1:
							location_key = location_hierarchy[-2].get('_key')
			if parent.entity_type != 'location' and location_key is not None and os.path.isdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{location_key}"):
				# print("Resolving image 2: ", parent.key, "/", location_key)
				old_file = os.listdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{location_key}")[0]
				ext = os.path.splitext(old_file)[1]
				save_image(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{location_key}/{old_file}", parent.key, location_key)
				os.remove(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{location_key}/{old_file}")
				os.rmdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{location_key}")
				os.rmdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}")
				# return f"{parent.key}/{location_key}/original{ext}"
				return Portrait(path=f"{parent.key}/{location_key}/", size="original", ext=ext)
			elif parent.entity_type != 'location' and location_key is not None and os.path.isdir(f"{app.config['UPLOAD_FOLDER']}/{parent.key}/{location_key}"):
				# print("Resolving image 3: ", parent.key, "/", location_key)
				for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
					if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{parent.key}/{location_key}/original{ext}"):
						# return f"{parent.key}/{location_key}/original{ext}"
						return Portrait(path=f"{parent.key}/{location_key}/", size="original", ext=ext)
			elif os.path.isdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}"):
				# print("Resolving image 4: ", parent.key)
				old_file = os.listdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}")[0]
				ext = os.path.splitext(old_file)[1]
				# os.rename(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{old_file}", f"{app.config['IMAGEN_FOLDER']}/{parent.key}/original.jpg")
				save_image(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{old_file}", parent.key)
				os.remove(f"{app.config['IMAGEN_FOLDER']}/{parent.key}/{old_file}")
				os.rmdir(f"{app.config['IMAGEN_FOLDER']}/{parent.key}")
				# return f"{parent.key}/original{ext}"
				return Portrait(path=f"{parent.key}/", size="original", ext=ext)
			else:
				# print("Resolving image 5: ", parent.key)
				for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
					if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{parent.key}/original{ext}"):
						# return f"{parent.key}/original{ext}"
						return Portrait(path=f"{parent.key}/", size="original", ext=ext)
					elif parent.entity_type == 'location' and parent.location is not None:
						if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{parent.location.key}/original{ext}"):
							# return f"{parent.location.key}/original{ext}"
							return Portrait(path=f"{parent.location.key}/", size="original", ext=ext)
						else:
							return None
					elif (archetype_id := db.collection('Entities').get(parent.id).get('archetype_id')) is not None:
						archetype = db.collection('Entities').get(archetype_id)
						if os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{archetype.get('_key')}/{location_key}/original{ext}"):
							# return f"{archetype.get('_key')}/{location_key}/original{ext}"
							return Portrait(path=f"{archetype.get('_key')}/{location_key}/", size="original", ext=ext)
						elif os.path.isfile(f"{app.config['UPLOAD_FOLDER']}/{archetype.get('_key')}/original{ext}"):
							# return f"{archetype.get('_key')}/original{ext}"
							return Portrait(path=f"{archetype.get('_key')}/", size="original", ext=ext)
						else:
							return None
					else:
						return None
		except Exception as e:
			# print(f"Entity\tresolve_image:\t{e}")
			return None

	def resolve_imagening(parent, info):
		"""prevents the user from running image generation while busy"""
		return db.collection('Entities').get(parent.id).get('imagening')

	def resolve_imagened(parent, info):
		""""""
		if parent.entity_type is None:
			entity = db.collection('Entities').get(parent.id)
			parent.entity_type = entity.get('type')
			parent.name = entity.get('name') if entity.get('name') is not None else parent.name
			parent.description = entity.get('description') if entity.get('description') is not None else parent.description
		if parent.entity_type == 'character':
			if parent.location is None:
				location_id = db.collection('Entities').get(parent.id).get('location')
				location = db.collection('Entities').get(location_id)
				if location.get('type') != 'location':
					# if following
					location_id = location.get('location')
					location = db.collection('Entities').get(location_id)
				parent.location = Location(id=location.get('_id'), name=location.get('name'), description=location.get('description'))
				location_hierarchy = tv.retrieve_hierarchy(parent.location.id)
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
		location = retrieve_location(db.collection('Entities').get(parent.id))
		# print(f"Entity\n\tresolve_traitsets:\n\t\tretrieved {len(trait_settings)} trait settings, now filtering by location { location.get('name') }")
		filtered_trait_settings = filter_trait_settings_by_location(trait_settings, location.get('_id'))
		unique_traitsets = []
		for traitsetting in filtered_trait_settings:
			traitset_id = traitsetting.get('traitset')
			if traitset_id not in unique_traitsets:
				unique_traitsets.append(traitset_id)
		# print(f"Entity\n\tresolve_traitsets:\n\t\tfiltered to {len(unique_traitsets)} trait sets")
		
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
		# print(f"Entity\n\tresolve_traitsets:\n\t\tretrieved {len(unpopulated_traitsets)} unpopulated trait sets, now filtering by location { location.get('name') }")
		filtered_unpopulated_traitsets = filter_trait_settings_by_location(unpopulated_traitsets, location.get('_id'))
		for traitsetting in filtered_unpopulated_traitsets:
			traitset_id = traitsetting.get('traitset')
			if traitset_id not in unique_traitsets:
				unique_traitsets.append(traitset_id)
		# print(f"Entity\n\tresolve_traitsets:\n\t\tfiltered to {len(unique_traitsets)} trait sets")
		return [Traitset(id=traitset) for traitset in unique_traitsets]		

	def resolve_location(parent, info):
		entity = db.collection('Entities').get(parent.id)
		location = retrieve_location(entity)
		if location.get('_id') is not None:
			return Location(id=location.get('_id'))
		else:
			return None

	def resolve_following(parent, info):
		loc_id = db.collection('Entities').get(parent.id).get('location')
		if not loc_id:
			return None
		loc = db.collection('Entities').get(loc_id)
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
		# print("query: ", query)
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
		archetype_id = db.collection('Entities').get(parent.id).get('archetype_id')
		if archetype_id is not None:
			archetype = db.collection('Entities').get(archetype_id)
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

	def resolve_active(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.active

	def resolve_hidden(parent, info):
		Entity._hydrate_entity(parent, info)
		return parent.hidden or False

	def resolve_known_to(parent, info):
		known_to = db.collection('Entities').get(parent.id).get('known_to', [])
		result = []
		changed = False
		for entity_id in known_to:
			entity = db.collection('Entities').get(entity_id)
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
			db.collection('Entities').update({'_id': parent.id, 'known_to': known_to})
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
		key = ID(required=True)
		name = String()
		location = ID()
		following = ID()
		favorite = Boolean()
		is_archetype = Boolean()
		archetype_id = ID()
		active = Boolean()
		entity_input = EntityInput()

	entity = Field(lambda: Entity)

	def mutate(root, info, key, entity_input=None, name=None, location=None, following=None, favorite=None, is_archetype=None, archetype_id=None, active=None):
		entity = db.collection('Entities').get(key)
		# print(f"UpdateEntity.mutate:\t0\tparameters:\t{ locals() }")
		changes = {}
		if name is not None:
			changes['name'] = name
		
		# the entity changes location
		if (location or (entity_input and entity_input.get('location'))) and entity.get('type') != 'location':
			changes['location'] = location or entity_input.pop('location')
			# print(f"UpdateEntity.mutate:\t1\tchanges: { changes }")
			location_doc = db.collection('Entities').get(changes.get('location'))
			# print(f"UpdateEntity.mutate:\t2\tlocation_doc: { location_doc }")
			known_to = location_doc.get('known_to') or []
			if entity.get('_id') not in known_to:
				known_to.append(entity.get('_id'))
			location_doc['known_to'] = list(set(known_to))
			db.collection('Entities').update(location_doc)
		elif (location or (entity_input and entity_input.get('location'))) and entity.get('type') == 'location':
			zones = db.collection('Relations').find({'_from': entity.get('_id'), 'type': 'super'})
			zone = [doc for doc in zones][0]
			zone['_to'] = location or entity_input.pop('location')
			db.collection('Relations').update(zone)
		# print(f"UpdateEntity.mutate:\t3\tchanges: { changes }")
		if following is not None:
			changes['location'] = following
		if favorite is not None:
			changes['favorite'] = favorite
		if is_archetype is not None:
			changes['is_archetype'] = is_archetype
		if archetype_id is not None:
			changes['archetype_id'] = archetype_id
		if active is not None:
			changes['active'] = active
		# print(f"UpdateEntity.mutate:\t4\tchanges: { changes }")
		if entity_input is not None and entity_input.get('show_to') is not None:
			known_to = set(entity.get('known_to', []) + entity_input.pop('show_to', []))
			changes['known_to'] = list(known_to)
		# print(f"UpdateEntity.mutate:\t5\tchanges: { changes }")
		entity = {
			'_key': key,
			'_id': entity.get('_id'),
			**{key: value for key, value in entity.items() if not key.startswith('_')},
			**changes,
			**(entity_input if entity_input is not None else {})
		}
		# print(f"UpdateEntity.mutate:\t6\tentity: { entity }")
		db.collection('Entities').update(entity)
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
		key = ID(required=True)
		name = String(required=False)

	entity = Field(lambda: Entity)
	message = String()

	def mutate(root, info, key, name=None):
		archetype = db.collection('Entities').get(key)
		new_entity = {key: value for key, value in archetype.items() if not key.startswith('_')}
		new_entity['archetype_id'] = archetype.get('_id')
		new_entity['is_archetype'] = False
		if name is not None:
			new_entity['name'] = name
		else:
			name = list(archetype.get('name'))
			random.SystemRandom().shuffle(name)
			new_entity['name'] = ''.join(name)
			new_entity['name'] = ' '.join(s.capitalize() for s in new_entity['name'].split(' '))
		try:
			new_entity_meta = db.collection('Entities').insert(new_entity)
			new_entity = {**new_entity, **new_entity_meta}
		except:
			return InstantiateArchetype(message="error cloning entity", entity=None)
		
		# link instance with archetype
		db.collection('Relations').insert({ '_from': new_entity.get('_id'), '_to': archetype.get('_id'), 'type': 'archetype' })

		# # copy trait settings
		# query = f"""FOR entity IN Entities
		# 				FILTER entity._id == 'Entities/{ key }'

		# 			LET traitsettings = (
		# 				FOR ts IN TraitSettings
		# 				FILTER entity._id == ts._from
		# 				RETURN ts
		# 			)

		# 			RETURN {{
		# 				entity: entity,
		# 				traitsettings: traitsettings
		# 			}}"""
		# cursor = db.aql.execute(query)
		# result = [doc for doc in cursor][0]
		# for traitsetting in result.get('traitsettings'):
		# 	new_traitsetting = {key: value for key, value in traitsetting.items() if not key.startswith('_')}
		# 	new_traitsetting['_from'] = new_entity.get('_id')
		# 	new_traitsetting['_to'] = traitsetting.get('_to')
		# 	db.collection('TraitSettings').insert(new_traitsetting)

		# copy traitset settings
		query = f"""FOR entity IN Entities
						FILTER entity._id == 'Entities/{ key }'

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
		relations = db.collection('Relations').find({'_from': archetype.get('_id')})
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
		key = ID(required=True)
		rmtree = Boolean(required=False)

	success = Boolean()
	message = String()

	def mutate(root, info, key, rmtree=False):

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
			
			# and all traitset settings
			traitset_settings = db.collection('TraitsetSettings').find({'_from': entity_id})
			for traitset_setting in traitset_settings:
				db.collection('TraitsetSettings').delete(traitset_setting.get('_id'))

			# remove the image folder
			shutil.rmtree(f"{app.config['UPLOAD_FOLDER']}/{current_entity.get('_key')}", ignore_errors=True)

			# now we can delete the entity
			db.collection('Entities').delete(entity_id)

		try:
			current_entity = db.collection('Entities').get(key)

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
			return DeleteEntity(success=False, message=str(e))

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
		# print("(005) using query: ", set_query)
		set_cursor = db.aql.execute(set_query)
		result = [doc for doc in set_cursor][0]
		return result

	def resolve_available(parent, info):
		if parent.key is None:
			parent.key = db.collection('Entities').get(parent.id).get('_key')
		if parent.is_archetype is None:
			parent.is_archetype = db.collection('Entities').get(parent.id).get('is_archetype')
		return parent.key not in [d['character'] for d in session_characters] and not parent.is_archetype

	def resolve_pp(parent, info):
		return db.collection('Entities').get(parent.id).get('pp')

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
		# print("mutating character: ", key, " input: ", input)

		if key:
			character_doc = db.collection('Entities').get(key)
			if character_doc:
				# print("updating character: ", input)
				character_doc.update(input)
				db.collection('Entities').update(character_doc)
				if (location_id := input.get('location')) is not None:
					# print(f"CreateOrUpdateCharacter:\tlocation_id: { location_id }")
					loc_doc = db.collection('Entities').get(location_id)
					loc_doc['known_to'] = list(set((loc_doc.get('known_to') or []) + [character_doc.get('_id')]))
					db.collection('Entities').update(loc_doc)
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
		return db.collection('Entities').get(parent.id).get('description')

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
			character_entities = [entity for entity in entities if entity.get('type') == 'character']
			for other_entity in character_entities:
				if other_entity.get('_id') != entity.get('_id') and (entity.get('known_to') or []).count(other_entity.get('_id')) == 0:
					if entity.get('known_to') is None:
						entity['known_to'] = []
					entity['known_to'].append(other_entity.get('_id'))
			db.collection('Entities').update(entity)

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
		# print("Creating location: ", location_input)
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
		key = ID(required=True)
		location_input = LocationInput(required=False)

	location = Field(Location)

	def mutate(self, info, key, location_input=None):
		# id = 'Entities' + key
		loc = db.collection('Entities').get(key)
		if location_input:
			loc = {
				**loc,
				**location_input
			}
			db.collection('Entities').update(loc)
		return UpdateLocation(location=Location(id=loc['_id']))



class Relation(ObjectType):
	id = ID()
	from_entity = Field(lambda: Entity)
	to_entity = Field(lambda: Entity)
	traitsets = List(lambda: Traitset)
	favorite = Boolean()

	def resolve_from_entity(parent, info):
		entity_id = db.collection('Relations').get(parent.id).get('_from')
		entity_type = db.collection('Entities').get(entity_id).get('type')
		# print("Relation.resolve_entity:\tentity_id: ", entity_id, "\tentity_type: ", entity_type)
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
		entity_id = db.collection('Relations').get(parent.id).get('_to')
		entity_type = db.collection('Entities').get(entity_id).get('type')
		# print("Relation.resolve_entity:\tentity_id: ", entity_id, "\tentity_type: ", entity_type)
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
			# print("Relation.resolve_traitsets:\tquery: ", query)
			cursor = db.aql.execute(query)
			traits = [Trait(id=doc.get('trait'), trait_setting_id=doc.get('traitsetting')) for doc in cursor]
			result.append(Traitset(id=traitset_id, traits=traits))
		return result

	def resolve_favorite(parent, info):
		return db.collection('Relations').get(parent.id).get('favorite')

class CreateRelation(Mutation):
	class Arguments:
		from_id = ID(required=True)
		to_id = ID(required=True)
		type = String()

	success = Boolean()
	message = String()

	def mutate(root, info, from_id=None, to_id=None, type=None):
		if db.collection('Relations').find({'_from': from_id, '_to': to_id, 'type': type}).empty():
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
		relation = db.collection('Relations').get(id)
		relation['favorite'] = favorite
		db.collection('Relations').update(relation)
		return UpdateRelation(relation=Relation(id=id, favorite=favorite))

class DeleteRelation(Mutation):
	class Arguments:
		relation_id = ID(required=True)

	success = Boolean()

	def mutate(self, info, relation_id):
		traits = db.collection('TraitSettings').find({'_from': relation_id})
		for trait in traits:
			db.collection('TraitSettings').delete(trait.get('_id'))
		db.collection('Relations').delete(relation_id)
		return DeleteRelation(success=True)



class Query(ObjectType):
	session = Field(Session)
	def resolve_session(parent, info):
		return Session()

	characters = List(Character, key=ID(required=False), available=Boolean(required=False))
	def resolve_characters(parent, info, key=None, available=None):
		# print("character resolver, for key: ", key)
		if not key and not available:
			cursor = db.collection('Entities').find({'type': 'character'})
			return [Character(id = doc['_id']) for doc in cursor]
		elif not key and available:
			cursor = db.collection('Entities').get_many([char.get('character') for char in session_characters])
			return [Character(id = doc['_id']) for doc in cursor]
		else:
			character = db.collection('Entities').get(key)
			info.context['entity_id'] = character['_id']
			return [Character(id = character['_id'])]

	factions = List(Faction, key=ID(required=False))
	def resolve_factions(parent, info, key=None):
		if not key:
			cursor = db.collection('Entities').find({'type': 'faction'})
			return [Faction(id = doc['_id']) for doc in cursor]
		else:
			faction = db.collection('Entities').get(key)
			info.context['entity_id'] = faction['_id']
			return [Faction(id = faction['_id'])]

	assets = List(Asset, key=ID(required=False))
	def resolve_assets(parent, info, key=None):
		if not key:
			cursor = db.collection('Entities').find({'type': 'asset'})
			return [Asset(id = doc['_id']) for doc in cursor]
		else:
			asset = db.collection('Entities').get(key)
			info.context['entity_id'] = asset['_id']
			return [Asset(id = asset['_id'])]

	npcs = List(NPC, key=ID(required=False))
	def resolve_npcs(parent, info, key=None):
		if not key:
			cursor = db.collection('Entities').find({'type': 'npc'})
			return [NPC(id = doc['_id']) for doc in cursor]
		else:
			npc = db.collection('Entities').get(key)
			info.context['entity_id'] = npc['_id']
			return [NPC(id = npc['_id'])]

	entities = List(Entity,
				 key=ID(required=False),
				 entity_type=String(required=False),
				 search=String(required=False))
	def resolve_entities(parent, info, key=None, entity_type=None, search=None):
		# print("entity resolver, for key: ", key)
		if not key and not entity_type:
			query = "FOR e IN Entities "
			if search:
				query += "FILTER LOWER(e.name) LIKE LOWER('%" + search + "%') "
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
		elif not key and entity_type is not None:
			query = "FOR e IN Entities "
			if search:
				query += "FILTER LOWER(e.name) LIKE LOWER('%" + search + "%') "
			query += f"""FILTER e.type == '{ entity_type }'
			SORT e.name ASC
			RETURN e"""
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
		elif key is not None:
			entity = db.collection('Entities').get(key)
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
		sorting=String(required=False))
	def resolve_traitsets(parent, info, traitset_id=None, entity_id=None, entity_type=None, sorting=None):
		query = None
		if traitset_id is not None:
			if entity_id is not None:
				info.context['entity_id'] = entity_id
			if sorting is not None:
				info.context['sorting'] = sorting
			return [Traitset(id=traitset_id)]
		elif entity_type is not None:
			# return all traitsets of a given entity type
			query = f"""FOR traitsets IN Traitsets
				FILTER '{ entity_type }' IN traitsets.entity_types
				SORT traitsets.order ASC
				RETURN {{ 'id': traitsets._id, 'name': traitsets.name }}"""
			# print("retrieving traitsets for entity type: ", query)
		else:
			query = f"""FOR traitsets IN Traitsets
				SORT traitsets.order ASC, traitsets.name ASC
				RETURN {{ 'id': traitsets._id, 'name': traitsets.name }}"""
		if query is not None:
			cursor = db.aql.execute(query)
			result = [
				Traitset(id = doc['id'], name = doc['name'])
				for doc in cursor
			]
			return result
		else:
			return []

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
			trait_setting = db.collection('TraitSettings').get(trait_setting_id)
			# check if it is a default trait
			if trait_setting is not None and trait_id is not None and trait_setting.get('_from') == trait_id and trait_setting.get('_to') == 'Traits/1':
				return [Trait(id=trait_id, trait_setting_id=trait_setting_id, trait_setting=trait_setting)]
			return [Trait(id=trait_setting.get('_to'), trait_setting_id=trait_setting_id, trait_setting=trait_setting)]

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
			traitset = db.collection('Traitsets').get(traitset_id)
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
			# print("resolve_traits\tpotential traits query\n", query)
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
			doc = db.collection('SFXs').get(sfx_id)
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

	locations = List(Location, key=ID(required=False))
	def resolve_locations(parent, info, key=None):
		# print("Query.resolve_locations:\tkey: ", key)
		if not key:
			cursor = db.collection('Entities').find({'type': 'location'})
			return [
				Location(id=doc['_id'], name = doc['name'])
				for doc in cursor
			]
		else:
			location_id = db.collection('Entities').get(key).get('_id')
			info.context['entity_id'] = location_id
			result = Location(id=location_id)
			# print(result)
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

	create_traitset = CreateTraitset.Field()
	mutate_traitset = MutateTraitset.Field()
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

schema = Schema(query=Query, mutation=Mutation)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view(
	'graphql',
	schema=schema,
	graphiql=True,
))


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
	# print(f"filter_trait_settings_by_location:\n\ttrait_settings: {[trait_setting.get('_id') for trait_setting in trait_settings]}")
	hierarchy_ids = [location.get('_id') for location in tv.retrieve_hierarchy(location_id)]
	# print(f"filter_trait_settings_by_location:\n\thierarchy_ids: {hierarchy_ids}")
	for trait_setting in trait_settings:
		# print(f"filter_trait_settings_by_location:\n\tProcessing trait setting: {trait_setting.get('_id')}")
		determined = False
		for location_id in hierarchy_ids:
			# print(f"filter_trait_settings_by_location:\n\tChecking location_id {location_id} in enabled locations")
			if trait_setting.get('locations_enabled') and location_id in trait_setting.get('locations_enabled'):
				result.append(trait_setting)
				determined = True
				# print("filter_trait_settings_by_location:\n\tTrait setting enabled at this location, added to result")
				break
			elif trait_setting.get('locations_disabled') and location_id in trait_setting.get('locations_disabled'):
				determined = True
				# print("filter_trait_settings_by_location:\n\tTrait setting disabled at this location, not added")
				break
		if not determined and trait_setting.get('_to') is not None and trait_setting.get('_to') != 'Traits/1':
			# print("filter_trait_settings_by_location:\n\tChecking default trait setting")
			default_trait_setting = db.collection('TraitSettings').find({ '_from': trait_setting.get('_to'), '_to': 'Traits/1' })
			if not default_trait_setting.empty():
				default_trait_setting = [doc for doc in default_trait_setting][0]
				for location_id in hierarchy_ids:
					# print(f"filter_trait_settings_by_location:\n\tChecking location_id {location_id} in default enabled locations")
					if default_trait_setting.get('locations_enabled') and location_id in default_trait_setting.get('locations_enabled'):
						result.append(trait_setting)
						determined = True
						# print("filter_trait_settings_by_location:\n\tDefault trait setting enabled, added to result")
						break
					elif default_trait_setting.get('locations_disabled') and location_id in default_trait_setting.get('locations_disabled'):
						determined = True
						# print("filter_trait_settings_by_location:\n\tDefault trait setting disabled, not added")
						break
		if not determined and trait_setting.get('_from') is not None and not trait_setting.get('_from').startswith('Traitsets'):
			# print("filter_trait_settings_by_location:\n\tChecking traitset default setting")
			traitset_id = db.collection('Traits').get(trait_setting.get('_to')).get('traitset')
			traitset_setting = db.collection('TraitSettings').find({ '_from': traitset_id, '_to': 'Traits/1' })
			if not traitset_setting.empty():
				traitset_setting = [doc for doc in traitset_setting][0]
				for location_id in hierarchy_ids:
					# print(f"filter_trait_settings_by_location:\n\tChecking location_id {location_id} in traitset enabled locations")
					if traitset_setting.get('locations_enabled') and location_id in traitset_setting.get('locations_enabled'):
						result.append(trait_setting)
						determined = True
						# print("filter_trait_settings_by_location:\n\tTraitset default setting enabled, added to result")
						break
					elif traitset_setting.get('locations_disabled') and location_id in traitset_setting.get('locations_disabled'):
						determined = True
						# print("filter_trait_settings_by_location:\n\tTraitset default setting disabled, not added")
						break
		if not determined:
			result.append(trait_setting)
			# print("filter_trait_settings_by_location:\n\tNo location restrictions, added trait setting to result")
			# print(f"filter_trait_settings_by_location:\n\tNo location restrictions, ignoring trait setting")
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
		location = db.collection('Entities').get(location_id)
		if location.get('type') != 'location':
			# if the location is not a location, get the location from its location attribute
			location = retrieve_location(location)
	elif entity.get('_id') != 'Entities/2':
		# if the entity is a location, get the location from its super relations
		location_id = [doc.get('_to') for doc in db.collection('Relations').find({ '_from': entity.get('_id'), 'type': 'super' })][0]
		location = db.collection('Entities').get(location_id)
	else:
		location = entity
	return location

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

@app.route("/pick-character/<uuid>/<character>", methods = ['POST'])
def pick_character(uuid, character):
	if uuid not in [d['uuid'] for d in session_characters] and character not in [d['character'] for d in session_characters]:
		session_characters.append({
			"uuid": uuid,
			"character": character
		})
		return { "success": True }

	elif character not in [d['character'] for d in session_characters]:
		for sc in session_characters:
			if sc["uuid"] == uuid:
				sc["character"] = character
				return { "success": True }
	
	character_doc = db.collection('Entities').get(character)
	character_doc['active'] = True
	db.collection('Entities').update(character_doc)

	return { "success": False }

@app.route("/deactivate-character/<character>", methods = ['POST'])
def deactivate_character(character):
	if character in [d['character'] for d in session_characters]:
		for sc in session_characters:
			if sc["character"] == character:
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
	# print("received request to upload file")
	file = request.files['file']
	file_extension = os.path.splitext(file.filename)[1]
	entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], entity_key)
	# print("entity_folder: ", entity_folder)
	if not os.path.exists(entity_folder):
		# print("creating folder: ", entity_folder)
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
	image_small.save(os.path.join(app.config['UPLOAD_FOLDER'], entity_key, f"small{ file_extension.lower() }"))
	image_mini.save(os.path.join(app.config['UPLOAD_FOLDER'], entity_key, f"mini{ file_extension.lower() }"))
	image_large.save(os.path.join(app.config['UPLOAD_FOLDER'], entity_key, f"large{ file_extension.lower() }"))
	image_without_exif.save(os.path.join(app.config['UPLOAD_FOLDER'], entity_key, f"original{ file_extension.lower() }"))
	return jsonify({ "success": True })

@app.route("/upload/<entity_key>/<location_key>", methods = ['POST'])
def upload_file_location(entity_key, location_key):
	# print("received request to upload file")
	file = request.files['file']
	file_extension = os.path.splitext(file.filename)[1]
	entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], entity_key, location_key)
	# print("entity_folder: ", entity_folder)
	if not os.path.exists(entity_folder):
		# print("creating folder: ", entity_folder)
		os.makedirs(entity_folder)
	# filename = f"{ entity_id }{ file_extension }"
	# filename = secure_filename(file.filename)
	image = Image.open(file)
	hierarchy = tv.retrieve_hierarchy('Entities/' + location_key)
	# print("hierarchy: ", hierarchy)
	location_key = hierarchy[-2].get('_key')
	path = os.path.join(app.config['UPLOAD_FOLDER'], entity_key, location_key, f"original{ file_extension.lower() }")
	# print("image path: ", path)
	if not os.path.exists(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))
	image.save(path)
	save_image(path, entity_key, location_key)
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
		"wuxia": "import/Xia3",
		"modern": "import/ModernCartoon-Gudarzi",
		"fantasy": "import/FantasyIllustration",
		"scifi": "setting/ScifiEnvironment",
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
	}

	# variables used in the generation
	width = 832
	height = 1216
	lora1 = "import/DigitalFantasyIllustration"
	lora1_weight = 0.0
	lora2 = "style/Anime art"
	lora2_weight = 0.4
	genres = []

	entity = db.collection('Entities').get(entity_key)

	if not entity.get('imagening') or force == "true":

		entity_type = entity.get('type')
		location_key = None
		if entity_type != "location":
			location_id = entity.get('location')
			location = db.collection('Entities').get(location_id)
			if entity.get('type') != 'location':
				if location.get('type') == 'location':
					location_key = location.get('_key')
				else:
					# if entity is following
					location_id = location.get('location')
					location = db.collection('Entities').get(location_id)
					location_key = location.get('_key')
				hierarchy = tv.retrieve_hierarchy(location_id)
				if len(hierarchy) > 1:
					location_key = hierarchy[-2].get('_key')
		name = entity.get('name')
		description = entity.get('description')
		negative = "cgi, 3d, bad quality, watermark, signature"

		if entity_type in ["character", "npc"]:
			prompt = f"(a solo upper body character portrait of { name }:1.2), head, shoulders, "
			negative += ", full body, legs, cropped head"
			genre_loras['realistic'] = "frame/RealFaceji"
		elif entity_type == "asset":
			prompt = f"(an image of { name }:1.2), "
			negative += ", person"
			width = 1216
			height = 832
		elif entity_type == "faction":
			prompt = f"(a symbol or logo or flag or shield or emblem:1.2) representing the faction called { name }. "
			negative += ", photo, person, environment"
			width = 1024
			height = 1024
		elif entity_type == "location":
			prompt = f"(location background image, a humanless atmospheric image focusing on { name }:1.2), "
			negative += ", person"

		if entity_type in ["character", "npc", "asset"]:
			entity = db.collection('Entities').get(entity_key)
			location = retrieve_location(entity)
			trait_settings = [doc for doc in db.collection('TraitSettings').find({'_from': entity.get('_id')})]
			trait_settings = filter_trait_settings_by_location(trait_settings, location.get('_id'))
			traits = []
			for trait_setting in trait_settings:
				trait_id = trait_setting.get('_to')
				trait = db.collection('Traits').get(trait_id)
				traitset_id = trait.get('traitset')
				traitset = db.collection('Traitsets').get(traitset_id)
				traits.append((traitset, trait, trait_setting))

			prompt += "("
			prompt += f"({entity.get('description')}), " if entity.get('description') else ""
			for traitset, trait, trait_setting in traits:
				if trait.get('name') == 'appearance':
					prompt += "("
					prompt += trait_setting.get('statement') if trait_setting.get('statement') else ""
					prompt += ", " if trait_setting.get('statement') and trait_setting.get('notes') else ""
					prompt += trait_setting.get('notes') if trait_setting.get('notes') else ""
					prompt += ":1.4)"
				elif trait.get('name') == 'negative imagen':
					# negative += f"{', '.join([trait_setting.get('statement'), trait_setting.get('notes')])}"
					negative += "," + trait_setting.get('statement') if trait_setting.get('statement') else ""
					negative += ", " + trait_setting.get('notes') if trait_setting.get('notes') else ""
				else:
					# prompt += f"({', '.join([trait.get('name'),trait_setting.get('statement'),trait_setting.get('notes')])}:{ str(rating_weights[abs(t[3]) - 1]) })"
					prompt += "("
					prompt += traitset.get('prompt_prefix') if traitset.get('prompt_prefix') else traitset.get('name') + " "
					prompt += trait.get('name')
					prompt += ", " if trait_setting.get('statement') else ""
					prompt += trait_setting.get('statement') if trait_setting.get('statement') else ""
					prompt += ", " if trait_setting.get('notes') else ""
					prompt += trait_setting.get('notes') if trait_setting.get('notes') else ""
					prompt += ":" if trait_setting.get('rating') and trait_setting.get('rating_type') != "empty" else ""
					prompt += str(rating_weights[abs(trait_setting.get('rating')[0]) - 1]) if trait_setting.get('rating') and trait_setting.get('rating_type') != "empty" else ""
					prompt += ")"
				prompt += ", "

			prompt = prompt[:-2] # remove the last comma
			prompt += ":1.2), "
			
			positive_imagen = []

			hierarchy = tv.retrieve_hierarchy(location.get('_id'))
			for loc in hierarchy:
				if entity_type in ["npc", "asset"]:
					prompt += f" (located in { loc.get('name') }, { loc.get('description') }"
				loc_trait_settings = db.collection('TraitSettings').find({'_from': loc.get('_id')})
				for lts in loc_trait_settings:
					trait_id = lts.get('_to')
					trait = db.collection('Traits').get(trait_id)
					if trait.get('name') == 'genre':
						genres.append(lts.get('statement'))
					elif trait.get('name') == 'positive imagen':
						positive_imagen.append(lts.get('statement')) if lts.get('statement') else ""
						positive_imagen.append(lts.get('notes')) if lts.get('notes') else ""
					elif trait.get('name') == 'negative imagen':
						negative += ", " + lts.get('statement') if lts.get('statement') else ""
						negative += ", " + lts.get('notes') if lts.get('notes') else ""
			strength = 0.4
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
			prompt += "), "
			prompt += "(" + ", ".join(positive_imagen) + ":0.8)"



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
					RETURN [t.name, s.statement, s.rating[0]]
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

				if len(doc.get('zones')) > 0:
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
					location_strength = 0.6
					for l in doc['hierarchy'][1:]:
						location_strength = location_strength * 0.2
						if location_strength >= 0.2:
							location_name = l[0]
							location_description = l[1]
							lts = l[2]
							for lt in lts:
								if lt[0].startswith("genre"):
									genres.append(lt[1])
								elif lt[0] == "negative imagen":
									negative += ", " + lt[1]
							prompt += " (" + location_name + ", " + location_description
						else:
							lts = l[2]
							for lt in lts:
								if lt[0].startswith("genre"):
									genres.append(lt[1])
					location_strength = 1.2
					strengths = []
					for l in doc['hierarchy'][1:]:
						location_strength = location_strength * 0.2
						if location_strength >= 0.2:
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
				RETURN [t.name, s.statement, s.rating[0]]
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
							traits.append(f"({t[0]}{' is ' + t[1] if t[1] else ''}:1.4), ")
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
			lora1 = genre_loras.get(genres[0])
			lora1_weight = 0.8
			if len(genres) > 1:
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
		db.collection('Entities').update(entity)
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
		entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], entity_key)
	else:
		entity_folder = os.path.join(app.config['UPLOAD_FOLDER'], entity_key, location_key)
	if not os.path.exists(entity_folder):
		os.makedirs(entity_folder)

	# Save images
	image_small.save(os.path.join(entity_folder, f"small{file_extension.lower()}"))
	image_mini.save(os.path.join(entity_folder, f"mini{file_extension.lower()}"))
	image_large.save(os.path.join(entity_folder, f"large{file_extension.lower()}"))
	image_without_exif.save(os.path.join(entity_folder, f"original{file_extension.lower()}"))

	entity = db.collection('Entities').get(entity_key)
	entity['imagening'] = False
	entity['imagened'] = True
	db.collection('Entities').update(entity)

	return jsonify({"success": True})

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=5000)
