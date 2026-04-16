import type { Die } from '@/interfaces/Types'

export interface WsDicepool {
	dice: Die[]
}

export interface WebsocketData {
	player_key: string
	session_id: string
	type: string
	dicepool?: WsDicepool
}
