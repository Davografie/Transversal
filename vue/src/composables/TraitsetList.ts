/*
	traitset list logic
*/
import { ref, inject, watch } from 'vue'
import type { Ref } from 'vue'
import type { ApolloClient } from '@apollo/client/core'
import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
import gql from 'graphql-tag'
import type { Traitset } from '@/interfaces/Types'
import { placeholder_trait } from '@/composables/Trait'

export const placeholder_traitset: Traitset = {
	id: "placeholder",
	name: "placeholder",
	traits: [
		placeholder_trait
	]
}

export function useTraitsetList(init?: Traitset[], entity_id?: string, entity_type?: string) {
	const traitsets: Ref<Traitset[]> = ref(init ? init : [placeholder_traitset])
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')

	function retrieve_traitsets() {
		const query_get_entity_traitsets = gql`query Traitsets($entityId: ID) {
			traitsets(entityId: $entityId) {
				key
				id
				name
			}
		}`
		const query_get_entity_type_traitsets = gql`query Traitsets($entityType: String) {
			traitsets(entityType: $entityType) {
				key
				id
				name
			}
		}`
		const query_get_all_traitsets = gql`query Traitsets {
			traitsets {
				key
				id
				name
				entityTypes
			}
		}`
		let query = query_get_all_traitsets
		if(entity_id) { query = query_get_entity_traitsets }
		if(entity_type) { query = query_get_entity_type_traitsets }
		// const query = entity_id ? query_get_entity_traitsets : query_get_all_traitsets
		let parameters = {}
		if(entity_id) { parameters = { entityId: entity_id } }
		if(entity_type) { parameters = { entityType: entity_type } }
		// const parameters = entity_id ? { traitsetId: entity_id } : {}
		// const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
		if(apolloClient) {
			const { result, refetch } = provideApolloClient(apolloClient)(
				() => useQuery<{traitsets: Traitset[]}>(query,
					parameters, { fetchPolicy: 'cache-and-network' })
			)
			watch(result, (newResult) => {
				if(newResult) {
					traitsets.value = newResult.traitsets
				}
			})
			refetch()
		}
	}

	async function create_traitset(name: string, entity_types: string[]) {
		const mutate_create_traitset = gql`mutation CreateTraitset($name: String!, $entityTypes: [String]) {
			createTraitset(name: $name, entityTypes: $entityTypes) {
				traitset {
					id
					name
				}
			}
		}`
		if(apolloClient) {
			const { mutate, onDone, onError } = provideApolloClient(apolloClient)(() => useMutation(mutate_create_traitset))
			let variables: object = {
				name: name,
				entityTypes: entity_types
			}
			// console.log("updating traitset with variables: ", variables)
			mutate(variables)
			retrieve_traitsets()
		}
	}

	function change_traitset_order(traitset_ids: string[]) {
		const mutate_change_traitset_order = gql`mutation ChangeTraitsetOrder($traitsetId: ID!, $traitsetInput: TraitsetInput!) {
				mutateTraitset(traitsetId: $traitsetId, traitsetInput: $traitsetInput) {
					traitset {
						id
					}
				}
			}`
		if(apolloClient) {
			const { mutate, onDone, onError } = provideApolloClient(apolloClient)(() => useMutation(mutate_change_traitset_order))
			for (let index = 0; index < traitset_ids.length; index++) {
				let variables: object = {
					traitsetId: traitset_ids[index],
					traitsetInput: { order: index }
				}
				// console.log("updating traitset with variables: ", variables)
				mutate(variables)
			}
		}
	}

	return {
		traitsets,
		retrieve_traitsets,
		create_traitset,
		change_traitset_order
	}
}
