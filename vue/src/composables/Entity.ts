import type { ApolloClient, FetchPolicy } from '@apollo/client'
import { provideApolloClient, useMutation } from '@vue/apollo-composable'
import gql from 'graphql-tag'

import { ref, computed, inject } from 'vue'
import { useRating } from '@/composables/Rating'
import type { Entity, EntityInput, Location, Relation, Trait, Traitset } from '@/interfaces/Types'

import { useFetch } from '@vueuse/core'

export const entity_icons: Record<string, string> = {
	"character": "👤",
	"npc": "🎭",
	"location": "🧭",
	"asset": "🛠",
	"faction": "🛡",
	"gm": "👑",
	"empty": "🚫"
}

export function useEntity(init?: Entity, entity_id?: string) {
	const apolloClient: ApolloClient<any>|undefined = inject('apolloClient')
	const entity = ref({} as Entity)
	const API_URL = inject('API_URL')

	const entity_type_icon = computed(() => {
		if(entity.value && entity.value.entityType == 'character'){
			return "👤"
		}
		else if(entity.value && entity.value.entityType == 'npc'){
			return "🎭"
		}
		else if(entity.value && entity.value.entityType == 'location'){
			return "🧭"
			// return "📍"
		}
		else if(entity.value && entity.value.entityType == 'asset'){
			return "🛠"
		}
		else if(entity.value && entity.value.entityType == 'faction'){
			return "🛡"
		}
	})

	function set_entity_id(new_entity_id: string) {
		entity_id = new_entity_id
		// retrieve_small_entity()
	}

	function retrieve_small_entity() {

		const small_entity_query = gql`query SmallEntity($entityId: ID) {
			entities(entityId: $entityId) {
				key
				id
				name
				entityType
				isArchetype
				image {
					path
					ext
				}
				favorite
				active
				... on Character {
					available
				}
				hidden
				knownTo {
					id
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/') && !entity_id.endsWith('undefined')) {
			apolloClient.query({
				query: small_entity_query,
				variables: { entityId: entity_id },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.entities[0]
				}
			}).catch((error) => {
				console.error(error)
			})
		}
	}

	function retrieve_entity() {
		console.log("retrieving entity: ", entity_id)
		const query = gql`query FullEntity($entityId: ID) {
			entities(entityId: $entityId) {
				key
				id
				name
				description
				pp
				hidden
				active
				entityType
				isArchetype
				archetype {
					id
					image {
						path
						ext
					}
				}
				archetypes {
					id
				}
				image {
					path
					ext
					width
					height
				}
				imagened
				location {
					key
					id
					name
					image {
						path
						ext
					}
				}
				following {
					id
				}
				relations {
					id
					toEntity {
						id
					}
				}
				knownTo {
					id
				}
				instances {
					id
				}
				traitsets {
					id
					name
				}
				favorite
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/') && entity_id != 'Entities/undefined') {
			apolloClient.query({
				query: query,
				variables: { entityId: entity_id },
				fetchPolicy: 'network-only'
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.entities[0]
				}
			}).catch((error) => {
				console.error("error retrieving entity: ", entity_id, "error: ", error)
			})
		}
	}

	/**
	 * Retrieves the full entity from the server
	 * 
	 * Carefull! This is a big query
	 */
	async function retrieve_full_entity() {
		const query = gql`query FullEntity($entityId: ID) {
			entities(entityId: $entityId) {
				key
				id
				name
				description
				pp
				hidden
				active
				entityType
				isArchetype
				archetype {
					id
					image {
						path
						ext
					}
				}
				archetypes {
					id
				}
				image {
					path
					ext
					width
					height
				}
				imagened
				location {
					key
					id
					name
					image {
						path
						ext
					}
				}
				following {
					id
				}
				relations {
					id
					fromEntity {
						id
					}
					toEntity {
						id
						entityType
					}
				}
				knownTo {
					id
				}
				instances {
					id
				}
				traitsets {
					id
					name
					explainer
					entityTypes
					duplicates
					sfxs {
						id
					}
					traits {
						id
						traitSettingId
						name
						rating
						ratingType
						inheritable
						subTraits {
							traitSettingId
						}
						requiredTraits {
							id
						}
						traitSetting {
							fromEntity {
								id
							}
							knownTo {
								id
							}
							statement
							notes
							hidden
							priority
						}
					}
				}
				favorite
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/') && entity_id != 'Entities/undefined' && entity_id != 'Entities/placeholder') {
			console.log("retrieving full entity! ", entity_id)
			apolloClient.query({
				query: query,
				variables: { entityId: entity_id },
				fetchPolicy: 'network-only'
			}).then((result) => {
				let traitsets: Traitset[] = []
				result.data.entities[0].traitsets.forEach((ts: Traitset) => {
					let traits: Trait[] = []
					ts.traits?.forEach((t: Trait) => {
						const rating = useRating().convert_rating_to_dice(
							t.rating,
							t.ratingType,
							t.id,
							t.traitSettingId,
							ts.id,
							entity_id
						)
						traits.push({
							...t,
							"rating": rating
						})
					})
					traitsets.push({
						...ts,
						"traits": traits
					})
				})
				entity.value = {
					...entity.value,
					...result.data.entities[0],
					"traitsets": traitsets
				}
			}).catch((error) => {
				console.error("error retrieving entity: ", entity_id, "error: ", error)
			})
		}
	}

	function toggle_favorite() {
		const toggle_favorite_query = gql`mutation ToggleFavorite($entityId: ID!, $favorite: Boolean!) {
				updateEntity(entityId: $entityId, favorite: $favorite) {
					entity {
						id
						favorite
					}
				}
			}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(toggle_favorite_query))
			mutate({
				entityId: entity_id,
				favorite: !entity.value.favorite
			}).then((response) => {
				if(response?.data?.updateEntity?.entity) {
					entity.value = {
						...entity.value,
						...response.data?.updateEntity?.entity
					}
				}
			}).catch((error) => {
				console.error(error)
			})
		}
	}

	async function retrieve_relations(caching: FetchPolicy = 'cache-first') {

		const relations_query = gql`query EntityRelations($entityId: ID) {
			entities(entityId: $entityId) {
				relations {
					id
					fromEntity {
						id
					}
					toEntity {
						id
						entityType
						name
					}
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			console.log("retrieving relations! ", entity_id)
			apolloClient.query({
				query: relations_query,
				variables: { entityId: entity_id },
				fetchPolicy: caching
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.entities[0]
				}
			}).catch((error) => {
				console.error(error)
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		relations_query,
			// 		{ entityId: entity_id },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, () => {
			// 	entity.value = {
			// 		...entity.value,
			// 		...result.value.entities[0]
			// 	}
			// })
		}
	}

	function retrieve_followers() {

		const followers_query = gql`query EntityFollowers($entityId: ID) {
			entities(entityId: $entityId) {
				followers {
					id
					entityType
					name
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			apolloClient.query({
				query: followers_query,
				variables: { entityId: entity_id },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.entities[0]
				}
			}).catch((error) => {
				console.error("error retrieving followers: ", entity_id, "error: ", error)
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		followers_query,
			// 		{ entityId: entity_id },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, () => {
			// 	entity.value = {
			// 		...entity.value,
			// 		...result.value.entities[0]
			// 	}
			// })
		}
	}

	function retrieve_archetypes(caching: FetchPolicy = 'cache-first') {

		const archetypes_query = gql`query EntityArchetypes($entityId: ID) {
			entities(entityId: $entityId) {
				archetypes {
					key
					id
					entityType
					name
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			apolloClient.query({
				query: archetypes_query,
				variables: { entityId: entity_id },
				fetchPolicy: caching
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.entities[0]
				}
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		archetypes_query,
			// 		{ entityId: entity_id },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, () => {
			// 	console.log('entity archetypes result', result.value.entities[0])
			// 	entity.value = {
			// 		...entity.value,
			// 		...result.value.entities[0]
			// 	}
			// 	console.log("entity result", entity.value)
			// })
		}
	}

	function retrieve_instances() {
		/* if current entity is an archetype, retrieve all entities with that archetype */
		const instances_query = gql`query EntityInstances($entityId: ID) {
			entities(entityId: $entityId) {
				instances {
					id
					entityType
					name
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			apolloClient.query({
				query: instances_query,
				variables: { entityId: entity_id },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.entities[0]
				}
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		instances_query,
			// 		{ entityId: entity_id },
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, () => {
			// 	entity.value = {
			// 		...entity.value,
			// 		...result.value.entities[0]
			// 	}
			// })
		}
	}

	function update_entity(input: EntityInput) {
		/* post character changes to the server */
		const query_update_entity = gql`mutation UpdateEntity($entityId: ID!, $entityInput: EntityInput) {
			updateEntity(entityId: $entityId, entityInput: $entityInput) {
				entity {
					id
					name
					description
					pp
					entityType
					favorite
					isArchetype
					hidden
					knownTo {
						id
						name
					}
					location {
						key
						id
						name
						image {
							path
							ext
						}
					}
				}
			}
		}`
		if(apolloClient) {
			console.log("updating entity ", (entity_id ?? entity.value.id), " input: ", input)
			apolloClient.mutate({
				mutation: query_update_entity,
				variables: {
					"entityId": entity_id ?? entity.value.id,
					"entityInput": input
				}
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.updateEntity.entity
				}
			})
		}
	}

	function activate_entity() {
		/* post character changes to the server */
		const query_update_entity = gql`mutation ActivateEntity($entityId: ID!, $active: Boolean) {
			updateEntity(entityId: $entityId, active: $active) {
				entity {
					id
					entityType
					active
				}
			}
		}`
		if(apolloClient && (entity_id || entity.value.id)) {
			apolloClient.mutate({
				mutation: query_update_entity,
				variables: {
					"entityId": entity_id ?? entity.value.id,
					"active": true
				}
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.updateEntity.entity
				}
			})
		}
	}

	function deactivate_entity(_entity_id?: string) {
		/* post character changes to the server */
		const query_update_entity = gql`mutation DeactivateEntity($entityId: ID!, $active: Boolean) {
			updateEntity(entityId: $entityId, active: $active) {
				entity {
					id
					entityType
					active
				}
			}
		}`
		if(apolloClient && entity) {
			console.log("deactivating entity, _entity_id: ", _entity_id, ", entity_id: ", entity_id, ", entity.id: ", entity.value.id)
			apolloClient.mutate({
				mutation: query_update_entity,
				variables: {
					"entityId": _entity_id ?? entity_id ?? entity.value.id,
					"active": false
				}
			}).then((result) => {
				entity.value = {
					...entity.value,
					...result.data.updateEntity.entity
				}
			})
		}
	}

	async function clone_entity(name?: string, location_id?: string) {
		/* post character changes to the server */
		console.log('cloning entity (A): ' + entity.value.name)
		const query_clone_entity = gql`mutation CloneEntity($entityId: ID!${ name ? ', $name: String' : '' }${ location_id ? ', $locationId: ID' : '' }) {
			instantiateArchetype(entityId: $entityId${ name ? ', name: $name' : '' }${ location_id ? ', locationId: $locationId' : '' }) {
				entity {
					id
					key
					entityType
				}
			}
		}`
		if(apolloClient) {
			let cloned_entity = {}
			await apolloClient.mutate({
				mutation: query_clone_entity,
				variables: {
					"entityId": entity_id ?? entity.value.id,
					"name": name,
					"locationId": location_id
				}
			}).then((result) => {
				console.log('cloned entity (B): ' + JSON.stringify(result.data.instantiateArchetype.entity))
				// return result.data.instantiateArchetype.entity
				cloned_entity = result.data.instantiateArchetype.entity
			})
			return cloned_entity
		}
	}

	function delete_entity() {
		/* post character changes to the server */
		console.log('deleting character: ' + entity.value.key)
		const query_delete_entity = gql`mutation DeleteEntity($entityId: ID!) {
			deleteEntity(entityId: $entityId) {
				success
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_delete_entity))
			console.log('deleting character: ' + entity.value.key)
			mutate({
				"entityId": entity_id ?? entity.value.id,
			})
		}
	}

	function prune_location() {
		/* post character changes to the server */
		console.log('pruning location: ' + entity.value.key)
		const query_prune_location = gql`mutation PruneLocation($entityId: ID!, $rmtree: Boolean) {
			deleteEntity(entityId: $entityId, rmtree: $rmtree) {
				message
				success
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_prune_location))
			console.log('pruning location: ' + entity.value.key)
			mutate({
				"entityId": entity_id ?? entity.value.id,
				"rmtree": true
			})
		}
	}

	/**
	 * sets the location of this entity in the database
	 * @param location the location to set the entity to
	 */
	function set_location(location: Location) {
		update_entity({ location: location.id })
	}

	async function set_entity_location(entity_id: string, location_id: string) {
		/* change an entity's location */
		const query_update_entity_location = gql`mutation UpdateEntityLocation($entityId: ID!, $locationId: ID!) {
			updateEntity(location: $locationId, entityId: $entityId) {
				entity {
					id
				}
			}
		}`
		if(apolloClient) {
			await apolloClient.mutate({
				mutation: query_update_entity_location,
				variables: {
					"entityId": entity_id,
					"locationId": location_id
				}
			})
		}
	}

	/**
	 * creates a relation from given entity to set entity, with the type "relation"
	 * @param entity_id the id of the entity to create a relation from
	 */
	async function create_relation(from_id: string = entity.value.id, to_id: string = entity.value.id): Promise<Relation|undefined> {
		/* create a relation between this character and an entity */
		const query_create_relation = gql`mutation CreateRelation($fromId: ID!, $toId: ID!, $type: String) {
				createRelation(fromId: $fromId, toId: $toId, type: $type) {
					success
					message
					relation {
						id
						fromEntity {
							id
						}
						toEntity {
							id
						}
					}
				}
			}`
		if(apolloClient) {
			const result = await apolloClient.mutate({
				mutation: query_create_relation,
				variables: {
					"fromId": from_id,
					"toId": to_id,
					"type": "relation"
				}
			})
			console.log(result.data.createRelation.message)
			return result.data.createRelation.relation
		}
	}

	async function delete_relation(relation_id: string) {
		const mutation_delete_relation = gql`mutation DeleteRelation($relationId: ID!) {
			deleteRelation(relationId: $relationId) {
				success
			}
		}`
		if(apolloClient && relation_id) {
			await apolloClient.mutate({
				mutation: mutation_delete_relation,
				variables: {
					relationId: relation_id
				}
			})
		}
	}

	/**
	 * sets the archetype of this entity
	 * @param archetype_id the id of the archetype entity
	 */
	async function set_archetype(archetype_id: string) {
		/* create a relation between this character and an entity */
		const query_create_relation = gql`mutation CreateRelation($fromId: ID!, $toId: ID!, $type: String) {
				createRelation(fromId: $fromId, toId: $toId, type: $type) {
					success
				}
			}`
		if(apolloClient) {
			await apolloClient.mutate({
				mutation: query_create_relation,
				variables: {
					"fromId": entity.value.id,
					"toId": archetype_id,
					"type": "archetype"
				}
			}).then(() => {
				retrieve_archetypes('network-only')
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_create_relation))
			// console.log('setting archetype of ' + entity.value.name + ' to ' + archetype_id)
			// mutate({
			// 	"fromId": entity.value.id,
			// 	"toId": archetype_id,
			// 	"type": "archetype"
			// })
		}
	}

	async function unset_archetype(archetype_id: string) {
		const query_delete_relation = gql`mutation DeleteRelation($fromId: ID!, $toId: ID!, $type: String) {
				deleteRelation(fromId: $fromId, toId: $toId, type: $type) {
					success
				}
			}`
		if(apolloClient && (entity.value.archetype || entity.value.archetypes)) {
			await apolloClient.mutate({
				mutation: query_delete_relation,
				variables: {
					"fromId": entity.value.id,
					"toId": archetype_id,
					"type": "archetype"
				}
			}).then(() => {
				retrieve_archetypes('network-only')
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query_delete_relation))
			// console.log('unsetting archetype of ' + entity.value.name)
			// mutate({
			// 	"fromId": entity.value.id,
			// 	"toId": archetype_id,
			// 	"type": "archetype"
			// })
		}
	}

	/**
	 * send generate image request
	 * @param force override is_player check
	 */
	function imagen(force: boolean = false) {
		const url = API_URL + "imagen/" + entity.value.key + "/" + force
		console.log("generating image for: " + entity.value.key + " (" + url + ")")
		interface API_result {
			success: boolean
		}
		useFetch<API_result>(url, { method: 'POST' }).post().json()
	}

	// onMounted(() => {
	// 	if(entity_id && !entity.value) {
	// 		retrieve_entity()
	// 	}
	// })

	return {
		entity,
		entity_id,
		set_entity_id,
		retrieve_small_entity,
		retrieve_entity,
		retrieve_full_entity,
		toggle_favorite,
		retrieve_relations,
		delete_relation,
		retrieve_followers,
		retrieve_archetypes,
		retrieve_instances,
		update_entity,
		activate_entity,
		deactivate_entity,
		clone_entity,
		delete_entity,
		prune_location,
		set_location,
		create_relation,
		set_archetype,
		unset_archetype,
		set_entity_location,
		imagen,
		entity_type_icon
	}
}