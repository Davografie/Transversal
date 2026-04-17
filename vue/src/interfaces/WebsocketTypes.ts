import type { Die } from '@/interfaces/Types'

export interface WsDicepool {
	player: {
		key: string
	}
	dice: Die[]
}

export interface WebsocketData {
	player_key: string
	session_id: string
	type: string
	dicepool?: WsDicepool
	dicepools?: WsDicepool[]
}
