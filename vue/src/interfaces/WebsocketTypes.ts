import type { Die, Player } from '@/interfaces/Types'
import { phases } from '@/stores/DicepoolStore'

export interface WsDicepool {
	player: Player
	phase: phases
	dice: Die[]
}

export interface WebsocketData {
	player_key: string
	session_id: string
	type: string
	dicepool?: WsDicepool
	dicepools?: WsDicepool[]
}
