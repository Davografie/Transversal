import { ref, watch, inject } from "vue";

import type { ApolloClient } from '@apollo/client/core'
import { useQuery, useMutation, provideApolloClient } from "@vue/apollo-composable"
import gql from 'graphql-tag'

import type { Player, Entity } from "@/interfaces/Types";

const player_placeholder: Player = {
	id: 'placeholder',
	name: 'placeholder',
	isGm: false
}

export function usePlayer(_init?: Player, _player_id?: string) {
	const apolloClient = inject<ApolloClient<Cache>>('apolloClient')
	const player = ref<Player>(_init ?? player_placeholder)

	function set_player_id(player_id: string) {
		_player_id = player_id
	}

	function retrieve_player() {
		// console.log('retrieving player: ' + _player_id)
		const query = gql`query Player($playerId: ID!) {
			players(playerId: $playerId) {
				id
				key
				name
				isGm
				entities {
					id
					name
				}
			}
		}`
		if(apolloClient && _player_id) {
			apolloClient.query({
				query: query,
				variables: { playerId: _player_id },
				fetchPolicy: 'network-only'
			}).then((result) => {
				player.value = result.data.players[0]
			})
		}
	}

	async function activate_entity(entity_id: string) {
		const query_update_entity = gql`mutation ActivateEntity($playerId: ID!, $entityId: ID!) {
			activateEntity(playerId: $playerId, entityId: $entityId) {
				player {
					id
				}
			}
		}`
		if(apolloClient && (_player_id || player.value.id != 'placeholder')) {
			await apolloClient.mutate({
				mutation: query_update_entity,
				variables: {
					playerId: _player_id ?? player.value.id,
					entityId: entity_id
				}
			})
			// const { mutate } = provideApolloClient(apolloClient)(
			// 	() => useMutation(query_update_entity)
			// )
			// mutate({
			// 	playerId: player.value.id,
			// 	entityId: entity.id
			// })
		}
	}

	return {
		player,
		set_player_id,
		retrieve_player,
		activate_entity
	}
}