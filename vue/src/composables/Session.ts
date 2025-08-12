import { ref, computed, inject, watch } from 'vue'
import { provideApolloClient, useMutation, useQuery } from '@vue/apollo-composable'
import gql from 'graphql-tag'
import type { ApolloClient } from '@apollo/client'
import { usePlayer } from '@/stores/Player'
import { useDicepoolStore } from '@/stores/DicepoolStore'
import { useDicepool } from '@/composables/Dicepool'
import type { Session } from '@/interfaces/Types'

export function useSession() {
	const apolloClient: ApolloClient<any>|undefined = inject('apolloClient')
	const player = usePlayer()
	const dicepool_store = useDicepoolStore()

	function get_session() {
		const query = gql`query getSession {
			session {
				session
				scene
				beat
			}
		}`
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{session: Session}>(query, {}, { fetchPolicy: 'no-cache' })
			)
			watch(result, (newResult) => {
				if(newResult?.session) {
					player.session_id = newResult.session.session
					player.scene_id = newResult.session.scene
					player.beat_id = newResult.session.beat
				}
			}, { once: true })
		}
	}

	function get_dicepool_limit() {
		const query = gql`query getDicepoolLimit {
			session {
				dicepoolLimit
			}
		}`
		if(apolloClient) {
			const { result } = provideApolloClient(apolloClient)(
				() => useQuery<{session: Session}>(query, {}, { fetchPolicy: 'cache-and-network' })
			)
			watch(result, (newResult) => {
				if(newResult?.session) {
					dicepool_store.dicepool_limit = newResult.session.dicepoolLimit
				}
			})
		}
	}

	function set_dicepool_limit(new_limit: number) {
		const query = gql`mutation setDicepoolLimit($sessionInput: SessionInput!) {
			updateSession(sessionInput: $sessionInput) {
				message
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			mutate({
				sessionInput: {
					dicepoolLimit: new_limit
				}
			})
		}
	}

	function new_session() {
		const query = gql`mutation newSession($sessionInput: SessionInput!) {
			updateSession(sessionInput: $sessionInput) {
				message
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			mutate({
				sessionInput: {
					newSession: true
				}
			})
		}
	}

	function next_scene() {
		const query = gql`mutation nextScene($sessionInput: SessionInput!) {
			updateSession(sessionInput: $sessionInput) {
				message
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			mutate({
				sessionInput: {
					nextScene: true
				}
			})
		}
	}

	function next_beat() {
		const query = gql`mutation nextBeat($sessionInput: SessionInput!) {
			updateSession(sessionInput: $sessionInput) {
				message
			}
		}`
		if(apolloClient) {
			const { mutate } = provideApolloClient(apolloClient)(() => useMutation(query))
			mutate({
				sessionInput: {
					nextBeat: true
				}
			})
		}
	}

	return {
		get_session,
		get_dicepool_limit,
		set_dicepool_limit,
		new_session,
		next_scene,
		next_beat
	}
}
