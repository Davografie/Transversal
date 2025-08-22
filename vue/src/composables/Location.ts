/*
	all logic for a location
*/
import _ from 'lodash'
import { ref, inject, watch } from 'vue'
import type { Ref } from 'vue'
import { provideApolloClient, useMutation, useQuery } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import type { ApolloClient } from '@apollo/client'
import type { Character, Location } from "@/interfaces/Types"


export const placeholder_location: Location = {
	id: 'placeholder',
	key: 'placeholder',
	name: 'placeholder',
	entityType: 'location'
}

export function useLocation(init?: Location, location_key?: string) {
	const apolloClient: ApolloClient<any>|undefined = inject('apolloClient')

	const location: Ref<Location> = ref(placeholder_location)
	const characters: Ref<Character[]> = ref([])    // the characters active at this location
	const transversable: Ref<Location[]> = ref([])  // the locations accessible from this location, only available for current location

	function set_location_key(key: string) {
		location_key = key
		retrieve_small_location()
	}

	function retrieve_location() {
		// console.log('retrieving location: ' + location_key)
		if(location_key && location_key != 'placeholder') {
			const get_location_query = gql`query FullLocation($locationKey: ID) {
				locations(key: $locationKey) {
					id
					key
					parent {
						key
						id
						name
						image {
							path
							ext
						}
					}
					parents {
						key
						id
						name
					}
					name
					image {
						path
						ext
						width
						height
					}
					flavortext
					hidden
					entities {
						id
						key
						name
						hidden
						entityType
						active
						... on Character {
							available
						}
						knownTo {
							id
						}
					}
					zones {
						id
						key
						name
						image {
							path
							ext
						}
						hidden
						knownTo {
							id
						}
					}
					transversables {
						id
						key
					}
					traitsets {
						id
						entityTypes
						limit
					}
				}
			  }`
			// console.log(get_location_query)
			if(apolloClient) {
				const { result } = provideApolloClient(apolloClient)(
					() => useQuery<{locations: Location[]}>(
						get_location_query,
						{ locationKey: location_key },
						{ fetchPolicy: 'cache-and-network' }
					)
				)
				watch(result, (newResult) => {
					if(newResult) {
						// console.log('retrieved location: ')
						// console.log(newResult)
						location.value = {
							...location.value,
							...newResult.locations[0]
						}
					}
				})
			}
		}
	}

	function retrieve_parents() {
		const get_location_query = gql`query LocationParents($locationKey: ID) {
			locations(key: $locationKey) {
				parent {
					key
					id
					name
				}
				parents {
					key
					id
					name
				}
			}
		  }`
		if(apolloClient && location_key && location_key != 'placeholder') {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{locations: Location[]}>(
					get_location_query,
					{ locationKey: location_key },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					location.value = {
						...location.value,
						parent: newResult.locations[0].parent,
						parents: newResult.locations[0].parents
					}
				}
			})
		}
	}

	function retrieve_transversables() {
		const get_location_query = gql`query LocationTransversables($locationKey: ID) {
			locations(key: $locationKey) {
				transversables {
					key
					id
					name
				}
			}
		  }`
		if(apolloClient && location_key && location_key != 'placeholder') {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{locations: Location[]}>(
					get_location_query,
					{ locationKey: location_key },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					location.value = {
						...location.value,
						...newResult.locations[0]
					}
				}
			}, { once: true })
		}
	}

	function retrieve_zones() {
		const get_location_query = gql`query LocationZones($locationKey: ID) {
			locations(key: $locationKey) {
				zones {
					key
					id
					name
				}
			}
		  }`
		if(apolloClient && location_key && location_key != 'placeholder') {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{locations: Location[]}>(
					get_location_query,
					{ locationKey: location_key },
					// { fetchPolicy: 'no-cache' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					location.value = {
						...location.value,
						...newResult.locations[0]
					}
				}
			}, { once: true })
		}
	}

	function retrieve_small_location() {
		const get_location_query = gql`query SmallLocation($locationKey: ID) {
			locations(key: $locationKey) {
				id
				key
				name
				flavortext
				image {
					path
					ext
					width
					height
				}
				hidden
			}
		  }`
		if(apolloClient) {
			if(location_key == 'placeholder') {
				console.warn('retrieve_small_location: location key is placeholder')
				return
			}
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{locations: Location[]}>(
					get_location_query,
					{ locationKey: location_key },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					// console.log('retrieved location: ')
					// console.log(newResult)
					// location.value = newResult.locations[0]
					location.value = {
						...location.value,
						...newResult.locations[0]
					}
				}
			},
			{ once: true })
		}
	}

	function retrieve_presence() {
		const get_location_query = gql`query Presence($locationKey: ID) {
			locations(key: $locationKey) {
				entities {
					key
					id
					name
					entityType
					isArchetype
					... on Character {
						available
					}
					hidden
					knownTo {
						id
					}
					active
				}
			}
		}`
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{locations: Location[]}>(
					get_location_query,
					{ locationKey: location_key },
					{ fetchPolicy: 'no-cache' }
				)
			)
			watch(result, (newResult) => {
				if(newResult && newResult.locations[0].entities) {
					location.value = { ...location.value, ...newResult.locations[0]}
				}
			}, { once: true })
		}
	}

	function retrieve_neighboring_presence() {
		const get_location_query = gql`query NeighboringPresence($locationKey: ID) {
				locations(key: $locationKey) {
					name
					zones {
						id
						key
						name
						entities {
							id
							name
						}
					}
					transversables {
						id
						key
						name
						entities {
							id
							name
						}
					}
					parents {
						id
						key
						name
						entities {
							id
							name
						}
					}
				}
			}`
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{locations: Location[]}>(
					get_location_query,
					{ locationKey: location_key },
					{ fetchPolicy: 'cache-and-network' }
				)
			)
			watch(result, (newResult) => {
				if(newResult) {
					location.value = { 
						...location.value,
						...newResult.locations[0]
					}
				}
			})
		}
	}

	// onMounted(() => {
	// 	if(!init && location_key && location_key != 'placeholder') {
	// 		retrieve_location()
	// 	}
	// })
	
	// function retrieve_potential_traits() {}
	// function add_trait() {}
	function update_location(input: {
		name?: string,
		description?: string,
	}) {
		/* changes to name, flavortext */
		const update_location_query = gql`mutation UpdateLocation($key: ID!, $locationInput: LocationInput) {
				updateLocation(key: $key, locationInput: $locationInput) {
					location {
						id
					}
				}
			}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(
				() => useMutation(update_location_query)
			)
			mutate({
				key: location.value.id,
				locationInput: input
			})
		}
	}

	function retrieve_potential_locales() {
		/* only retrieve locations not a descendant of the current location */
	}

	function change_locale() {}
	function retrieve_potential_zones() {
		/* only retrieve locations without locale
		and not an ancestor of the current location */
	}
	function remove_zone() {}

	function create_zone(name: string) {
		const create_zone_query = gql`mutation CreateZone($locationInput: LocationInput!) {
			createLocation(locationInput: $locationInput) {
				location {
					id
					key
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(
				() => useMutation(create_zone_query)
			)
			mutate({
				locationInput: {
					name: name,
					location: location.value.id
				}
			})
		}
	}

	function import_entity(entity_id: string) {
		/* change an entity's location */
		const query_import_entity = gql`mutation ImportEntity($entityId: ID!, $locationId: ID!) {
			updateEntity(location: $locationId, key: $entityId) {
				entity {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query_import_entity))
			mutate({
				"entityId": entity_id,
				"locationId": location.value.id
			})
		}
	}

	function add_location_relationship(entity_id: string) {
		/* create a relation between this character and an entity */
		const query_create_relation = gql`mutation CreateRelation($fromId: ID!, $toId: ID!, $type: String) {
				createRelation(fromId: $fromId, toId: $toId, type: $type) {
					success
				}
			}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{characters: Character[]}>(query_create_relation))
			console.log('creating relation between: ' + location.value.id + ' and ' + entity_id)
			mutate({
				"fromId": entity_id,
				"toId": location.value.id,
				"type": "relation"
			})
		}
	}

	function make_transversable(from_entity_id: string) {
		const query = gql`mutation CreateRelation($fromId: ID!, $toId: ID!, $type: String) {
			createRelation(fromId: $fromId, toId: $toId, type: $type) {
				success
			}
		}`

		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			mutate({
				"fromId": from_entity_id,
				"toId": location.value.id,
				"type": "transversable"
			})
		}
	}

	function set_location_visibility(hide?: boolean) {
		console.log('set_location_visibility: ' + (hide ?? !location.value.hidden))
		const query = gql`mutation HideLocation($key: ID!, $entityInput: EntityInput) {
			updateEntity(key: $key, entityInput: $entityInput) {
				entity {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			mutate({
				"key": location.value.key,
				"entityInput": {
					"hidden": hide ?? !location.value.hidden ?? false
				}
			})
		}
	}

	return {
		location,
		characters,
		transversable,
		set_location_key,
		retrieve_location,
		retrieve_parents,
		retrieve_transversables,
		retrieve_zones,
		retrieve_small_location,
		retrieve_presence,
		retrieve_neighboring_presence,
		create_zone,
		add_location_relationship,
		update_location,
		import_entity,
		make_transversable,
		set_location_visibility
	}
}
