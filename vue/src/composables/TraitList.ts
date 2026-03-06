/*
	Trait list
*/
import { ref, inject, watch } from "vue"
import type { Ref } from "vue"
import type { ApolloClient } from '@apollo/client/core'
import { useQuery, provideApolloClient } from "@vue/apollo-composable"
import gql from 'graphql-tag'

import { useRating } from "@/composables/Rating"
import type { Trait } from "@/interfaces/Types"

import { placeholder_trait } from "@/composables/Trait"

export function useTraitList(init?: Trait[], traitset_id?: string, entity_id?: string, potential_only?: boolean) {
	/*
		selection filter is one of following:
			character + traitset: all traits of a character's traitset
			location: all traits of location
			traitset: all traits of traitset
	*/
	const traits: Ref<Trait[]> = ref([placeholder_trait])
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')

	function retrieve_traits() {
		const query_get_traitset_traits = gql`query TraitsetTraits($traitsetId: ID) {
			traits(traitsetId: $traitsetId) {
				id
				name
				explanation
				defaultTraitSetting {
					rating
				}
			}
		}`


		const query = query_get_traitset_traits
		const args = { "traitsetId": traitset_id }

		if(apolloClient) {
			apolloClient.query({
				query: query,
				variables: args,
				fetchPolicy: 'no-cache'
			}).then((result) => {
				traits.value = result.data.traits
			})
		}
	}

	function set_traitset_id(_id: string) {
		traitset_id = _id
	}

	function set_entity_id(_id: string) {
		entity_id = _id
	}

	function retrieve_entity_traits() {
		if(apolloClient) {
			const query_get_entity_traits = gql`
				query EntityTraits($entityId: ID) {
					entities(entityId: $entityId) {
						traits {
							id
							name
							explanation
							traitSetting {
								id
							}
						}
					}
				}`

			const args = { "entityId": entity_id }
			console.log("retrieving entity traits for entity_id: " + entity_id + " with args: " + JSON.stringify(args))

			apolloClient.query({
				query: query_get_entity_traits,
				variables: args,
				fetchPolicy: 'no-cache'
			}).then((result) => {
				traits.value = result.data.entities[0].traits
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(query_get_entity_traits, args, { fetchPolicy: 'no-cache' })
			// )
			// watch(result, () => {
			// 	console.log("entity traits result: " + JSON.stringify(result.value.entities[0].traits))
			// 	traits.value = result.value.entities[0].traits
			// })
		}
	}

	function retrieve_potential_traits() {
		if(apolloClient) {
			const query_get_potential_entity_traits_for_traitset = gql`
			query PotentialTraits($traitsetId: ID, $potentialOnly: Boolean, $entityId: ID) {
				traits(traitsetId: $traitsetId, potentialOnly: $potentialOnly, entityId: $entityId) {
					id
					name
					explanation
					defaultTraitSetting {
						rating
					}
					locationRestricted
				}
			}`
			console.log("retrieving potential traits for traitset: " + traitset_id + ", entity_id: " + entity_id)
			const args = {
				"traitsetId": traitset_id,
				"potentialOnly": potential_only,
				"entityId": entity_id
			}

			apolloClient.query({
				query: query_get_potential_entity_traits_for_traitset,
				variables: args,
				fetchPolicy: 'no-cache'
			}).then((result) => {
				const { convert_rating_to_dice } = useRating()
				let new_traits: Trait[] = []
				for(let i = 0; i < result.data.traits.length; i++) {
					const trait = result.data.traits[i]
					trait.defaultTraitSetting.rating = convert_rating_to_dice(trait.defaultTraitSetting.rating ?? [])
					new_traits.push(trait)
				}
				traits.value = new_traits
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(query_get_potential_entity_traits_for_traitset, args, { fetchPolicy: 'no-cache' })
			// )
			// watch(result, () => {
			// 	const { convert_rating_to_dice } = useRating()
			// 	let new_traits: Trait[] = []
			// 	for(let i = 0; i < result.value.traits.length; i++) {
			// 		const trait = result.value.traits[i]
			// 		trait.defaultTraitSetting.rating = convert_rating_to_dice(trait.defaultTraitSetting.rating ?? [])
			// 		new_traits.push(trait)
			// 	}
			// 	traits.value = new_traits
			// })
		}
	}

	return {
		traits,
		set_traitset_id,
		retrieve_traits,
		retrieve_entity_traits,
		retrieve_potential_traits,
		set_entity_id
	}
}
