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
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery(
					query,
					null,
					{ fetchPolicy: 'cache-first' }
				)
			)
			watch(result, (newResult) => {
				console.log('retrieved players: ', newResult)
				players.value = newResult.players
			})
		}
	}

	function create_player(player_name: string) {
		const mutation = gql`mutation CreatePlayer($name: String!) {
			createPlayer(name: $name) {
				id
				name
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

	return {
		players,
		retrieve_players,
		create_player
	}
}