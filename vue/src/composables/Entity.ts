import type { ApolloClient } from '@apollo/client'
import { provideApolloClient, useMutation, useQuery } from '@vue/apollo-composable'
import gql from 'graphql-tag'

import { ref, computed, inject, watch } from 'vue'
import type { Entity, EntityInput, Location } from '@/interfaces/Types'

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

	function retrieve_entity() {
		console.log("retrieving entity: ", entity_id)
		const query = gql`query FullEntity($entityId: ID) {
			entities(key: $entityId) {
				key
				id
				name
				description
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
				relations {
					id
					toEntity {
						id
					}
				}
				following {
					id
				}
				instances {
					id
				}
				traitsets {
					id
				}
				favorite
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					query,
					{ entityId: entity_id },
					{ fetchPolicy: 'no-cache' }
				)
			)
			watch(result, () => {
				entity.value = {
					...entity.value,
					...result.value.entities[0]
				}
			})
		}
	}

	function retrieve_small_entity() {

		const small_entity_query = gql`query SmallEntity($entityId: ID) {
			entities(key: $entityId) {
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
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					small_entity_query,
					{ entityId: entity_id },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, () => {
				entity.value = {
					...entity.value,
					...result.value.entities[0]
				}
			})
		}
	}

	function retrieve_relations() {

		const relations_query = gql`query EntityRelations($entityId: ID) {
			entities(key: $entityId) {
				relations {
					id
					toEntity {
						id
						entityType
						name
					}
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					relations_query,
					{ entityId: entity_id },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, () => {
				entity.value = {
					...entity.value,
					...result.value.entities[0]
				}
			})
		}
	}

	function retrieve_followers() {

		const followers_query = gql`query EntityFollowers($entityId: ID) {
			entities(key: $entityId) {
				followers {
					id
					entityType
					name
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					followers_query,
					{ entityId: entity_id },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, () => {
				entity.value = {
					...entity.value,
					...result.value.entities[0]
				}
			})
		}
	}

	function retrieve_instances() {
		/* if current entity is an archetype, retrieve all entities with that archetype */
		const instances_query = gql`query EntityInstances($entityId: ID) {
			entities(key: $entityId) {
				instances {
					id
					entityType
					name
				}
			}
		}`

		if(apolloClient && entity_id && entity_id.startsWith('Entities/')) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					instances_query,
					{ entityId: entity_id },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, () => {
				entity.value = {
					...entity.value,
					...result.value.entities[0]
				}
			})
		}
	}

	function update_entity(input: EntityInput) {
		/* post character changes to the server */
		const query_update_entity = gql`mutation UpdateEntity($key: ID!, $entityInput: EntityInput) {
			updateEntity(key: $key, entityInput: $entityInput) {
				entity {
					id
					entityType
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_update_entity))
			mutate({
				"key": entity.value.key,
				"entityInput": input
			})
		}
	}

	function activate_entity() {
		/* post character changes to the server */
		const query_update_entity = gql`mutation ActivateEntity($key: ID!, $active: Boolean) {
			updateEntity(key: $key, active: $active) {
				entity {
					id
					entityType
				}
			}
		}`
		if(apolloClient && entity.value.key) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_update_entity))
			mutate({
				"key": entity.value.key,
				"active": true
			})
		}
	}

	function deactivate_entity(entity_key?: string) {
		/* post character changes to the server */
		const query_update_entity = gql`mutation DeactivateEntity($key: ID!, $active: Boolean) {
			updateEntity(key: $key, active: $active) {
				entity {
					id
					entityType
				}
			}
		}`
		if(apolloClient && entity) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_update_entity))
			mutate({
				"key": entity_key ?? entity.value.key,
				"active": false
			})
		}
	}

	async function clone_entity(name?: string) {
		/* post character changes to the server */
		console.log('cloning character: ' + entity.value.key)
		const query_clone_entity = gql`mutation CloneEntity($key: ID!${ name ? ', $name: String' : '' }) {
			instantiateArchetype(key: $key${ name ? ', name: $name' : '' }) {
				entity {
					id
					key
					entityType
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_clone_entity))
			console.log('cloning character: ' + entity.value.key)
			const variables = name ? { "key": entity.value.key, "name": name } : { "key": entity.value.key }
			await mutate(variables).then((result) => {
				console.log('clone_entity result', result)
			})
		}
	}

	function delete_entity() {
		/* post character changes to the server */
		console.log('deleting character: ' + entity.value.key)
		const query_delete_entity = gql`mutation DeleteEntity($key: ID!) {
			deleteEntity(key: $key) {
				success
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_delete_entity))
			console.log('deleting character: ' + entity.value.key)
			mutate({
				"key": entity.value.key
			  })
		}
	}

	/**
	 * sets the location of this entity in the database
	 * @param location the location to set the entity to
	 */
	function set_location(location: Location) {
		// entity.value.location = location
		update_entity({ location: location.id })
		retrieve_entity()
	}

	function create_relation(entity_id: string) {
		/* create a relation between this character and an entity */
		const query_create_relation = gql`mutation CreateRelation($fromId: ID!, $toId: ID!, $type: String) {
				createRelation(fromId: $fromId, toId: $toId, type: $type) {
					success
				}
			}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_create_relation))
			console.log('creating relation between: ' + entity.value.id + ' and ' + entity_id)
			mutate({
				"fromId": entity_id,
				"toId": entity.value.id,
				"type": "relation"
			})
		}
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
		retrieve_entity,
		retrieve_small_entity,
		retrieve_relations,
		retrieve_followers,
		retrieve_instances,
		update_entity,
		activate_entity,
		deactivate_entity,
		clone_entity,
		delete_entity,
		set_location,
		create_relation,
		entity_type_icon
	}
}