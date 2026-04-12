import { ref, inject, watch } from 'vue'
import type { ApolloClient, FetchPolicy } from '@apollo/client'
import gql from 'graphql-tag'
import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
import type { Player } from '@/interfaces/Types'

export function usePlayerList() {
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
	const players = ref<Player[]>([])

	async function retrieve_players(caching: FetchPolicy = 'cache-first') {
		const query = gql`query Players {
			players {
				id
				name
			}
		}`
		if(apolloClient) {
			await apolloClient.query({
				query: query,
				fetchPolicy: caching
			}).then((result) => {
				players.value = result.data.players
			})
			// const { result } = provideApolloClient(apolloClient)(
			// 	() => useQuery(
			// 		query,
			// 		null,
			// 		{ fetchPolicy: 'cache-and-network' }
			// 	)
			// )
			// watch(result, (newResult) => {
			// 	console.log('retrieved players: ', newResult)
			// 	players.value = newResult.players
			// })
		}
	}

	async function create_player(player_name: string) {
		const mutation = gql`mutation CreatePlayer($name: String!) {
			createPlayer(name: $name) {
				player {
					id
					name
				}
			}
		}`
		if(apolloClient) {
			const result = await apolloClient.mutate({
				mutation: mutation,
				variables: {
					name: player_name
				}
			})
			return result.data.createPlayer.player
		}
	}

	function remove_player(player_id: string) {
		const mutation = gql`mutation DeletePlayer($playerId: ID!) {
			deletePlayer(playerId: $playerId) {
				message
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(
				() => useMutation(mutation)
			)
			mutate({
				playerId: player_id
			})
		}
	}

	return {
		players,
		retrieve_players,
		create_player,
		remove_player
	}
}