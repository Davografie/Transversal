/*
	all logic for characters
*/
import { ref, onMounted, inject, watch } from 'vue'
import type { Ref } from 'vue'
import { useFetch } from '@vueuse/core'
import { provideApolloClient, useMutation, useQuery } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import type { ApolloClient } from '@apollo/client'
import type { Character, Entity, Location } from '@/interfaces/Types'
import { placeholder_location } from './Location'
import { placeholder_traitset } from './Traitset'

export const placeholder_character: Character = {
	id: 'placeholder',
	key: 'placeholder',
	name: 'loading',
	entityType: 'character',
	available: true,
	pp: 0,
	traitsets: [
		placeholder_traitset
	],
	location: placeholder_location
}

export function useCharacter(init?: Character, character_key?: string) {

	const apolloClient: ApolloClient<any>|undefined = inject('apolloClient')
	const API_URL: string|undefined = inject('API_URL')

	const character: Ref<Character> = ref(init ?? placeholder_character)

	function set_character_key(key: string) {
		character_key = key
		retrieve_character()
	}

	function retrieve_character() {
		/* returns the character with the given key */
		if(apolloClient) {
			let charkey = undefined
			if(init) {
				charkey = init.key
			}
			else if(character_key) {
				charkey = character_key
			}
			else {
				throw("no character key provided")
			}
			const query_get_character = gql`query FullCharacter{
				characters(key: "${charkey}") {
					id
					key
					name
					description
					image {
						path
						ext
					}
					imagened
					entityType
					location {
						id
						key
						name
						image {
							path
							ext
						}
					}
					following {
						id
					}
					available
					hidden
					pp
					traitsets {
						id
						entityTypes
						limit
					}
					relations {
						id
						toEntity {
							id
							key
							entityType
						}
					}
					isArchetype
					archetype {
						id
						key
						name
						image {
							path
							ext
						}
					}
				}
			}`
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{characters: Entity[]}>(
					query_get_character,
					null,
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				console.log('retrieved character: ')
				console.log(newResult)
				if(newResult?.characters && newResult.characters.length > 0) {
					character.value = newResult.characters[0]
				}
			})
		}
	}

	function retrieve_relations() {

		const relations_query = gql`query CharacterRelations($characterKey: ID) {
			characters(key: $characterKey) {
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

		if(apolloClient && character_key) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					relations_query,
					{ characterKey: character_key },
					{ fetchPolicy: 'no-cache' }
				)
			)
			watch(result, () => {
				if(result.value.characters?.length > 0) {
					character.value = {
						...character.value,
						...result.value.characters[0]
					}
				}
			})
		}
	}

	onMounted(() => {
		if(character_key && character_key != 'placeholder') {
			retrieve_character()
		}
		else {
			console.warn("missing character initialization parameter")
		}
	})

	function update_character(input: object) {
		/* post character changes to the server */
		console.log('updating character: ' + character.value.key + ' with the following input:')
		console.log(input)
		const query_update_character = gql`mutation Mutation($input: CharacterInput!, $key: ID) {
			createOrUpdateCharacter(input: $input, key: $key) {
				character {
					name
				}
			}
		}`
		if(apolloClient && (character_key ?? character.value.key) != 'placeholder') {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{characters: Character[]}>(query_update_character))
			mutate({
				input: input,
				key: character_key ?? character.value.key
			})
		}
	}

	function clone_entity() {
		/* post character changes to the server */
		console.log('cloning character: ' + character.value.key)
		const query_clone_entity = gql`mutation CloneEntity($key: ID!) {
			cloneEntity(key: $key) {
				entity {
					id
					entityType
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_clone_entity))
			console.log('cloning character: ' + character.value.key)
			mutate({
				"key": character.value.key
			})
		}
	}
	
	function delete_entity() {
		/* post character changes to the server */
		console.log('deleting character: ' + character.value.key)
		const query_delete_entity = gql`mutation DeleteEntity($key: ID!) {
			deleteEntity(key: $key) {
				success
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{entities: Entity[]}>(query_delete_entity))
			console.log('deleting character: ' + character.value.key)
			mutate({
				"key": character.value.key
				})
		}
	}

	function toggle_archetype() {
		update_character({ isArchetype: !character.value.isArchetype })
		retrieve_character()
	}

	function set_location(location: Location) {
		// character.value.location = location
		update_character({ location: location.id })
		retrieve_character()
	}

	function mutate_pp(delta: number) {
		character.value = { ...character.value, pp: (character.value.pp ?? 0) + delta }
		update_character({ pp: character.value.pp })
	}

	function create_relation(entity_id: string) {
		/* create a relation between this character and an entity */
		const query_create_relation = gql`mutation CreateRelation($fromId: ID!, $toId: ID!, $type: String) {
				createRelation(fromId: $fromId, toId: $toId, type: $type) {
					success
				}
			}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{characters: Character[]}>(query_create_relation))
			console.log('creating relation between: ' + character.value.id + ' and ' + entity_id)
			mutate({
				"fromId": entity_id,
				"toId": character.value.id,
				"type": "relation"
			})
		}
	}

	function activate_character(player_id: string) {
		const url = API_URL + "pick-character/" + player_id + "/" + character_key
		interface API_result {
			success: boolean
		}
		const { data } = useFetch<API_result>(url).post().json()
		watch(data, (newData) => {
			console.log("picking character, API success: " + newData.success)
			if(newData && newData.success) {
				character.value = {
					...character.value,
					available: false
				}
			}
		})
	}

	function deactivate_character() {
		const url = API_URL + "deactivate-character/" + character.value.key
		interface API_result {
			success: boolean
		}
		const { data } = useFetch<API_result>(url).post().json()
		watch(data, (newData) => {
			if(newData && newData.success) {
				console.log("unpicking character, API success: " + newData.success)
				character.value = {
					...character.value,
					available: true
				}
			}
		})
	}

	return {
		character,
		set_character_key,
		retrieve_character,
		retrieve_relations,
		activate_character,
		deactivate_character,
		set_location,
		mutate_pp,
		create_relation,
		update_character,
		clone_entity,
		delete_entity,
		toggle_archetype
	}
}
