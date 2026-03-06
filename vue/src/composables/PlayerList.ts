import { ref, inject, watch } from 'vue'
import type { ApolloClient } from '@apollo/client'
import gql from 'graphql-tag'
import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
import type { Player } from '@/interfaces/Types'

export function usePlayerList() {
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
	const players = ref<Player[]>([])

	function retrieve_players() {
		const query = gql`query Players {
			players {
				id
				name
			}
		}`
		if(apolloClient) {
			apolloClient.query({
				query: query,
				fetchPolicy: 'cache-first'
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

	function create_player(player_name: string) {
		const mutation = gql`mutation CreatePlayer($name: String!) {
			createPlayer(name: $name) {
				player {
					id
				}
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(
				() => useMutation(mutation)
			)
			mutate({
				name: player_name
			})
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