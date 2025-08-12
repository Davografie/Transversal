/*
	SFX logic
	example SFX: SFXs/333969
*/
import { ref, onMounted, watch, inject } from 'vue'
import type { Ref } from 'vue'
import { provideApolloClient, useQuery, useMutation } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import type { ApolloClient } from '@apollo/client'
import type { SFX } from '@/interfaces/Types'

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
				const { result } = provideApolloClient(apolloClient)(
					() => useQuery<{sfxs: SFX[]}>(
						get_sfx_query,
						{ sfxId: sfx_id }
					)
				)
				watch(result, (newResult) => {
					if(newResult) {
						// console.log('retrieved sfx: ')
						// console.log(newResult)
						sfx.value = newResult.sfxs[0]
					}
				},
				{ immediate: true })
			}
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

	onMounted(() => {
		if(init) {
			sfx.value = init
		}
		else if(sfx_id) {
			retrieve_sfx()
		}
		else {
			console.log('no sfx specified')
		}
	})
	
	return { sfx }
}
