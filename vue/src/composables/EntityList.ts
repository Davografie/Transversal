/*
	generate a entity list to use on the entity overview page
*/

import { ref, inject } from 'vue'
import type { Ref } from 'vue'
import type { Entity } from '@/interfaces/Types'
import { useMutation, provideApolloClient } from "@vue/apollo-composable"
import type { ApolloClient } from '@apollo/client/core'
import gql from 'graphql-tag'

export function useEntityList(init?: Entity[], entity_type?: string) {
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
	const entities: Ref<Entity[]> = ref(init ?? [])
	const entityType = ref<string|null>(entity_type ?? null)

	function retrieve_entities() {
		const get_entities_query = gql`query EntityList($entityType: String) {
			entities(entityType: $entityType) {
				key
				id
				name
				entityType
				image {
					path
					ext
				}
				favorite
				active
				isArchetype
			}
		}`
		const variables = { "entityType": entityType.value }
		if(apolloClient) {
			console.log('retrieving entities: ', variables)
			apolloClient.query({
				query: get_entities_query,
				variables,
				fetchPolicy: 'network-only'
			}).then((result) => {
				console.log('retrieved entities: ', result.data.entities)
				entities.value = result.data.entities
			})
		}
	}

	function retrieve_archetypes(entity_type?: string, location_id?: string) {
		const get_archetypes_query = gql`query Archetypes($entityType: String, $locationId: ID, $isArchetype: Boolean) {
			entities(entityType: $entityType, locationId: $locationId, isArchetype: $isArchetype) {
				key
				id
				name
				entityType
			}
		}`
		if(entity_type == 'npc') {
			// when NPC, also pick up character archetypes
			entity_type = ""
		}
		const variables = {
			"entityType": entity_type,
			"locationId": location_id,
			"isArchetype": true
		}
		if(apolloClient) {
			apolloClient.query({
				query: get_archetypes_query,
				variables,
				fetchPolicy: 'cache-first'
			}).then((result) => {
				if(entity_type != '' && entity_type != 'npc') {
					entities.value = result.data.entities
				}
				else {
					entities.value = result.data.entities.filter((e: Entity) => ['character', 'npc'].includes(e.entityType))
				}
			})
		}
	}

	function search_entities(query: string) {
		const search_entities_query = gql`query SearchEntities($search: String) {
			entities(search: $search) {
				key
				id
				name
				entityType
				image {
					path
					ext
				}
				favorite
				active
				isArchetype
			}
		}`
		if(apolloClient) {
			apolloClient.query({
				query: search_entities_query,
				variables: { search: query },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				entities.value = result.data.entities
			})
		}
	}

	function retrieve_characters(available?: boolean) {
		const query = gql`query Characters($available: Boolean) {
			characters(available: $available) {
				key
				id
				name
				entityType
				favorite
				active
				isArchetype
			}
		}`
		const args = { "available": available ?? false }
		if(apolloClient) {
			apolloClient.query({
				query: query,
				variables: args,
				fetchPolicy: 'network-only'
			}).then((result) => {
				entities.value = result.data.characters
			})
		}
	}

	/**
	 * create a new entity
	 * @param name the new entity's name
	 * @param entity_type the type of the new entity
	 * @param location_id where to spawn the new entity
	 * @returns the created entity
	 */
	async function create_entity(name: string, entity_type: string, location_id?: string, is_archetype?: boolean) {
		const create_entity_query = gql`mutation CreateEntity($entityType: String!, $name: String!, $location: ID, $isArchetype: Boolean) {
			createEntity(entityType: $entityType, name: $name, location: $location, isArchetype: $isArchetype) {
				entity {
					id
					key
					name
					entityType
				}
			}
		}`
		if(apolloClient) {
			console.log('creating entity: ', name, entity_type, location_id, is_archetype)
			const new_entity = await apolloClient.mutate({
				mutation: create_entity_query,
				variables: {
					"entityType": entity_type,
					"name": name,
					"location": location_id,
					"isArchetype": is_archetype
				}
			})
			return new_entity.data.createEntity.entity
			// const { mutate: create } = provideApolloClient(apolloClient)(() => useMutation(create_entity_query))
			// let input: any = { "name": name, "entityType": entity_type }
			// if(location_id) { input = { ...input, "location": location_id } }
			// // create(input)
			// try {
			// 	const result = await create(input);
			// 	return result?.data?.createEntity?.entity; // Extract and return the entity data
			// } catch (error) {
			// 	console.error('Error creating entity:', error);
			// 	throw error; // Re-throw the error if needed
			// }
		}
	}

	return {
		entities,
		retrieve_entities,
		retrieve_archetypes,
		search_entities,
		retrieve_characters,
		create_entity,
		entityType
	}
}
