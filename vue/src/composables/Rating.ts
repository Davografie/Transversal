import _ from "lodash"

import { useDie } from "@/composables/Die"
import type { Die as DieType } from "@/interfaces/Types"

export const rating_types: string[] = ['empty', 'static', 'resource', 'challenge']

export function useRating() {

	function convert_rating_to_dice(
		rating: number[],
		rating_type: string = 'empty',
		trait_id: string = '',
		trait_setting_id: string = '',
		traitset_id: string = '',
		entity_id: string = '',
		scaling: number = 0
	) {
		let new_rating = <DieType[]>[]
		for(let i = 0; i < rating.length; i++) {
			const { die, tag } = useDie(undefined, undefined, rating[i])
			tag()
			die.value.ratingType = rating_type
			die.value.traitId = trait_id
			die.value.traitsettingId = trait_setting_id
			die.value.traitsetId = traitset_id
			die.value.entityId = entity_id
			die.value.scaling = scaling
			new_rating.push(_.cloneDeep(die.value))
		}
		return new_rating
	}

	return {
		convert_rating_to_dice
	}
}