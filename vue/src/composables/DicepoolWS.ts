import { ref, inject, watch } from 'vue'
import { useWebSocket } from '@vueuse/core'
import { usePlayerStore } from '@/stores/PlayerStore'
import { useDicepoolStore } from '@/stores/DicepoolStore'
import { usePlayer } from '@/composables/Player'
import type { Die, Dicepool } from '@/interfaces/Types'
import type { WebsocketData, WsDicepool } from '@/interfaces/WebsocketTypes'

let websocket: ReturnType<typeof useWebSocket>

export function useDicepoolWS() {
	const API_WS = inject('API_WS')

	const playerStore = usePlayerStore()
	const dicepoolStore = useDicepoolStore()
	
	const player_key = playerStore.player_id.substring(playerStore.player_id.indexOf("/") + 1)
	
	websocket = useWebSocket(API_WS + "ws/" + (playerStore.player.key ?? player_key) + '/' + playerStore.uuid)
	
	function connect() {
		if (websocket.status.value == "OPEN") {
			console.error("websocket already open")
		}
		else {
			console.log("connecting websocket")
			websocket.open()
		}
	}

	function hello_world() {
		websocket.send(JSON.stringify({ type: "hello_world", data: { player: playerStore.player.key, perspective: playerStore.perspective } }))
	}

	watch(playerStore.player, (newPlayer) => {
		if(newPlayer.key) {
			websocket.close()
			websocket = useWebSocket(API_WS + "ws/" + newPlayer.key + '/' + playerStore.uuid)
		}
	})

	/**
	 * sends message that you want to join a dicepool
	 * also sends your complications to be used by others
	 */
	function engage() {
		console.log("engaging dicepool")
		const traits = playerStore.the_entity?.traitsets?.map((ts) => ts.traits).flat()
		const complications = traits?.filter((t) => (t?.rating?.filter((r) => r.number_rating < 0).length ?? 0) > 0).map((t) => t?.traitSetting?.id ?? t?.traitSettingId)
		websocket.send(JSON.stringify({ type: "engage", data: complications }))
	}

	function send_dicepool(dice: Die[]) {
		console.log("sending dicepool: ", dice)
		websocket.send(JSON.stringify({
			type: "dicepool",
			dicepool: {
				dice: dice
			}
		}))
	}

	watch(() => dicepoolStore.dice, (newDice) => {
		console.log("new dice: ", newDice)
		send_dicepool(newDice)
	}, { deep: true })

	const receiving = ref(false)
	const { player, retrieve_player, set_player_id } = usePlayer(undefined, undefined)

	async function receive_dicepool(data: WebsocketData) {
		// check current dicepools by player key
		// if it doesn't exist, create it
		// if it does exist, update it
		console.log("receiving dicepool: ", data)
		if(data.dicepool) {
			if(dicepoolStore.dicepools.find((dp: Dicepool) => dp.player.key == data.player_key)) {
				dicepoolStore.dicepools.find((dp: Dicepool) => dp.player.key == data.player_key)!.dice = data.dicepool.dice
			}
			else {
				set_player_id('Players/' + data.player_key)
				await retrieve_player()
				console.log("setting dicepool for player: ", player.value)
				dicepoolStore.dicepools.push({
					player: player.value,
					dice: data.dicepool.dice
				})
			}
		}
	}

	watch(websocket.data, (newData: WebsocketData) => {
		if(newData) {
			receiving.value = true
			const dataObject = typeof newData === "string" ? JSON.parse(newData) : newData;
			console.log("new dicepool (" + dataObject.type + "): ", dataObject)
			switch(dataObject.type) {
				case "dicepool":
					if(dataObject.dicepool) receive_dicepool(dataObject)
					break
			}
			setTimeout(() => {
				receiving.value = false
			}, 200)
		}
	})

	return {
		connect,
		close: websocket.close,
		status: websocket.status,
		receiving,
		hello_world,
		engage,
		send_dicepool
	}
}