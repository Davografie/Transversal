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
import { useEntity } from '@/composables/Entity'


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
	const location_id: Ref<string|undefined> = ref('Entities/' + location_key)
	const { entity, imagen } = useEntity()

	function set_location_key(key: string) {
		location_key = key
		if(location_key.startsWith('Entities/')) {
			location_id.value = location_key
		} else {
			location_id.value = 'Entities/' + location_key
		}
		retrieve_small_location()
	}

	function retrieve_location() {
		// console.log('retrieving location: ' + location_key)
		if(location_key && location_key != 'placeholder') {
			const get_location_query = gql`query FullLocation($locationId: ID) {
				locations(locationId: $locationId) {
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
						isArchetype
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
				apolloClient.query({
					query: get_location_query,
					variables: { locationId: location_id.value ?? 'Entities/' + location_key },
					fetchPolicy: 'cache-first'
				}).then((result) => {
					location.value = {
						...location.value,
						...result.data.locations[0]
					}
				}).catch((error) => {
					console.error(error)
				})
			}
		}
	}

	function retrieve_parents() {
		const get_location_query = gql`query LocationParents($locationId: ID) {
			locations(locationId: $locationId) {
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
			apolloClient.query({
				query: get_location_query,
				variables: { locationId: location_id.value ?? 'Entities/' + location_key },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				location.value = {
					...location.value,
					parent: result.data.locations[0].parent,
					parents: result.data.locations[0].parents
				}
			}).catch((error) => {
				console.error(error)
			})
		}
	}

	function retrieve_transversables() {
		const get_location_query = gql`query LocationTransversables($locationId: ID) {
			locations(locationId: $locationId) {
				transversables {
					key
					id
					name
				}
			}
		  }`
		if(apolloClient && location_key && location_key != 'placeholder') {
			apolloClient.query({
				query: get_location_query,
				variables: { locationId: location_id.value ?? 'Entities/' + location_key },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				location.value = {
					...location.value,
					...result.data.locations[0]
				}
			}).catch((error) => {
				console.error(error)
			})
		}
	}

	function retrieve_zones() {
		const get_location_query = gql`query LocationZones($locationId: ID) {
			locations(locationId: $locationId) {
				zones {
					key
					id
					name
				}
			}
		  }`
		if(apolloClient && location_key && location_key != 'placeholder') {
			apolloClient.query({
				query: get_location_query,
				variables: { locationId: location_id.value ?? 'Entities/' + location_key },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				location.value = {
					...location.value,
					...result.data.locations[0]
				}
			}).catch((error) => {
				console.error(error)
			})
		}
	}

	function retrieve_small_location() {
		const get_location_query = gql`query SmallLocation($locationId: ID) {
			locations(locationId: $locationId) {
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
			if(!location_key || location_key == 'undefined' || location_key == 'placeholder') {
				console.warn('retrieve_small_location, location_key: ' + location_key)
				return
			}
			apolloClient.query({
				query: get_location_query,
				variables: { locationId: location_id.value ?? 'Entities/' + location_key },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				location.value = {
					...location.value,
					...result.data.locations[0]
				}
			}).catch((error) => {
				console.error("Error while trying to retrieve location " + location_key, error)
			})
		}
	}

	function retrieve_presence() {
		const get_location_query = gql`query Presence($locationId: ID) {
			locations(locationId: $locationId) {
				entities {
					key
					id
					name
					entityType
					isArchetype
					hidden
					active
					knownTo {
						id
					}
				}
			}
		}`
		if(apolloClient) {
			apolloClient.query({
				query: get_location_query,
				variables: { locationId: 'Entities/' + location_key },
				fetchPolicy: 'network-only'
			}).then((result) => {
				location.value = {
					...location.value,
					...result.data.locations[0]
				}
			}).catch((error) => {
				console.error(error)
			})
		}
	}

	function retrieve_neighboring_presence() {
		const get_location_query = gql`query NeighboringPresence($locationId: ID) {
				locations(locationId: $locationId) {
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
			apolloClient.query({
				query: get_location_query,
				variables: { locationId: location_id.value ?? 'Entities/' + location_key },
				fetchPolicy: 'cache-first'
			}).then((result) => {
				location.value = {
					...location.value,
					...result.data.locations[0]
				}
			}).catch((error) => {
				console.error(error)
			})
		}
	}

	function update_location(input: {
		name?: string,
		description?: string,
	}) {
		/* changes to name, flavortext */
		const update_location_query = gql`mutation UpdateLocation($locationId: ID!, $locationInput: LocationInput) {
				updateLocation(locationId: $locationId, locationInput: $locationInput) {
					location {
						id
						name
						description
					}
				}
			}`
		if(apolloClient) {
			apolloClient.mutate({
				mutation: update_location_query,
				variables: {
					"locationId": location.value.id,
					"locationInput": input
				}
			}).then((result) => {
				if(!result?.data.updateLocation.location) return
				location.value = {
					...location.value,
					...result.data.updateLocation.location
				}
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

	async function create_zone(name: string) {
		const create_zone_query = gql`mutation CreateZone($locationInput: LocationInput!) {
			createLocation(locationInput: $locationInput) {
				location {
					id
					key
					name
				}
			}
		}`
		if(apolloClient) {
			apolloClient.mutate({
				mutation: create_zone_query,
				variables: {
					"locationInput": {
						name: name,
						location: location.value.id
					}
				}
			}).then((result) => {
				location.value = {
					...location.value,
					zones: [
						...(location.value.zones ?? []),
						result.data.createLocation.location
					]
				}
			})
		}
	}

	function import_entity(entity_id: string) {
		/* change an entity's location */
		const query_import_entity = gql`mutation ImportEntity($entityId: ID!, $locationId: ID!) {
			updateEntity(location: $locationId, entityId: $entityId) {
				entity {
					id
				}
			}
		}`
		if(apolloClient) {
			apolloClient.mutate({
				mutation: query_import_entity,
				variables: {
					"entityId": entity_id,
					"locationId": location.value.id
				}
			}).then(() => {
				retrieve_presence()
			})
		}
	}

	async function add_location_relationship(entity_id: string) {
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
					"fromId": entity_id,
					"toId": location.value.id,
					"type": "relation"
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(() => useMutation<{characters: Character[]}>(query_create_relation))
			// console.log('creating relation between: ' + location.value.id + ' and ' + entity_id)
			// mutate({
			// 	"fromId": entity_id,
			// 	"toId": location.value.id,
			// 	"type": "relation"
			// })
		}
	}

	async function make_transversable(from_entity_id: string) {
		const query = gql`mutation CreateRelation($fromId: ID!, $toId: ID!, $type: String) {
			createRelation(fromId: $fromId, toId: $toId, type: $type) {
				success
			}
		}`

		if(apolloClient) {
			await apolloClient.mutate({
				mutation: query,
				variables: {
					"fromId": from_entity_id,
					"toId": location.value.id,
					"type": "transversable"
				}
			})
		}
	}

	async function set_location_visibility(hide?: boolean) {
		console.log('set_location_visibility: ' + (hide ?? !location.value.hidden))
		const query = gql`mutation HideLocation($entityId: ID!, $entityInput: EntityInput) {
			updateEntity(entityId: $entityId, entityInput: $entityInput) {
				entity {
					id
					hidden
				}
			}
		}`
		if(apolloClient) {
			apolloClient.mutate({
				mutation: query,
				variables: {
					"entityId": location.value.id,
					"entityInput": {
						"hidden": hide ?? !location.value.hidden
					}
				}
			}).then((result) => {
				location.value = {
					...location.value,
					...result.data.updateEntity.entity
				}
			})
		}
	}

	watch(location, (newLocation) => {
		if(newLocation) {
			entity.value = newLocation
		}
	})

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
		set_location_visibility,
		imagen
	}
}
