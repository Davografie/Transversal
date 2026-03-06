/*
	SFX logic
	example SFX: SFXs/333969
*/
import { ref, onMounted, watch, inject } from 'vue'
import type { Ref } from 'vue'
import { provideApolloClient, useQuery, useMutation } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import type { ApolloClient } from '@apollo/client'
import type { SFX, SFXInput } from '@/interfaces/Types'

export const placeholder_sfx: SFX = {
	id: "placeholder",
	name: "loading",
	description: "placeholder",
	effects: []
}

export function useSFX(init?: SFX, sfx_id?: string) {
	const apolloClient: ApolloClient<any>|undefined = inject('apolloClient')
	const sfx: Ref<SFX> = ref(placeholder_sfx)

	function retrieve_sfx() {
		// console.log('retrieving sfx: ' + sfx_id)
		if(sfx_id) {
			const get_sfx_query = gql`query Sfxs($sfxId: ID) {
				sfxs(sfxId: $sfxId) {
					id
					name
					description
				}
			}`
			// console.log(get_sfx_query)
			if(apolloClient) {
				apolloClient.query({
					query: get_sfx_query,
					variables: {
						sfxId: sfx_id
					}
				}).then((result) => {
					sfx.value = result.data.sfxs[0]
				})
				// const { result } = provideApolloClient(apolloClient)(
				// 	() => useQuery<{sfxs: SFX[]}>(
				// 		get_sfx_query,
				// 		{ sfxId: sfx_id }
				// 	)
				// )
				// watch(result, (newResult) => {
				// 	if(newResult) {
				// 		// console.log('retrieved sfx: ')
				// 		// console.log(newResult)
				// 		sfx.value = newResult.sfxs[0]
				// 	}
				// },
				// { immediate: true })
			}
		}
	}

	function retrieve_traits() {
		const query = gql`query SfxTraits($sfxId: ID) {
			sfxs(sfxId: $sfxId) {
				traits {
					id
					name
				}
			}
		}`
		if(apolloClient) {
			apolloClient.query({
				query: query,
				variables: {
					sfxId: sfx_id
				}
			}).then((result) => {
				if(result.data.sfxs[0] && result.data.sfxs[0].traits) {
					sfx.value = {
						...sfx.value,
						traits: result.data.sfxs[0].traits
					}
				}
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery<{sfxs: SFX[]}>(
			// 		query,
			// 		{ sfxId: sfx_id }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	if(newResult?.sfxs[0] && newResult.sfxs[0].traits) {
			// 		sfx.value = {
			// 			...sfx.value,
			// 			traits: newResult.sfxs[0].traits
			// 		}
			// 	}
			// },
			// { immediate: true })
		}
	}

	function change_sfx(input: SFXInput) {
		if(apolloClient) {
			const query = gql`mutation UpdateSfx($updateSfxId: ID!, $input: SfxInput!) {
				updateSfx(id: $updateSfxId, input: $input) {
					success
					message
				}
			}`
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			let variables: object = {
				updateSfxId: sfx_id,
				input: input
			}
			mutate(variables)
		}
	}

	function delete_sfx() {
		if(apolloClient) {
			const query = gql`mutation DeleteSfx($deleteSfxId: ID!) {
				deleteSfx(id: $deleteSfxId) {
					success
					message
				}
			}`

			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			let variables: object = {
				deleteSfxId: sfx_id
			}
			mutate(variables)
		}
	}

	// onMounted(() => {
	// 	if(init) {
	// 		sfx.value = init
	// 	}
	// 	else if(sfx_id) {
	// 		retrieve_sfx()
	// 	}
	// 	else {
	// 		console.log('no sfx specified')
	// 	}
	// })
	
	return {
		sfx,
		retrieve_sfx,
		retrieve_traits,
		change_sfx,
		delete_sfx
	}
}
