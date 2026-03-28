import { inject, onUnmounted } from 'vue'
import { useWebSocket } from '@vueuse/core'
import { usePlayerStore } from '@/stores/PlayerStore'
import { phases } from '@/stores/DicepoolStore'
import type { Die } from '@/interfaces/Types'

export function useDicepoolWS() {
	const API_WS = inject('API_WS')
	const playerStore = usePlayerStore()
	const player_key = playerStore.player_id.substring(playerStore.player_id.indexOf("/") + 1)
	const { open, close, data, send, status } = useWebSocket(API_WS + "ws/" + (playerStore.player.key ?? player_key))
	
	function connect() {
		console.log("connecting websocket")
		open()
	}

	function hello_world() {
		send(JSON.stringify({ type: "hello_world", data: { player: playerStore.player, perspective: playerStore.perspective } }))
	}

	/**
	 * sends message that you want to join a dicepool
	 * also sends your complications to be used by others
	 */
	function engage() {
		const traits = playerStore.the_entity?.traitsets?.map((ts) => ts.traits).flat()
		console.log("traits: ", traits)
		const complications = traits?.filter((t) => (t?.rating?.filter((r) => r.number_rating < 0).length ?? 0) > 0)

		send(JSON.stringify({ type: "engage", data: { player: playerStore.player, complications: complications } }))
	}

	/**
	 * sends message adding dice to your dicepool
	 */
	function add_dice(dice: Die[]) {}

	function set_result_limit(n: number) {}

	function set_effect_limit(n: number) {}

	function set_phase(_phase: phases) {}

	onUnmounted(() => {
		close()
	})

	return {
		connect,
		status,
		hello_world,
		engage,
		add_dice,
		set_result_limit,
		set_effect_limit,
		set_phase
	}
}