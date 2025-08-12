import { ref, type Ref, onMounted, inject, watch } from 'vue'
import type { SFX } from '@/interfaces/Types'
import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
import type { ApolloClient } from '@apollo/client/core'
import gql from 'graphql-tag'

export function useSFXList() {
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
	const sfx_list: Ref<SFX[]> = ref([])

	function retrieve_sfx_list() {
		const query_get_sfx_list = gql`query Sfxs {
			sfxs {
				id
				name
				description
			}
		}`

		if(apolloClient) {
			const { result, refetch } = provideApolloClient(apolloClient)(
				() => useQuery(
					query_get_sfx_list,
					null,
					{ fetchPolicy: 'cache-first' }
				)
			)
			watch(result, (newResult) => {
				if(newResult && newResult.sfxs) {
					sfx_list.value = newResult.sfxs
				}
			},
			{ immediate: true })
			refetch()
		}
	}

	async function create_sfx(name: string, description: string) {
		const mutation_create_sfx = gql`mutation CreateSfx($description: String!, $name: String!) {
				createSfx(description: $description, name: $name) {
					sfx {
						id
					}
				}
			}`

		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutation_create_sfx))
			let variables: object = {
				name: name,
				description: description
			}
			mutate(variables)
		}
	}

	function update_sfx(id: string, name: string, description: string) {
		const mutation_update_sfx = gql`mutation MutateSfx($mutateSfxId: ID!, $name: String, $description: String) {
				mutateSfx(id: $mutateSfxId, name: $name, description: $description) {
					sfx {
						id
					}
				}
			}`

		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutation_update_sfx))
			let variables: object = {
				"mutateSfxId": id,
				"name": name,
				"description": description
			}
			mutate(variables)
		}
	}

	function delete_sfx(id: string) {
		const mutation_delete_sfx = gql`mutation DeleteSfx($id: ID!) {
			deleteSfx(id: $id) {
				success
				message
			}
		}`

		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(mutation_delete_sfx))
			let variables: object = {
				id: id
			}
			mutate(variables)
		}
	}

	onMounted(() => {
		retrieve_sfx_list()
	})

	return { sfx_list, retrieve_sfx_list, create_sfx, update_sfx, delete_sfx }
}