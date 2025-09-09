/*
	generate a entity list to use on the entity overview page
*/

import { ref, watch, inject } from 'vue'
import type { Ref } from 'vue'
import type { Entity } from '@/interfaces/Types'
import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
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
		const variables = { "entityType": entityType }
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{entities: Entity[]}>(
					get_entities_query,
					variables,
					{ fetchPolicy: 'no-cache' }
				)
			)
			// const { result } = useQuery(get_entities_query, null, { fetchPolicy: 'cache-and-network' })
			watch(result, (newResult) => {
				if(newResult) {
					entities.value = newResult.entities
				}
			}, { immediate: true })
		}
	}

	function retrieve_archetypes(entity_type?: string) {
		const get_archetypes_query = gql`query Archetypes($entityType: String, $isArchetype: Boolean) {
			entities(entityType: $entityType, isArchetype: $isArchetype) {
				key
				id
				name
				entityType
			}
		}`
		const variables = { "entityType": entity_type, "isArchetype": true }
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{entities: Entity[]}>(
					get_archetypes_query,
					variables,
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					entities.value = newResult.entities
				}
			}, { immediate: true })
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
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{entities: Entity[]}>(
					search_entities_query,
					{ search: query },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					entities.value = newResult.entities
				}
			}, { immediate: true })
		}
	}

	function retrieve_characters(available?: boolean) {
		const query = gql`query Characters($available: Boolean) {
			characters(available: $available) {
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
			const args = { "available": available ?? false }
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{characters: Entity[]}>(
					query,
					args,
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					entities.value = newResult.characters
				}
			}, { immediate: true })
		}
	}

	async function create_entity(name: string, entity_type: string, location_id?: string) {
		const create_entity_query = gql`mutation CreateEntity($entityType: String!, $name: String!, $location: ID) {
			createEntity(entityType: $entityType, name: $name, location: $location) {
				entity {
					id
					key
					name
					entityType
				}
			}
		}`
		if(apolloClient) {
			const { mutate: create } = provideApolloClient(apolloClient)(() => useMutation(create_entity_query))
			let input: any = { "name": name, "entityType": entity_type }
			if(location_id) { input = { ...input, "location": location_id } }
			// create(input)
			try {
				const result = await create(input);
				return result?.data?.createEntity?.entity; // Extract and return the entity data
			} catch (error) {
				console.error('Error creating entity:', error);
				throw error; // Re-throw the error if needed
			}
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
