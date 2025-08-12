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
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(query_get_potential_entity_traits_for_traitset, args, { fetchPolicy: 'no-cache' })
			)
			watch(result, () => {
				const { convert_rating_to_dice } = useRating()
				let new_traits: Trait[] = []
				for(let i = 0; i < result.value.traits.length; i++) {
					const trait = result.value.traits[i]
					trait.defaultTraitSetting.rating = convert_rating_to_dice(trait.defaultTraitSetting.rating ?? [])
					new_traits.push(trait)
				}
				traits.value = new_traits
			})
		}
	}

	return { traits, retrieve_traits, retrieve_potential_traits }
}
